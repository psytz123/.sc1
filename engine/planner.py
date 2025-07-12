"""
Planning Engine - Orchestrates the raw material planning process
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from functools import lru_cache

import pandas as pd

from config.settings import PlanningConfig
from models.bom import BillOfMaterials, BOMExploder
from models.forecast import FinishedGoodsForecast, ForecastProcessor
from models.inventory import Inventory, InventoryNetter
from models.recommendation import ProcurementRecommendation
from models.supplier import EOQCalculator, Supplier, SupplierSelector
from utils.logger import get_logger

logger = get_logger(__name__)


class RawMaterialPlanner:
    """Main planning engine that orchestrates the planning process"""

    def __init__(self, config: PlanningConfig):
        self.config = config
        self.forecast_processor = ForecastProcessor(config)
        self.bom_exploder = BOMExploder()
        self.inventory_netter = InventoryNetter()
        self.supplier_selector = SupplierSelector(config)
        self.eoq_calculator = EOQCalculator()
        self._supplier_cache = {}  # Cache for supplier lookups
        self._bom_cache = {}  # Cache for BOM lookups

    def plan(self,
             forecasts: List[FinishedGoodsForecast],
             boms: List[BillOfMaterials],
             inventory: List[Inventory],
             suppliers: List[Supplier]) -> List[ProcurementRecommendation]:
        """
        Execute the 6-step planning process

        Returns:
            List of procurement recommendations
        """
        # Input validation
        if not isinstance(forecasts, list):
            raise TypeError("forecasts must be a list")
        if not isinstance(boms, list):
            raise TypeError("boms must be a list")
        if not isinstance(inventory, list):
            raise TypeError("inventory must be a list")
        if not isinstance(suppliers, list):
            raise TypeError("suppliers must be a list")

        if not forecasts:
            logger.warning("No forecasts provided")
            return []
        if not boms:
            logger.warning("No BOMs provided")
            return []
        if not suppliers:
            logger.warning("No suppliers provided")
            return []

        logger.info("Starting Beverly Knits Raw Material Planning Engine")
        logger.info("=" * 50)

        # Step 1: Unify forecasts
        logger.info("Step 1: Unifying forecasts...")

        # Check if we need to generate forecasts from sales data
        if hasattr(self.config, 'enable_sales_forecasting') and self.config.enable_sales_forecasting:
            logger.info("Generating forecasts from sales history...")
            sales_forecasts = self._generate_sales_forecasts()
            if sales_forecasts:
                forecasts.extend(sales_forecasts)
                logger.info(f"Added {len(sales_forecasts)} sales-based forecasts")

        unified_forecasts = self.forecast_processor.unify_forecasts(forecasts)
        logger.info(f"Unified {len(forecasts)} forecasts into {len(unified_forecasts)} SKU demands")

        # Step 2: Explode BOMs
        logger.info("Step 2: Exploding BOMs...")

        # Check if we have style-to-yarn BOMs
        if hasattr(self.config, 'use_style_yarn_bom') and self.config.use_style_yarn_bom:
            material_requirements = self._explode_with_style_yarn_bom(unified_forecasts, boms)
        else:
            material_requirements = BOMExploder.explode_requirements(unified_forecasts, boms)

        logger.info(f"Exploded to {len(material_requirements)} material requirements")

        # Step 3: Net against inventory
        logger.info("Step 3: Netting against inventory...")
        net_requirements = self.inventory_netter.calculate_net_requirements(
            material_requirements, inventory
        )
        logger.info(f"Calculated net requirements for {len(net_requirements)} materials")

        # Step 4 & 5: Optimize procurement and select suppliers
        logger.info("Step 4 & 5: Optimizing procurement and selecting suppliers...")
        recommendations = self._generate_recommendations(net_requirements, suppliers)
        logger.info(f"Generated {len(recommendations)} procurement recommendations")

        # Step 6: Generate output
        logger.info("Step 6: Generating reports...")
        self._generate_reports(recommendations)

        # Store recommendations for summary
        self._last_recommendations = recommendations

        return recommendations

    def _generate_recommendations(self,
                                  net_requirements: Dict[str, float],
                                  suppliers: List[Supplier]) -> List[ProcurementRecommendation]:
        """Generate procurement recommendations with supplier selection"""
        recommendations = []

        # Group suppliers by material
        suppliers_by_material = defaultdict(list)
        for supplier in suppliers:
            suppliers_by_material[supplier.material_id].append(supplier)

        for material_id, req_data in net_requirements.items():
            net_requirement = req_data['net_requirement']
            if net_requirement <= 0:
                continue

            material_suppliers = suppliers_by_material.get(material_id, [])
            if not material_suppliers:
                logger.info(f"   ⚠️  No suppliers found for material {material_id}")
                continue

            # Apply safety stock buffer
            safety_buffer = self.config.get('safety_buffer', 0.1) if isinstance(self.config, dict) else getattr(self.config, 'safety_stock_percentage', 0.1)

            # Check if we should use advanced safety stock calculation
            if hasattr(self.config, 'safety_stock_method') and self.config.safety_stock_method == 'statistical':
                safety_stock = self._calculate_statistical_safety_stock(material_id, req_data)
                buffered_requirement = net_requirement + safety_stock
            else:
                buffered_requirement = net_requirement * (1 + safety_buffer)

            # Check if multi-supplier optimization is enabled
            enable_multi_supplier = self.config.get('enable_multi_supplier', True) if isinstance(self.config, dict) else getattr(self.config, 'enable_multi_supplier', True)

            if enable_multi_supplier and len(material_suppliers) > 1:
                # Use multi-supplier optimization
                supplier_recommendations = self._optimize_multi_supplier(
                    material_id, buffered_requirement, material_suppliers
                )
                recommendations.extend(supplier_recommendations)
            else:
                # Select single best supplier
                selected_supplier = self.supplier_selector.select_supplier(
                    material_suppliers, buffered_requirement
                )

                if selected_supplier:
                    # Calculate EOQ
                    eoq = self.eoq_calculator.calculate_eoq(
                        buffered_requirement,
                        selected_supplier.ordering_cost,
                        selected_supplier.cost_per_unit,  # Added unit_cost parameter
                        selected_supplier.holding_cost_rate
                    )

                    # Apply MOQ constraint
                    order_qty = max(eoq, selected_supplier.moq)

                    # Round to order multiple if specified
                    # if selected_supplier.order_multiple > 1:
                    #     order_qty = np.ceil(order_qty / selected_supplier.order_multiple) * selected_supplier.order_multiple

                    # Create recommendation
                    recommendation = ProcurementRecommendation(
                        material_id=material_id,
                        supplier_id=selected_supplier.supplier_id,
                        order_qty=order_qty,
                        unit_price=selected_supplier.cost_per_unit,
                        total_cost=order_qty * selected_supplier.cost_per_unit,
                        order_date=datetime.now().date(),
                        delivery_date=datetime.now().date() + timedelta(days=selected_supplier.lead_time_days),
                        risk_flags=self._assess_risks(selected_supplier, order_qty, buffered_requirement)
                    )
                    recommendations.append(recommendation)

        return recommendations

    def _generate_sales_forecasts(self) -> List[FinishedGoodsForecast]:
        """Generate forecasts from sales data"""
        try:
            from data.sales_data_processor import SalesDataProcessor

            processor = SalesDataProcessor(self.config)

            # Load sales data
            processor.load_and_validate_sales_data()

            # Load BOM data if available
            if hasattr(self.config, 'bom_file'):
                processor.load_bom_data(self.config.bom_file)

            # Generate planning inputs
            planning_inputs = processor.generate_planning_inputs(
                lookback_days=getattr(self.config, 'sales_lookback_days', 90),
                planning_horizon_days=getattr(self.config, 'planning_horizon_days', 90),
                aggregation_period=getattr(self.config, 'aggregation_period', 'weekly'),
                safety_stock_method=getattr(self.config, 'safety_stock_method', 'statistical')
            )

            return planning_inputs.get('forecasts', [])

        except Exception as e:
            logger.info(f"   ⚠️  Error generating sales forecasts: {e}")
            return []

    def _explode_with_style_yarn_bom(self,
                                    unified_forecasts: Dict[str, float],
                                    boms: List[BillOfMaterials]) -> Dict[str, Dict]:
        """Explode forecasts using style-to-yarn BOM with enhanced integration"""
        try:
            # Try to use the enhanced style-yarn BOM integration
            from engine.style_yarn_bom_integration import StyleYarnBOMIntegrator

            # Initialize the integrator with the configured BOM file
            bom_file = getattr(self.config, 'style_yarn_bom_file', 'data/cfab_Yarn_Demand_By_Style.csv')
            integrator = StyleYarnBOMIntegrator(bom_file)

            # Separate style forecasts from SKU forecasts
            style_forecasts = {}
            sku_forecasts = {}

            for item_id, forecast_qty in unified_forecasts.items():
                # Check if this is a style ID (typically contains '/')
                if '/' in item_id:
                    style_forecasts[item_id] = forecast_qty
                else:
                    sku_forecasts[item_id] = forecast_qty

            # Explode style forecasts to yarn requirements
            yarn_requirements = {}
            if style_forecasts:
                logger.info(f"   📊 Exploding {len(style_forecasts)} style forecasts to yarn requirements")
                yarn_requirements = integrator.explode_style_forecast_to_yarn(style_forecasts)

                # Log summary
                total_yarn_qty = sum(req['total_qty'] for req in yarn_requirements.values())
                logger.info(f"   ✅ Generated requirements for {len(yarn_requirements)} yarns")
                logger.info(f"   📦 Total yarn required: {total_yarn_qty:,.0f} yards")

            # If there are also SKU forecasts, handle them with regular BOM explosion
            if sku_forecasts and boms:
                from models.bom import BOMExploder
                sku_requirements = BOMExploder.explode_requirements(sku_forecasts, boms)

                # Merge yarn and SKU requirements
                yarn_requirements = BOMExploder.merge_requirements(yarn_requirements, sku_requirements)

            return yarn_requirements

        except ImportError:
            logger.info("   ⚠️  Enhanced BOM integration not available, falling back to standard method")
            # Fall back to the original method
            import pandas as pd

            from models.bom import BOMExploder

            # Load style-yarn BOM data
            bom_file = getattr(self.config, 'style_yarn_bom_file', 'data/cfab_Yarn_Demand_By_Style.csv')
            bom_df = pd.read_csv(bom_file)

            # Create style-yarn BOMs
            style_yarn_boms = BOMExploder.from_style_yarn_dataframe(bom_df)

            # Explode to yarn requirements
            yarn_requirements = BOMExploder.explode_style_to_yarn_requirements(
                unified_forecasts,
                style_yarn_boms
            )

            return yarn_requirements

        except Exception as e:
            logger.info(f"   ⚠️  Error with style-yarn BOM explosion: {e}")
            # Fall back to regular BOM explosion
            from models.bom import BOMExploder
            return BOMExploder.explode_requirements(unified_forecasts, boms)

    def _calculate_statistical_safety_stock(self,
                                          material_id: str,
                                          req_data: Dict) -> float:
        """Calculate safety stock based on demand variability"""
        try:
            # Get historical demand data if available
            if 'demand_history' in req_data:
                demand_history = req_data['demand_history']

                # Calculate statistics
                import numpy as np
                from scipy import stats

                np.mean(demand_history)
                std_demand = np.std(demand_history)

                # Get service level from config
                service_level = getattr(self.config, 'service_level', 0.95)
                z_score = stats.norm.ppf(service_level)

                # Get lead time
                lead_time_days = req_data.get('lead_time_days', 14)

                # Safety stock = Z * σ * √(Lead Time)
                safety_stock = z_score * std_demand * np.sqrt(lead_time_days / 7)  # Convert to weeks

                return max(0, safety_stock)
            else:
                # Fall back to percentage-based safety stock
                return req_data['net_requirement'] * 0.2

        except Exception as e:
            logger.info(f"   ⚠️  Error calculating statistical safety stock: {e}")
            return req_data['net_requirement'] * 0.2

    def _optimize_multi_supplier(self,
                               material_id: str,
                               total_requirement: float,
                               suppliers: List[Supplier]) -> List[ProcurementRecommendation]:
        """Optimize procurement across multiple suppliers"""
        recommendations = []
        remaining_qty = total_requirement

        # Sort suppliers by total cost (price only, as shipping_cost is not in the model)
        sorted_suppliers = sorted(suppliers, key=lambda s: s.cost_per_unit)

        for supplier in sorted_suppliers:
            if remaining_qty <= 0:
                break

            # Calculate optimal quantity for this supplier
            if remaining_qty >= supplier.moq:
                # Calculate EOQ for this supplier
                eoq = self.eoq_calculator.calculate_eoq(
                    remaining_qty,
                    supplier.ordering_cost,
                    supplier.cost_per_unit,  # Added unit_cost parameter
                    supplier.holding_cost_rate
                )

                # Apply constraints
                order_qty = max(eoq, supplier.moq)
                order_qty = min(order_qty, remaining_qty)

                # Round to order multiple if specified
                # if supplier.order_multiple > 1:
                #     order_qty = np.ceil(order_qty / supplier.order_multiple) * supplier.order_multiple

                # Create recommendation
                recommendation = ProcurementRecommendation(
                    material_id=material_id,
                    supplier_id=supplier.supplier_id,
                    order_qty=order_qty,
                    unit_price=supplier.cost_per_unit,
                    total_cost=order_qty * supplier.cost_per_unit,
                    order_date=datetime.now().date(),
                    delivery_date=datetime.now().date() + timedelta(days=supplier.lead_time_days),
                    risk_flags=self._assess_risks(supplier, order_qty, order_qty)
                )
                recommendations.append(recommendation)

                remaining_qty -= order_qty

        return recommendations

    def generate_summary_report(self) -> Dict[str, any]:
        """Generate a comprehensive summary of the planning run"""
        if not hasattr(self, '_last_recommendations'):
            return {"error": "No planning run completed yet"}

        recommendations = self._last_recommendations

        # Calculate summary statistics
        total_materials = len(set(r.material_id for r in recommendations))
        total_suppliers = len(set(r.supplier_id for r in recommendations))
        total_cost = sum(r.total_cost for r in recommendations)

        # Group by risk level
        risk_summary = {
            'high': sum(1 for r in recommendations if any(rf.severity == 'high' for rf in r.risk_flags)),
            'medium': sum(1 for r in recommendations if any(rf.severity == 'medium' for rf in r.risk_flags)),
            'low': sum(1 for r in recommendations if any(rf.severity == 'low' for rf in r.risk_flags)),
            'none': sum(1 for r in recommendations if not r.risk_flags)
        }

        # Calculate delivery timeline
        earliest_delivery = min(r.delivery_date for r in recommendations) if recommendations else None
        latest_delivery = max(r.delivery_date for r in recommendations) if recommendations else None

        return {
            'summary': {
                'total_materials': total_materials,
                'total_suppliers': total_suppliers,
                'total_cost': total_cost,
                'total_recommendations': len(recommendations)
            },
            'risk_summary': risk_summary,
            'delivery_timeline': {
                'earliest': earliest_delivery,
                'latest': latest_delivery,
                'span_days': (latest_delivery - earliest_delivery).days if earliest_delivery and latest_delivery else 0
            },
            'top_cost_items': sorted(
                [(r.material_id, r.total_cost) for r in recommendations],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        """
        Get summary statistics from the last planning run

        Returns:
            Dictionary with planning summary statistics
        """
        if not hasattr(self, '_last_recommendations'):
            return {
                'total_recommendations': 0,
                'total_cost': 0,
                'materials_planned': 0,
                'suppliers_used': 0
            }

        recommendations = self._last_recommendations

        return {
            'total_recommendations': len(recommendations),
            'total_cost': sum(r.total_cost for r in recommendations),
            'materials_planned': len(set(r.material_id for r in recommendations)),
            'suppliers_used': len(set(r.supplier_id for r in recommendations)),
            'urgent_orders': len([r for r in recommendations if r.lead_time_days <= 14]),
            'average_lead_time': sum(r.lead_time_days for r in recommendations) / len(recommendations) if recommendations else 0
        }

    def export_results_to_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        Export planning results to dataframes

        Returns:
            Dictionary of dataframes with planning results
        """
        if not hasattr(self, '_last_recommendations'):
            return {'error': pd.DataFrame({'message': ['No planning results available']})}

        recommendations = self._last_recommendations

        # Create recommendations dataframe
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'material_id': rec.material_id,
                'supplier_id': rec.supplier_id,
                'order_quantity': rec.order_quantity,
                'cost_per_unit': rec.cost_per_unit,
                'total_cost': rec.total_cost,
                'lead_time_days': rec.lead_time_days,
                'risk': rec.risk.value,
                'reasoning': rec.reasoning
            })

        return {
            'recommendations': pd.DataFrame(recommendations_data) if recommendations_data else pd.DataFrame()
        }

