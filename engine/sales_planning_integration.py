"""
Sales to Planning Integration Module
Connects sales-based forecasts with the main planning engine
"""

import logging
import os
from typing import Dict, List, Optional

import pandas as pd

from config.settings import PlanningConfig
from data.sales_data_processor import SalesDataProcessor
from models.forecast import FinishedGoodsForecast
from models.sales_forecast_generator import SalesForecastGenerator
from models.bom import BillOfMaterials, BOMExploder
from models.inventory import Inventory, InventoryNetter
from models.supplier import Supplier

logger = logging.getLogger(__name__)

class SalesPlanningIntegration:
    """Integrate sales-based forecasts with planning system"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize with optional configuration"""
        self.config = config or PlanningConfig.get_default_config()
        self.sales_processor = SalesDataProcessor()
        self.planner = None
        self.forecast_generator = None
        
    def generate_sales_forecasts(self, aggregate_by: str = 'week') -> List[FinishedGoodsForecast]:
        """
        Generate forecasts from sales data with enhanced options
        
        Args:
            aggregate_by: 'week' or 'month' for aggregation period
            
        Returns:
            List of FinishedGoodsForecast objects
        """
        logger.info(f"Generating {aggregate_by}ly forecasts from sales data...")
        
        # Load and process sales data
        sales_df = self.sales_processor.load_and_validate_sales_data()
        
        # Load BOM data for style-to-yarn mapping
        bom_df = self.sales_processor.load_bom_data()
        
        # Create forecast generator with BOM data
        self.forecast_generator = SalesForecastGenerator(
            sales_df,
            planning_horizon_days=self.config.get('planning_horizon_days', 90),
            lookback_days=self.config.get('lookback_days', 90),
            min_history_days=self.config.get('min_sales_history_days', 30),
            bom_df=bom_df
        )
        
        # Generate forecasts
        forecasts = self.forecast_generator.generate_forecasts(
            apply_seasonality=self.config.get('seasonality_enabled', True),
            include_safety_stock=True,
            aggregate_by=aggregate_by
        )
        
        logger.info(f"Generated {len(forecasts)} sales-based forecasts")
        return forecasts
    
    def generate_yarn_forecasts_from_sales(self) -> Dict[str, Dict]:
        """
        Generate yarn-level forecasts directly from sales using BOM explosion
        
        Returns:
            Dictionary of yarn_id -> forecast details
        """
        if self.forecast_generator is None:
            self.generate_sales_forecasts()
        
        yarn_forecasts = self.forecast_generator.generate_yarn_forecasts()
        
        logger.info(f"Generated forecasts for {len(yarn_forecasts)} yarns from sales")
        return yarn_forecasts
    
    def combine_forecasts(self, 
                         sales_forecasts: List[FinishedGoodsForecast],
                         manual_forecasts: List[FinishedGoodsForecast],
                         customer_orders: List[FinishedGoodsForecast]) -> List[FinishedGoodsForecast]:
        """
        Combine forecasts from multiple sources using configured weights
        
        Args:
            sales_forecasts: Forecasts generated from sales history
            manual_forecasts: Manually entered forecasts
            customer_orders: Confirmed customer orders
            
        Returns:
            Combined list of forecasts
        """
        # Create a dictionary to aggregate forecasts by SKU
        sku_forecasts = {}
        
        # Process each forecast source
        sources = [
            (sales_forecasts, 'sales_history'),
            (manual_forecasts, 'manual_forecast'),
            (customer_orders, 'customer_orders')
        ]
        
        for forecast_list, source in sources:
            weight = self.config.get('forecast_source_weights', {}).get(source, 1.0)
            
            for forecast in forecast_list:
                if forecast.sku_id not in sku_forecasts:
                    sku_forecasts[forecast.sku_id] = {
                        'total_quantity': 0,
                        'weighted_confidence': 0,
                        'sources': [],
                        'unit': forecast.unit,
                        'forecast_date': forecast.forecast_date,
                        'source_details': {}
                    }
                
                # Add weighted quantity
                weighted_qty = forecast.forecast_qty * weight
                sku_forecasts[forecast.sku_id]['total_quantity'] += weighted_qty
                sku_forecasts[forecast.sku_id]['weighted_confidence'] += forecast.confidence * weight
                sku_forecasts[forecast.sku_id]['sources'].append(source)
                sku_forecasts[forecast.sku_id]['source_details'][source] = {
                    'quantity': forecast.forecast_qty,
                    'weight': weight,
                    'confidence': forecast.confidence
                }
        
        # Create combined forecasts
        combined_forecasts = []
        for sku, data in sku_forecasts.items():
            # Calculate average confidence
            num_sources = len(data['sources'])
            avg_confidence = data['weighted_confidence'] / num_sources if num_sources > 0 else 0.5
            
            # Create source breakdown note
            source_notes = []
            for source, details in data['source_details'].items():
                pct = (details['quantity'] * details['weight'] / data['total_quantity'] * 100)
                source_notes.append(f"{source}: {pct:.0f}%")
            
            combined_forecast = FinishedGoodsForecast(
                sku_id=sku,
                forecast_qty=data['total_quantity'],
                unit=data['unit'],
                forecast_date=data['forecast_date'],
                confidence=min(avg_confidence, 1.0),
                source='combined',
                notes=f"Combined from {', '.join(source_notes)}"
            )
            
            combined_forecasts.append(combined_forecast)
        
        logger.info(f"Combined {len(combined_forecasts)} forecasts from {len(sources)} sources")
        return combined_forecasts
    
    def run_integrated_planning(self,
                               manual_forecasts: Optional[List[FinishedGoodsForecast]] = None,
                               customer_orders: Optional[List[FinishedGoodsForecast]] = None,
                               aggregate_by: str = 'week') -> Dict:
        """
        Run complete planning cycle with sales integration
        
        Args:
            manual_forecasts: Optional manual forecasts to include
            customer_orders: Optional customer orders to include
            aggregate_by: 'week' or 'month' for sales aggregation
            
        Returns:
            Dictionary with planning results and analytics
        """
        logger.info("Starting integrated planning with sales data...")
        
        # Generate sales-based forecasts
        sales_forecasts = self.generate_sales_forecasts(aggregate_by=aggregate_by)
        
        # Combine with other forecast sources if provided
        if manual_forecasts or customer_orders:
            all_forecasts = self.combine_forecasts(
                sales_forecasts,
                manual_forecasts or [],
                customer_orders or []
            )
        else:
            all_forecasts = sales_forecasts
        
        # Generate planning inputs
        planning_inputs = self.sales_processor.generate_planning_inputs()
        
        # Create planner instance
        from engine.planner import RawMaterialPlanner
        
        self.planner = RawMaterialPlanner(self.config)
        
        # Load additional data for planning
        boms = self._load_boms()
        inventory = self._load_inventory()
        suppliers = self._load_suppliers()
        
        # Run planning
        recommendations = self.planner.plan(all_forecasts, boms, inventory, suppliers)
        
        # Generate analytics
        analytics = self._generate_analytics(
            sales_forecasts, 
            all_forecasts, 
            recommendations,
            planning_inputs
        )
        
        return {
            'recommendations': recommendations,
            'forecasts': all_forecasts,
            'analytics': analytics,
            'planning_inputs': planning_inputs
        }
    
    def validate_integration(self) -> Dict[str, bool]:
        """
        Validate that all integration components are working
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {}
        
        try:
            # Test sales data loading
            sales_df = self.sales_processor.load_and_validate_sales_data()
            validation_results['sales_data_load'] = len(sales_df) > 0
        except Exception as e:
            validation_results['sales_data_load'] = False
            logger.error(f"Sales data load failed: {str(e)}")
        
        try:
            # Test BOM data loading
            bom_df = self.sales_processor.load_bom_data()
            validation_results['bom_data_load'] = len(bom_df) > 0
        except Exception as e:
            validation_results['bom_data_load'] = False
            logger.error(f"BOM data load failed: {str(e)}")
        
        try:
            # Test forecast generation
            forecasts = self.generate_sales_forecasts()
            validation_results['forecast_generation'] = len(forecasts) > 0
        except Exception as e:
            validation_results['forecast_generation'] = False
            logger.error(f"Forecast generation failed: {str(e)}")
        
        try:
            # Test style-yarn mapping validation
            mappings = self.sales_processor.validate_style_yarn_mappings()
            validation_results['style_yarn_mapping'] = len(mappings['active_mapped']) > 0
        except Exception as e:
            validation_results['style_yarn_mapping'] = False
            logger.error(f"Style-yarn mapping failed: {str(e)}")
        
        # Overall validation
        validation_results['overall'] = all(validation_results.values())
        
        return validation_results
    
    def _load_boms(self) -> List[BillOfMaterials]:
        """Load BOMs from data files"""
        try:
            # Load integrated BOMs
            bom_file = os.path.join(self.data_dir, 'integrated_boms_v3_corrected.csv')
            if not os.path.exists(bom_file):
                # Fallback to other BOM files
                bom_file = os.path.join(self.data_dir, 'integrated_boms_v2.csv')
                if not os.path.exists(bom_file):
                    bom_file = os.path.join(self.data_dir, 'integrated_boms.csv')

            if not os.path.exists(bom_file):
                logger.warning("No BOM file found, using empty BOM list")
                return []

            logger.info(f"Loading BOMs from {bom_file}")
            df = pd.read_csv(bom_file)

            # Standardize column names
            column_mapping = {
                'quantity_per_unit': 'qty_per_unit',
                'Quantity Per Unit': 'qty_per_unit',
                'SKU': 'sku_id',
                'Material': 'material_id',
                'Material ID': 'material_id',
                'Yarn ID': 'material_id'
            }

            df.rename(columns=column_mapping, inplace=True)

            # Add unit column if not present (default to yards for yarn)
            if 'unit' not in df.columns:
                df['unit'] = 'yards'

            # Convert to BOM objects
            boms = BOMExploder.from_dataframe(df)
            logger.info(f"Loaded {len(boms)} BOM entries")

            # Validate BOM data
            issues = BOMExploder.validate_bom_data(boms)
            if issues:
                logger.warning(f"BOM validation issues found: {len(issues)}")
                for issue in issues[:5]:  # Show first 5 issues
                    logger.warning(f"  - {issue}")

            return boms

        except Exception as e:
            logger.error(f"Error loading BOMs: {str(e)}")
            raise

    def _load_inventory(self) -> List[Inventory]:
        """Load inventory from data files"""
        try:
            # Load integrated inventory
            inventory_file = os.path.join(self.data_dir, 'integrated_inventory_v2.csv')
            if not os.path.exists(inventory_file):
                inventory_file = os.path.join(self.data_dir, 'integrated_inventory.csv')

            if not os.path.exists(inventory_file):
                logger.warning("No inventory file found, using empty inventory list")
                return []

            logger.info(f"Loading inventory from {inventory_file}")
            df = pd.read_csv(inventory_file)

            # Standardize column names
            column_mapping = {
                'current_stock': 'on_hand_qty',
                'Current Stock': 'on_hand_qty',
                'On Hand': 'on_hand_qty',
                'incoming_stock': 'open_po_qty',
                'Incoming Stock': 'open_po_qty',
                'Open PO': 'open_po_qty',
                'Material': 'material_id',
                'Material ID': 'material_id',
                'Yarn ID': 'material_id'
            }

            df.rename(columns=column_mapping, inplace=True)

            # Add unit column if not present (default to yards for yarn)
            if 'unit' not in df.columns:
                df['unit'] = 'yards'

            # Ensure required columns exist
            if 'open_po_qty' not in df.columns:
                df['open_po_qty'] = 0.0

            # Convert to Inventory objects
            inventories = InventoryNetter.from_dataframe(df)
            logger.info(f"Loaded inventory for {len(inventories)} materials")

            # Log inventory summary
            total_on_hand = sum(inv.on_hand_qty for inv in inventories)
            total_open_po = sum(inv.open_po_qty for inv in inventories)
            logger.info(f"Total on-hand: {total_on_hand:,.2f}, Total open PO: {total_open_po:,.2f}")

            return inventories

        except Exception as e:
            logger.error(f"Error loading inventory: {str(e)}")
            raise
        return []
    
    def _load_suppliers(self) -> List[Supplier]:
        """Load suppliers from data files"""
        # Implementation depends on your supplier data structure
        # This is a placeholder
        return []
    
    def _generate_analytics(self,
                           sales_forecasts: List[FinishedGoodsForecast],
                           combined_forecasts: List[FinishedGoodsForecast],
                           recommendations: List,
                           planning_inputs: Dict) -> Dict:
        """Generate analytics and insights from the planning run"""
        analytics = {
            'forecast_summary': {
                'sales_forecast_count': len(sales_forecasts),
                'combined_forecast_count': len(combined_forecasts),
                'total_forecast_quantity': sum(f.forecast_qty for f in combined_forecasts),
                'avg_confidence': sum(f.confidence for f in combined_forecasts) / len(combined_forecasts) if combined_forecasts else 0
            },
            'recommendation_summary': {
                'total_recommendations': len(recommendations),
                'total_value': sum(r.total_cost for r in recommendations) if recommendations else 0,
                'suppliers_used': len(set(r.supplier_id for r in recommendations)) if recommendations else 0
            },
            'inventory_alerts': {
                'low_stock_count': len(planning_inputs.get('low_stock_alerts', [])),
                'critical_items': len([item for item in planning_inputs.get('low_stock_alerts', []) 
                                     if item.get('critical_stock', False)])
            },
            'data_quality': planning_inputs.get('validation_report', {})
        }
        
        return analytics
    
    def generate_demand_aggregation_report(self, period: str = 'week') -> pd.DataFrame:
        """
        Generate demand aggregation report by specified period
        
        Args:
            period: 'week', 'month', or 'quarter'
            
        Returns:
            DataFrame with aggregated demand by period
        """
        if self.sales_processor.sales_df is None:
            self.sales_processor.load_and_validate_sales_data()
        
        sales_df = self.sales_processor.sales_df.copy()
        
        # Create period column
        if period == 'week':
            sales_df['Period'] = sales_df['Week']
        elif period == 'month':
            sales_df['Period'] = sales_df['Month']
        elif period == 'quarter':
            sales_df['Period'] = sales_df['Quarter']
        else:
            raise ValueError(f"Invalid period: {period}")
        
        # Aggregate by period
        period_demand = sales_df.groupby('Period').agg({
            'Yds_ordered': ['sum', 'mean', 'std', 'count'],
            'Style': 'nunique'
        }).round(2)
        
        period_demand.columns = ['total_yards', 'avg_order', 'std_dev', 'order_count', 'unique_styles']
        period_demand = period_demand.reset_index()
        
        # Add growth metrics
        period_demand['growth_rate'] = period_demand['total_yards'].pct_change()
        period_demand['moving_avg_3'] = period_demand['total_yards'].rolling(3).mean()
        
        return period_demand
    
    def calculate_safety_stock_requirements(self) -> pd.DataFrame:
        """
        Calculate safety stock requirements based on sales variability
        
        Returns:
            DataFrame with safety stock recommendations by yarn
        """
        # Get yarn requirements from sales
        yarn_forecasts = self.generate_yarn_forecasts_from_sales()
        
        # Load inventory data
        inventory_df = self.sales_processor.load_inventory_data()
        
        safety_stock_df = []
        
        for yarn_id, forecast_data in yarn_forecasts.items():
            # Get current inventory
            current_inv = 0
            if 'Yarn_ID' in inventory_df.columns:
                yarn_inv = inventory_df[inventory_df['Yarn_ID'] == yarn_id]
                if len(yarn_inv) > 0:
                    current_inv = yarn_inv['Quantity_on_Hand'].iloc[0]
            
            # Calculate safety stock (already included in forecast)
            # Extract it by comparing with base demand
            weekly_demand = forecast_data['forecast_qty'] / (self.config.get('planning_horizon_days', 90) / 7)
            
            safety_stock_df.append({
                'Yarn_ID': yarn_id,
                'weekly_demand': weekly_demand,
                'current_inventory': current_inv,
                'weeks_of_supply': current_inv / weekly_demand if weekly_demand > 0 else 999,
                'recommended_safety_stock': weekly_demand * 2,  # 2 weeks as base
                'forecast_quantity': forecast_data['forecast_qty'],
                'contributing_styles': forecast_data['contributing_styles']
            })
        
        return pd.DataFrame(safety_stock_df)