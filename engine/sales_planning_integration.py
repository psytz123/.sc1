"""
Sales to Planning Integration Module
Connects sales-based forecasts with the main planning engine
"""

import logging
import os
from typing import Dict, List, Optional, Union
import traceback

import pandas as pd

from config.settings import PlanningConfig
from data.sales_data_processor import SalesDataProcessor
from models.forecast import FinishedGoodsForecast
from models.sales_forecast_generator import SalesForecastGenerator
from models.bom import BillOfMaterials, BOMExploder
from models.inventory import Inventory, InventoryNetter
from models.supplier import Supplier

logger = logging.getLogger(__name__)

class SalesPlanningIntegrationError(Exception):
    """Custom exception for sales planning integration errors"""
    pass

class DataValidationError(SalesPlanningIntegrationError):
    """Exception for data validation errors"""
    pass

class ForecastGenerationError(SalesPlanningIntegrationError):
    """Exception for forecast generation errors"""
    pass

class PlanningExecutionError(SalesPlanningIntegrationError):
    """Exception for planning execution errors"""
    pass

class SalesPlanningIntegration:
    """Integrate sales-based forecasts with planning system"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize with optional configuration"""
        try:
            self.config = config or PlanningConfig.get_default_config()
            self.sales_processor = SalesDataProcessor()
            self.planner = None
            self.forecast_generator = None
            self.data_dir = self.config.get('data_directory', 'data')
            
            # Initialize error tracking
            self.errors = []
            self.warnings = []
            
            logger.info("Sales Planning Integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Sales Planning Integration: {str(e)}")
            raise SalesPlanningIntegrationError(f"Initialization failed: {str(e)}")
        
    def generate_sales_forecasts(self, aggregate_by: str = 'week') -> List[FinishedGoodsForecast]:
        """
        Generate forecasts from sales data with enhanced options
        
        Args:
            aggregate_by: 'week' or 'month' for aggregation period
            
        Returns:
            List of FinishedGoodsForecast objects
            
        Raises:
            ForecastGenerationError: If forecast generation fails
            DataValidationError: If data validation fails
        """
        logger.info(f"Generating {aggregate_by}ly forecasts from sales data...")
        
        try:
            # Validate aggregation parameter
            if aggregate_by not in ['week', 'month']:
                raise ValueError(f"Invalid aggregation period: {aggregate_by}. Must be 'week' or 'month'")
            
            # Load and process sales data with error handling
            try:
                sales_df = self.sales_processor.load_and_validate_sales_data()
                if sales_df is None or len(sales_df) == 0:
                    raise DataValidationError("No sales data available for forecast generation")
            except Exception as e:
                logger.error(f"Failed to load sales data: {str(e)}")
                raise DataValidationError(f"Sales data loading failed: {str(e)}")
            
            # Load BOM data for style-to-yarn mapping
            try:
                bom_df = self.sales_processor.load_bom_data()
                if bom_df is None:
                    logger.warning("No BOM data available, proceeding without style-to-yarn mapping")
                    bom_df = pd.DataFrame()  # Empty dataframe
            except Exception as e:
                logger.warning(f"Failed to load BOM data: {str(e)}. Proceeding without BOM data.")
                bom_df = pd.DataFrame()
            
            # Create forecast generator with BOM data
            try:
                self.forecast_generator = SalesForecastGenerator(
                    sales_df,
                    planning_horizon_days=self.config.get('planning_horizon_days', 90),
                    lookback_days=self.config.get('lookback_days', 90),
                    min_history_days=self.config.get('min_sales_history_days', 30),
                    bom_df=bom_df if not bom_df.empty else None
                )
            except Exception as e:
                logger.error(f"Failed to create forecast generator: {str(e)}")
                raise ForecastGenerationError(f"Forecast generator initialization failed: {str(e)}")
            
            # Generate forecasts with error handling
            try:
                forecasts = self.forecast_generator.generate_forecasts(
                    apply_seasonality=self.config.get('seasonality_enabled', True),
                    include_safety_stock=True,
                    aggregate_by=aggregate_by
                )
                
                if not forecasts:
                    logger.warning("No forecasts generated from sales data")
                    return []
                
                logger.info(f"Generated {len(forecasts)} sales-based forecasts")
                return forecasts
                
            except Exception as e:
                logger.error(f"Forecast generation failed: {str(e)}")
                raise ForecastGenerationError(f"Failed to generate forecasts: {str(e)}")
                
        except (DataValidationError, ForecastGenerationError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_sales_forecasts: {str(e)}")
            raise ForecastGenerationError(f"Unexpected error: {str(e)}")
    
    def generate_yarn_forecasts_from_sales(self) -> Dict[str, Dict]:
        """
        Generate yarn-level forecasts directly from sales using BOM explosion
        
        Returns:
            Dictionary of yarn_id -> forecast details
            
        Raises:
            ForecastGenerationError: If yarn forecast generation fails
        """
        try:
            if self.forecast_generator is None:
                logger.info("Forecast generator not initialized, generating sales forecasts first")
                self.generate_sales_forecasts()
            
            if self.forecast_generator is None:
                raise ForecastGenerationError("Failed to initialize forecast generator")
            
            yarn_forecasts = self.forecast_generator.generate_yarn_forecasts()
            
            if not yarn_forecasts:
                logger.warning("No yarn forecasts generated from sales")
                return {}
            
            logger.info(f"Generated forecasts for {len(yarn_forecasts)} yarns from sales")
            return yarn_forecasts
            
        except Exception as e:
            logger.error(f"Failed to generate yarn forecasts: {str(e)}")
            raise ForecastGenerationError(f"Yarn forecast generation failed: {str(e)}")
    
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
            
        Raises:
            DataValidationError: If forecast combination fails
        """
        try:
            # Validate inputs
            if not any([sales_forecasts, manual_forecasts, customer_orders]):
                logger.warning("No forecasts provided to combine")
                return []
            
            # Create a dictionary to aggregate forecasts by SKU
            sku_forecasts = {}
            
            # Process each forecast source
            sources = [
                (sales_forecasts, 'sales_history'),
                (manual_forecasts, 'manual_forecast'),
                (customer_orders, 'customer_orders')
            ]
            
            for forecast_list, source in sources:
                if not forecast_list:
                    continue
                    
                weight = self.config.get('forecast_source_weights', {}).get(source, 1.0)
                
                for forecast in forecast_list:
                    try:
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
                    except Exception as e:
                        logger.error(f"Error processing forecast for SKU {forecast.sku_id}: {str(e)}")
                        self.errors.append(f"Failed to process forecast for SKU {forecast.sku_id}")
            
            # Create combined forecasts
            combined_forecasts = []
            for sku, data in sku_forecasts.items():
                try:
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
                    
                except Exception as e:
                    logger.error(f"Error creating combined forecast for SKU {sku}: {str(e)}")
                    self.errors.append(f"Failed to create combined forecast for SKU {sku}")
            
            logger.info(f"Combined {len(combined_forecasts)} forecasts from {len(sources)} sources")
            return combined_forecasts
            
        except Exception as e:
            logger.error(f"Failed to combine forecasts: {str(e)}")
            raise DataValidationError(f"Forecast combination failed: {str(e)}")
    
    def run_integrated_planning(self,
                               manual_forecasts: Optional[List[FinishedGoodsForecast]] = None,
                               customer_orders: Optional[List[FinishedGoodsForecast]] = None,
                               bom_data: Optional[pd.DataFrame] = None,
                               inventory_data: Optional[pd.DataFrame] = None,
                               supplier_data: Optional[pd.DataFrame] = None,
                               aggregate_by: str = 'week') -> Dict:
        """
        Run complete planning cycle with sales integration
        
        Args:
            manual_forecasts: Optional manual forecasts to include
            customer_orders: Optional customer orders to include
            bom_data: Optional BOM data DataFrame
            inventory_data: Optional inventory data DataFrame
            supplier_data: Optional supplier data DataFrame
            aggregate_by: 'week' or 'month' for sales aggregation
            
        Returns:
            Dictionary with planning results and analytics
        """
        logger.info("Starting integrated planning with sales data...")
        
        # Reset error tracking
        self.errors = []
        self.warnings = []
        
        try:
            # Step 1: Generate sales-based forecasts
            try:
                sales_forecasts = self.generate_sales_forecasts(aggregate_by=aggregate_by)
            except ForecastGenerationError as e:
                logger.error(f"Sales forecast generation failed: {str(e)}")
                return {
                    'error': str(e),
                    'errors': self.errors,
                    'warnings': self.warnings,
                    'status': 'failed',
                    'stage': 'forecast_generation'
                }
            
            # Step 2: Combine with other forecast sources if provided
            try:
                if manual_forecasts or customer_orders:
                    all_forecasts = self.combine_forecasts(
                        sales_forecasts,
                        manual_forecasts or [],
                        customer_orders or []
                    )
                else:
                    all_forecasts = sales_forecasts
            except DataValidationError as e:
                logger.error(f"Forecast combination failed: {str(e)}")
                return {
                    'error': str(e),
                    'errors': self.errors,
                    'warnings': self.warnings,
                    'status': 'failed',
                    'stage': 'forecast_combination'
                }
            
            # Step 3: Generate planning inputs
            try:
                planning_inputs = self.sales_processor.generate_planning_inputs()
            except Exception as e:
                logger.error(f"Failed to generate planning inputs: {str(e)}")
                planning_inputs = {}
                self.warnings.append("Planning inputs generation failed, using defaults")
            
            # Step 4: Create planner instance
            try:
                from engine.planner import RawMaterialPlanner
                self.planner = RawMaterialPlanner(self.config)
            except Exception as e:
                logger.error(f"Failed to create planner instance: {str(e)}")
                return {
                    'error': f"Planner initialization failed: {str(e)}",
                    'errors': self.errors,
                    'warnings': self.warnings,
                    'status': 'failed',
                    'stage': 'planner_initialization'
                }
            
            # Step 5: Load or use provided data
            try:
                # Load BOMs
                if bom_data is not None:
                    boms = self._process_bom_dataframe(bom_data)
                else:
                    boms = self._load_boms()
                
                # Load inventory
                if inventory_data is not None:
                    inventory = self._process_inventory_dataframe(inventory_data)
                else:
                    inventory = self._load_inventory()
                
                # Load suppliers
                if supplier_data is not None:
                    suppliers = self._process_supplier_dataframe(supplier_data)
                else:
                    suppliers = self._load_suppliers()
                    
            except Exception as e:
                logger.error(f"Failed to load planning data: {str(e)}")
                return {
                    'error': f"Data loading failed: {str(e)}",
                    'errors': self.errors,
                    'warnings': self.warnings,
                    'status': 'failed',
                    'stage': 'data_loading'
                }
            
            # Step 6: Run planning
            try:
                recommendations = self.planner.plan(all_forecasts, boms, inventory, suppliers)
                
                # Convert recommendations to DataFrame if needed
                if recommendations and not isinstance(recommendations, pd.DataFrame):
                    recommendations_df = pd.DataFrame([r.__dict__ for r in recommendations])
                else:
                    recommendations_df = recommendations
                    
            except Exception as e:
                logger.error(f"Planning execution failed: {str(e)}")
                logger.error(traceback.format_exc())
                return {
                    'error': f"Planning execution failed: {str(e)}",
                    'errors': self.errors,
                    'warnings': self.warnings,
                    'status': 'failed',
                    'stage': 'planning_execution'
                }
            
            # Step 7: Generate analytics
            try:
                analytics = self._generate_analytics(
                    sales_forecasts, 
                    all_forecasts, 
                    recommendations,
                    planning_inputs
                )
            except Exception as e:
                logger.error(f"Analytics generation failed: {str(e)}")
                analytics = {}
                self.warnings.append("Analytics generation failed")
            
            # Step 8: Create unified forecasts DataFrame
            try:
                unified_forecasts_df = pd.DataFrame([
                    {
                        'sku': f.sku_id,
                        'quantity': f.forecast_qty,
                        'unit': f.unit,
                        'forecast_date': f.forecast_date,
                        'confidence': f.confidence,
                        'source': f.source,
                        'notes': f.notes
                    }
                    for f in all_forecasts
                ])
            except Exception as e:
                logger.error(f"Failed to create unified forecasts DataFrame: {str(e)}")
                unified_forecasts_df = pd.DataFrame()
            
            # Step 9: Create integration metadata
            integration_metadata = {
                'sales_forecasts_count': len(sales_forecasts),
                'manual_forecasts_count': len(manual_forecasts) if manual_forecasts else 0,
                'customer_orders_count': len(customer_orders) if customer_orders else 0,
                'combined_forecasts_count': len(all_forecasts),
                'recommendations_count': len(recommendations_df) if isinstance(recommendations_df, pd.DataFrame) else 0,
                'errors': self.errors,
                'warnings': self.warnings,
                'status': 'success'
            }
            
            logger.info("Integrated planning completed successfully")
            
            return {
                'recommendations': recommendations_df,
                'unified_forecasts': unified_forecasts_df,
                'forecasts': all_forecasts,
                'analytics': analytics,
                'planning_inputs': planning_inputs,
                'integration_metadata': integration_metadata
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in integrated planning: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'error': f"Unexpected error: {str(e)}",
                'errors': self.errors,
                'warnings': self.warnings,
                'status': 'failed',
                'stage': 'unknown'
            }
    
    def validate_integration(self) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate that all integration components are working
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'errors': [],
            'warnings': []
        }
        
        # Test sales data loading
        try:
            sales_df = self.sales_processor.load_and_validate_sales_data()
            validation_results['sales_data_load'] = len(sales_df) > 0
            if len(sales_df) == 0:
                validation_results['warnings'].append("No sales data found")
        except Exception as e:
            validation_results['sales_data_load'] = False
            validation_results['errors'].append(f"Sales data load failed: {str(e)}")
        
        # Test BOM data loading
        try:
            bom_df = self.sales_processor.load_bom_data()
            validation_results['bom_data_load'] = bom_df is not None and len(bom_df) > 0
            if bom_df is None or len(bom_df) == 0:
                validation_results['warnings'].append("No BOM data found")
        except Exception as e:
            validation_results['bom_data_load'] = False
            validation_results['errors'].append(f"BOM data load failed: {str(e)}")
        
        # Test forecast generation
        try:
            forecasts = self.generate_sales_forecasts()
            validation_results['forecast_generation'] = len(forecasts) > 0
            if len(forecasts) == 0:
                validation_results['warnings'].append("No forecasts generated")
        except Exception as e:
            validation_results['forecast_generation'] = False
            validation_results['errors'].append(f"Forecast generation failed: {str(e)}")
        
        # Test style-yarn mapping validation
        try:
            mappings = self.sales_processor.validate_style_yarn_mappings()
            validation_results['style_yarn_mapping'] = len(mappings.get('active_mapped', [])) > 0
            if len(mappings.get('unmapped_styles', [])) > 0:
                validation_results['warnings'].append(
                    f"{len(mappings['unmapped_styles'])} unmapped styles found"
                )
        except Exception as e:
            validation_results['style_yarn_mapping'] = False
            validation_results['errors'].append(f"Style-yarn mapping failed: {str(e)}")
        
        # Overall validation
        validation_results['overall'] = len(validation_results['errors']) == 0
        
        return validation_results
    
    def _process_bom_dataframe(self, bom_df: pd.DataFrame) -> List[BillOfMaterials]:
        """Process BOM DataFrame into BillOfMaterials objects"""
        try:
            # Standardize column names
            column_mapping = {
                'quantity_per_unit': 'qty_per_unit',
                'Quantity Per Unit': 'qty_per_unit',
                'SKU': 'sku_id',
                'Material': 'material_id',
                'Material ID': 'material_id',
                'Yarn ID': 'material_id'
            }
            
            bom_df = bom_df.rename(columns=column_mapping)
            
            # Add unit column if not present
            if 'unit' not in bom_df.columns:
                bom_df['unit'] = 'yards'
            
            # Convert to BOM objects
            boms = BOMExploder.from_dataframe(bom_df)
            logger.info(f"Processed {len(boms)} BOM entries from DataFrame")
            
            # Validate BOM data
            issues = BOMExploder.validate_bom_data(boms)
            if issues:
                logger.warning(f"BOM validation issues found: {len(issues)}")
                for issue in issues[:5]:
                    self.warnings.append(f"BOM issue: {issue}")
            
            return boms
            
        except Exception as e:
            logger.error(f"Error processing BOM DataFrame: {str(e)}")
            raise DataValidationError(f"BOM processing failed: {str(e)}")
    
    def _process_inventory_dataframe(self, inventory_df: pd.DataFrame) -> List[Inventory]:
        """Process inventory DataFrame into Inventory objects"""
        try:
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
            
            inventory_df = inventory_df.rename(columns=column_mapping)
            
            # Add unit column if not present
            if 'unit' not in inventory_df.columns:
                inventory_df['unit'] = 'yards'
            
            # Ensure required columns exist
            if 'open_po_qty' not in inventory_df.columns:
                inventory_df['open_po_qty'] = 0.0
            
            # Convert to Inventory objects
            inventories = InventoryNetter.from_dataframe(inventory_df)
            logger.info(f"Processed inventory for {len(inventories)} materials from DataFrame")
            
            # Log inventory summary
            total_on_hand = sum(inv.on_hand_qty for inv in inventories)
            total_open_po = sum(inv.open_po_qty for inv in inventories)
            logger.info(f"Total on-hand: {total_on_hand:,.2f}, Total open PO: {total_open_po:,.2f}")
            
            return inventories
            
        except Exception as e:
            logger.error(f"Error processing inventory DataFrame: {str(e)}")
            raise DataValidationError(f"Inventory processing failed: {str(e)}")
    
    def _process_supplier_dataframe(self, supplier_df: pd.DataFrame) -> List[Supplier]:
        """Process supplier DataFrame into Supplier objects"""
        try:
            # Convert to Supplier objects
            suppliers = []
            for _, row in supplier_df.iterrows():
                try:
                    supplier = Supplier(
                        supplier_id=row.get('supplier_id', row.get('Supplier ID', '')),
                        name=row.get('name', row.get('Supplier Name', '')),
                        materials=row.get('materials', []),
                        lead_time_days=int(row.get('lead_time_days', row.get('Lead Time Days', 30))),
                        min_order_qty=float(row.get('min_order_qty', row.get('MOQ', 0))),
                        price_per_unit=float(row.get('price_per_unit', row.get('Price', 0))),
                        reliability_score=float(row.get('reliability_score', row.get('Reliability', 0.8))),
                        payment_terms=row.get('payment_terms', row.get('Payment Terms', 'Net 30'))
                    )
                    suppliers.append(supplier)
                except Exception as e:
                    logger.warning(f"Failed to process supplier row: {str(e)}")
                    self.warnings.append(f"Failed to process supplier: {row.get('supplier_id', 'unknown')}")
            
            logger.info(f"Processed {len(suppliers)} suppliers from DataFrame")
            return suppliers
            
        except Exception as e:
            logger.error(f"Error processing supplier DataFrame: {str(e)}")
            raise DataValidationError(f"Supplier processing failed: {str(e)}")
    
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
            
            return self._process_bom_dataframe(df)

        except Exception as e:
            logger.error(f"Error loading BOMs: {str(e)}")
            raise DataValidationError(f"BOM loading failed: {str(e)}")

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
            
            return self._process_inventory_dataframe(df)

        except Exception as e:
            logger.error(f"Error loading inventory: {str(e)}")
            raise DataValidationError(f"Inventory loading failed: {str(e)}")
    
    def _load_suppliers(self) -> List[Supplier]:
        """Load suppliers from data files"""
        try:
            # Try multiple supplier file locations
            supplier_files = [
                os.path.join(self.data_dir, 'suppliers.csv'),
                os.path.join(self.data_dir, 'supplier_data.csv'),
                os.path.join('integrations', 'suppliers', 'supplier_list.csv')
            ]
            
            supplier_file = None
            for file in supplier_files:
                if os.path.exists(file):
                    supplier_file = file
                    break
            
            if not supplier_file:
                logger.warning("No supplier file found, using empty supplier list")
                return []
            
            logger.info(f"Loading suppliers from {supplier_file}")
            df = pd.read_csv(supplier_file)
            
            return self._process_supplier_dataframe(df)
            
        except Exception as e:
            logger.error(f"Error loading suppliers: {str(e)}")
            logger.warning("Continuing with empty supplier list")
            return []
    
    def _generate_analytics(self,
                           sales_forecasts: List[FinishedGoodsForecast],
                           combined_forecasts: List[FinishedGoodsForecast],
                           recommendations: List,
                           planning_inputs: Dict) -> Dict:
        """Generate analytics and insights from the planning run"""
        try:
            analytics = {
                'forecast_summary': {
                    'sales_forecast_count': len(sales_forecasts),
                    'combined_forecast_count': len(combined_forecasts),
                    'total_forecast_quantity': sum(f.forecast_qty for f in combined_forecasts),
                    'avg_confidence': sum(f.confidence for f in combined_forecasts) / len(combined_forecasts) if combined_forecasts else 0
                },
                'recommendation_summary': {
                    'total_recommendations': len(recommendations) if recommendations else 0,
                    'total_value': 0,
                    'suppliers_used': 0
                },
                'inventory_alerts': {
                    'low_stock_count': len(planning_inputs.get('low_stock_alerts', [])),
                    'critical_items': len([item for item in planning_inputs.get('low_stock_alerts', []) 
                                         if item.get('critical_stock', False)])
                },
                'data_quality': planning_inputs.get('validation_report', {})
            }
            
            # Process recommendations if available
            if recommendations:
                if isinstance(recommendations, pd.DataFrame) and not recommendations.empty:
                    analytics['recommendation_summary']['total_value'] = recommendations['total_cost'].sum() if 'total_cost' in recommendations.columns else 0
                    analytics['recommendation_summary']['suppliers_used'] = recommendations['supplier_id'].nunique() if 'supplier_id' in recommendations.columns else 0
                elif isinstance(recommendations, list) and recommendations:
                    analytics['recommendation_summary']['total_value'] = sum(getattr(r, 'total_cost', 0) for r in recommendations)
                    analytics['recommendation_summary']['suppliers_used'] = len(set(getattr(r, 'supplier_id', '') for r in recommendations))
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating analytics: {str(e)}")
            return {
                'error': f"Analytics generation failed: {str(e)}",
                'forecast_summary': {},
                'recommendation_summary': {},
                'inventory_alerts': {},
                'data_quality': {}
            }
    
    def generate_demand_aggregation_report(self, period: str = 'week') -> pd.DataFrame:
        """
        Generate demand aggregation report by specified period
        
        Args:
            period: 'week', 'month', or 'quarter'
            
        Returns:
            DataFrame with aggregated demand by period
            
        Raises:
            DataValidationError: If report generation fails
        """
        try:
            if self.sales_processor.sales_df is None:
                self.sales_processor.load_and_validate_sales_data()
            
            if self.sales_processor.sales_df is None or self.sales_processor.sales_df.empty:
                raise DataValidationError("No sales data available for demand aggregation")
            
            sales_df = self.sales_processor.sales_df.copy()
            
            # Validate period parameter
            if period not in ['week', 'month', 'quarter']:
                raise ValueError(f"Invalid period: {period}. Must be 'week', 'month', or 'quarter'")
            
            # Create period column
            if period == 'week':
                if 'Week' not in sales_df.columns:
                    raise DataValidationError("Week column not found in sales data")
                sales_df['Period'] = sales_df['Week']
            elif period == 'month':
                if 'Month' not in sales_df.columns:
                    raise DataValidationError("Month column not found in sales data")
                sales_df['Period'] = sales_df['Month']
            elif period == 'quarter':
                if 'Quarter' not in sales_df.columns:
                    raise DataValidationError("Quarter column not found in sales data")
                sales_df['Period'] = sales_df['Quarter']
            
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
            
        except Exception as e:
            logger.error(f"Failed to generate demand aggregation report: {str(e)}")
            raise DataValidationError(f"Demand aggregation failed: {str(e)}")
    
    def calculate_safety_stock_requirements(self) -> pd.DataFrame:
        """
        Calculate safety stock requirements based on sales variability
        
        Returns:
            DataFrame with safety stock recommendations by yarn
            
        Raises:
            DataValidationError: If safety stock calculation fails
        """
        try:
            # Get yarn requirements from sales
            yarn_forecasts = self.generate_yarn_forecasts_from_sales()
            
            if not yarn_forecasts:
                logger.warning("No yarn forecasts available for safety stock calculation")
                return pd.DataFrame()
            
            # Load inventory data
            try:
                inventory_df = self.sales_processor.load_inventory_data()
            except Exception as e:
                logger.warning(f"Failed to load inventory data: {str(e)}")
                inventory_df = pd.DataFrame()
            
            safety_stock_df = []
            
            for yarn_id, forecast_data in yarn_forecasts.items():
                try:
                    # Get current inventory
                    current_inv = 0
                    if not inventory_df.empty and 'Yarn_ID' in inventory_df.columns:
                        yarn_inv = inventory_df[inventory_df['Yarn_ID'] == yarn_id]
                        if len(yarn_inv) > 0:
                            current_inv = yarn_inv['Quantity_on_Hand'].iloc[0]
                    
                    # Calculate safety stock
                    planning_horizon_days = self.config.get('planning_horizon_days', 90)
                    weekly_demand = forecast_data['forecast_qty'] / (planning_horizon_days / 7)
                    
                    safety_stock_df.append({
                        'Yarn_ID': yarn_id,
                        'weekly_demand': weekly_demand,
                        'current_inventory': current_inv,
                        'weeks_of_supply': current_inv / weekly_demand if weekly_demand > 0 else 999,
                        'recommended_safety_stock': weekly_demand * 2,  # 2 weeks as base
                        'forecast_quantity': forecast_data['forecast_qty'],
                        'contributing_styles': forecast_data.get('contributing_styles', 0)
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to calculate safety stock for yarn {yarn_id}: {str(e)}")
                    self.warnings.append(f"Safety stock calculation failed for yarn {yarn_id}")
            
            return pd.DataFrame(safety_stock_df)
            
        except Exception as e:
            logger.error(f"Failed to calculate safety stock requirements: {str(e)}")
            raise DataValidationError(f"Safety stock calculation failed: {str(e)}")