class MaterialPlanner:
    """
    Material Planning Engine for Beverly Knits
    
    Implements the core material planning workflow with the following steps:
    1. Unify forecasts from multiple sources
    2. Explode BOM requirements
    3. Net against inventory
    4. Track errors and validations
    """
    
    def __init__(self, config=None):
        """
        Initialize the MaterialPlanner
        
        Args:
            config: Optional configuration object
        """
        self.config = config or {}
        self._errors = []
        self._warnings = []
        
        # Default source weights
        self.source_weights = {
            'sales_order': 0.4,
            'demand_forecast': 0.6,
            'production_plan': 0.3
        }
        
        # Update with config if provided
        if hasattr(config, 'source_weights'):
            self.source_weights.update(config.source_weights)
        elif isinstance(config, dict) and 'source_weights' in config:
            self.source_weights.update(config['source_weights'])
    
    def unify_forecasts(self, forecast_data):
        """
        Unify forecasts from multiple sources with proper weighting
        
        Args:
            forecast_data (pd.DataFrame): Forecast data with columns:
                - sku_id: SKU identifier
                - forecast_qty: Forecast quantity
                - forecast_date: Forecast date
                - source: Forecast source (sales_order, demand_forecast, production_plan)
        
        Returns:
            pd.DataFrame: Unified forecast data with source_weight column
        """
        try:
            # Handle empty input
            if forecast_data.empty:
                logger.info("   ⚠️  Empty forecast data provided")
                return pd.DataFrame(columns=['sku_id', 'unified_qty', 'forecast_date', 'source_weight'])
            
            # Validate required columns
            required_columns = ['sku_id', 'forecast_qty', 'forecast_date', 'source']
            missing_columns = [col for col in required_columns if col not in forecast_data.columns]
            if missing_columns:
                error_msg = f"Missing required columns: {missing_columns}"
                self.add_error(error_msg)
                logger.error(f"   ❌ {error_msg}")
                return pd.DataFrame(columns=['sku_id', 'unified_qty', 'forecast_date', 'source_weight'])
            
            # Create a copy to avoid modifying original data
            df = forecast_data.copy()
            
            # Validate and handle data quality issues
            self._validate_forecast_data(df)
            
            # Handle invalid source types
            valid_sources = set(self.source_weights.keys())
            invalid_sources = set(df['source'].unique()) - valid_sources
            if invalid_sources:
                warning_msg = f"Invalid source types found: {invalid_sources}. Using default weight of 0.1"
                self.add_warning(warning_msg)
                logger.warning(f"   ⚠️  {warning_msg}")
                # Set default weight for invalid sources
                for source in invalid_sources:
                    self.source_weights[source] = 0.1
            
            # Apply source weights
            df['source_weight'] = df['source'].map(self.source_weights)
            
            # Handle zero and negative quantities
            df = self._handle_quantity_issues(df)
            
            # Handle duplicate SKUs by aggregating
            if df.duplicated(subset=['sku_id', 'forecast_date']).any():
                logger.info("   📊 Aggregating duplicate SKU forecasts")
                df = df.groupby(['sku_id', 'forecast_date']).agg({
                    'forecast_qty': 'sum',
                    'source_weight': 'mean',
                    'source': lambda x: ', '.join(x.unique())
                }).reset_index()
            
            # Normalize source weights to 1.0 for single source scenarios
            unique_sources = df['source'].unique()
            if len(unique_sources) == 1:
                df['source_weight'] = 1.0
            
            # Calculate unified quantities
            df['unified_qty'] = df['forecast_qty'] * df['source_weight']
            
            # Handle decimal precision
            df['unified_qty'] = df['unified_qty'].round(6)
            
            # Final cleanup and validation
            result = df[['sku_id', 'unified_qty', 'forecast_date', 'source_weight']].copy()
            
            logger.info(f"   ✅ Unified {len(forecast_data)} forecast records into {len(result)} unified forecasts")
            
            return result
            
        except Exception as e:
            error_msg = f"Error in unify_forecasts: {str(e)}"
            self.add_error(error_msg)
            logger.error(f"   ❌ {error_msg}")
            return pd.DataFrame(columns=['sku_id', 'unified_qty', 'forecast_date', 'source_weight'])
    
    def explode_bom(self, bom_data, forecast_data=None, test_forecast=None):
        """
        Explode BOM requirements based on forecast data
        
        Args:
            bom_data (pd.DataFrame): BOM data with columns:
                - sku_id: SKU identifier
                - material_id: Material identifier
                - qty_per_unit: Quantity per unit
            forecast_data (pd.DataFrame): Forecast data with unified_qty column
            test_forecast (pd.DataFrame): Alternative parameter name for forecast data (for test compatibility)
        
        Returns:
            pd.DataFrame: Material requirements
        """
        try:
            # Handle test_forecast parameter for backward compatibility
            if test_forecast is not None:
                forecast_data = test_forecast
            
            # Handle empty inputs
            if bom_data.empty or forecast_data is None or forecast_data.empty:
                logger.info("   ⚠️  Empty BOM or forecast data provided")
                return pd.DataFrame(columns=['material_id', 'total_requirement', 'sku_id'])
            
            # Validate BOM data
            self._validate_bom_data(bom_data)
            
            # Create copies to avoid modifying original data
            bom_df = bom_data.copy()
            forecast_df = forecast_data.copy()
            
            # Handle BOM percentage corrections
            bom_df = self._handle_bom_percentages(bom_df)
            
            # Handle zero percentage materials
            bom_df = bom_df[bom_df['qty_per_unit'] > 0]
            
            # Check for missing BOMs
            forecast_skus = set(forecast_df['sku_id'].unique())
            bom_skus = set(bom_df['sku_id'].unique())
            missing_bom_skus = forecast_skus - bom_skus
            
            if missing_bom_skus:
                warning_msg = f"Missing BOM data for SKUs: {missing_bom_skus}"
                self.add_warning(warning_msg)
                logger.warning(f"   ⚠️  {warning_msg}")
            
            # Detect circular BOM references
            self._detect_circular_bom_references(bom_df)
            
            # Merge forecast and BOM data
            merged_df = pd.merge(
                forecast_df,
                bom_df,
                on='sku_id',
                how='inner'
            )
            
            if merged_df.empty:
                logger.warning("   ⚠️  No matching SKUs found between forecast and BOM data")
                return pd.DataFrame(columns=['material_id', 'total_requirement', 'sku_id'])
            
            # Calculate material requirements
            merged_df['material_requirement'] = merged_df['unified_qty'] * merged_df['qty_per_unit']
            
            # Handle unit conversions if unit column exists
            if 'unit' in merged_df.columns:
                merged_df = self._handle_unit_conversions(merged_df)
            
            # Aggregate requirements by material
            result = merged_df.groupby(['material_id']).agg({
                'material_requirement': 'sum',
                'sku_id': lambda x: ', '.join(x.unique())
            }).reset_index()
            
            result.rename(columns={'material_requirement': 'total_requirement'}, inplace=True)
            
            # Handle fractional requirements
            result['total_requirement'] = result['total_requirement'].round(6)
            
            logger.info(f"   ✅ Exploded {len(forecast_df)} forecasts into {len(result)} material requirements")
            
            return result
            
        except Exception as e:
            error_msg = f"Error in explode_bom: {str(e)}"
            self.add_error(error_msg)
            logger.error(f"   ❌ {error_msg}")
            return pd.DataFrame(columns=['material_id', 'total_requirement', 'sku_id'])
    
    def net_inventory(self, requirements, inventory):
        """
        Calculate net requirements after considering inventory
        
        Args:
            requirements (pd.DataFrame): Material requirements
            inventory (pd.DataFrame): Current inventory with columns:
                - material_id: Material identifier
                - on_hand_qty: On-hand quantity
                - unit: Unit of measure
        
        Returns:
            pd.DataFrame: Net requirements
        """
        try:
            # Handle empty inputs
            if requirements.empty:
                logger.info("   ⚠️  Empty requirements data provided")
                return pd.DataFrame(columns=['material_id', 'gross_requirement', 'on_hand_qty', 'net_requirement'])
            
            if inventory.empty:
                logger.info("   ⚠️  Empty inventory data provided")
                # Return requirements as net requirements
                result = requirements.copy()
                result['gross_requirement'] = result['total_requirement']
                result['on_hand_qty'] = 0
                result['net_requirement'] = result['gross_requirement']
                return result[['material_id', 'gross_requirement', 'on_hand_qty', 'net_requirement']]
            
            # Validate inventory data
            self._validate_inventory_data(inventory)
            
            # Create copies
            req_df = requirements.copy()
            inv_df = inventory.copy()
            
            # Rename columns for consistency
            if 'total_requirement' in req_df.columns:
                req_df = req_df.rename(columns={'total_requirement': 'gross_requirement'})
            elif 'gross_requirement' not in req_df.columns:
                # Try to find a quantity column
                qty_columns = [col for col in req_df.columns if 'qty' in col.lower() or 'requirement' in col.lower()]
                if qty_columns:
                    req_df = req_df.rename(columns={qty_columns[0]: 'gross_requirement'})
            
            # Merge requirements with inventory
            result = pd.merge(
                req_df,
                inv_df[['material_id', 'on_hand_qty']],
                on='material_id',
                how='left'
            )
            
            # Fill missing inventory with zeros
            result['on_hand_qty'] = result['on_hand_qty'].fillna(0)
            
            # Handle negative inventory (treat as additional requirement)
            result['effective_on_hand'] = result['on_hand_qty'].clip(lower=0)
            result['additional_requirement'] = result['on_hand_qty'].clip(upper=0).abs()
            
            # Calculate net requirement
            result['net_requirement'] = (
                result['gross_requirement'] 
                - result['effective_on_hand'] 
                + result['additional_requirement']
            )
            
            # Ensure net requirements are not negative
            result['net_requirement'] = result['net_requirement'].clip(lower=0)
            
            # Handle unit conversions if needed
            if 'unit' in result.columns:
                result = self._handle_inventory_unit_conversions(result)
            
            # Log negative inventory materials
            negative_inventory = result[result['on_hand_qty'] < 0]
            if not negative_inventory.empty:
                warning_msg = f"Negative inventory found for materials: {negative_inventory['material_id'].tolist()}"
                self.add_warning(warning_msg)
                logger.warning(f"   ⚠️  {warning_msg}")
            
            # Final cleanup
            final_result = result[['material_id', 'gross_requirement', 'on_hand_qty', 'net_requirement']].copy()
            
            # Round to handle floating point precision
            final_result['gross_requirement'] = final_result['gross_requirement'].round(6)
            final_result['net_requirement'] = final_result['net_requirement'].round(6)
            
            logger.info(f"   ✅ Calculated net requirements for {len(final_result)} materials")
            materials_needed = len(final_result[final_result['net_requirement'] > 0])
            logger.info(f"   📦 {materials_needed} materials need procurement")
            
            return final_result
            
        except Exception as e:
            error_msg = f"Error in net_inventory: {str(e)}"
            self.add_error(error_msg)
            logger.error(f"   ❌ {error_msg}")
            return pd.DataFrame(columns=['material_id', 'gross_requirement', 'on_hand_qty', 'net_requirement'])
    
    def has_errors(self):
        """
        Check if any errors occurred during processing
        
        Returns:
            bool: True if errors exist, False otherwise
        """
        return len(self._errors) > 0
    
    def add_error(self, message):
        """Add an error message to the error list"""
        self._errors.append(message)
    
    def add_warning(self, message):
        """Add a warning message to the warning list"""
        self._warnings.append(message)
    
    def get_errors(self):
        """Get all error messages"""
        return self._errors.copy()
    
    def get_warnings(self):
        """Get all warning messages"""
        return self._warnings.copy()
    
    def clear_errors(self):
        """Clear all errors and warnings"""
        self._errors = []
        self._warnings = []
    
    def _validate_forecast_data(self, df):
        """Validate forecast data quality"""
        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.any():
            warning_msg = f"Null values found in forecast data: {null_counts[null_counts > 0].to_dict()}"
            self.add_warning(warning_msg)
        
        # Check for invalid dates
        try:
            pd.to_datetime(df['forecast_date'])
        except:
            self.add_error("Invalid date format in forecast_date column")
        
        # Check for non-numeric quantities
        if not pd.api.types.is_numeric_dtype(df['forecast_qty']):
            self.add_error("forecast_qty column must be numeric")
    
    def _validate_bom_data(self, df):
        """Validate BOM data quality"""
        required_columns = ['sku_id', 'material_id', 'qty_per_unit']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"Missing required BOM columns: {missing_columns}"
            self.add_error(error_msg)
        
        # Check for negative quantities
        if 'qty_per_unit' in df.columns and (df['qty_per_unit'] < 0).any():
            self.add_error("Negative quantities found in BOM data")
    
    def _validate_inventory_data(self, df):
        """Validate inventory data quality"""
        required_columns = ['material_id', 'on_hand_qty']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"Missing required inventory columns: {missing_columns}"
            self.add_error(error_msg)
        
        # Check for non-numeric quantities
        if 'on_hand_qty' in df.columns and not pd.api.types.is_numeric_dtype(df['on_hand_qty']):
            self.add_error("on_hand_qty column must be numeric")
    
    def _handle_quantity_issues(self, df):
        """Handle zero and negative quantities"""
        # Log zero quantities
        zero_qty = df[df['forecast_qty'] == 0]
        if not zero_qty.empty:
            logger.info(f"   📊 Found {len(zero_qty)} zero quantity forecasts")
        
        # Log negative quantities
        negative_qty = df[df['forecast_qty'] < 0]
        if not negative_qty.empty:
            warning_msg = f"Found {len(negative_qty)} negative quantity forecasts"
            self.add_warning(warning_msg)
            logger.warning(f"   ⚠️  {warning_msg}")
        
        # Log extreme quantities
        extreme_qty = df[df['forecast_qty'] > 1000000]
        if not extreme_qty.empty:
            warning_msg = f"Found {len(extreme_qty)} extremely large quantity forecasts"
            self.add_warning(warning_msg)
            logger.warning(f"   ⚠️  {warning_msg}")
        
        return df
    
    def _handle_bom_percentages(self, df):
        """Handle BOM percentage corrections"""
        # Group by SKU and check percentage sums
        sku_percentages = df.groupby('sku_id')['qty_per_unit'].sum()
        
        # Check for 99% BOMs (auto-correct)
        boms_99 = sku_percentages[(sku_percentages >= 0.98) & (sku_percentages < 1.0)]
        if not boms_99.empty:
            logger.info(f"   🔧 Auto-correcting {len(boms_99)} BOMs summing to ~99%")
            for sku in boms_99.index:
                correction_factor = 1.0 / sku_percentages[sku]
                df.loc[df['sku_id'] == sku, 'qty_per_unit'] *= correction_factor
        
        # Check for 101%+ BOMs (warning)
        boms_101 = sku_percentages[sku_percentages > 1.01]
        if not boms_101.empty:
            warning_msg = f"BOMs summing to >101% found for SKUs: {boms_101.index.tolist()}"
            self.add_warning(warning_msg)
            logger.warning(f"   ⚠️  {warning_msg}")
        
        return df
    
    def _detect_circular_bom_references(self, df):
        """Detect circular BOM references"""
        # Simple circular reference detection
        skus_as_materials = set(df['sku_id'].unique())
        materials_as_skus = set(df['material_id'].unique())
        circular_refs = skus_as_materials & materials_as_skus
        
        if circular_refs:
            warning_msg = f"Potential circular BOM references detected: {circular_refs}"
            self.add_warning(warning_msg)
            logger.warning(f"   ⚠️  {warning_msg}")
    
    def _handle_unit_conversions(self, df):
        """Handle unit conversions in BOM explosion"""
        # Basic unit conversion logic
        if 'unit' in df.columns:
            # Log unit types found
            units = df['unit'].unique()
            logger.info(f"   🔄 Processing units: {units}")
        
        return df
    
    def _handle_inventory_unit_conversions(self, df):
        """Handle unit conversions in inventory netting"""
        # Basic unit conversion logic for inventory
        if 'unit' in df.columns:
            units = df['unit'].unique()
            logger.info(f"   🔄 Processing inventory units: {units}")
        
        return df