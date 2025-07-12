"""
Planning Engine - Orchestrates the raw material planning process
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from functools import lru_cache
from pathlib import Path
import json

import pandas as pd
from utils.logger import get_logger

from config.settings import PlanningConfig

logger = get_logger(__name__, level="DEBUG")
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

        # Debug logging
        logger.debug(f"Loaded suppliers for {len(suppliers_by_material)} materials")
        if len(suppliers_by_material) > 0:
            sample_materials = list(suppliers_by_material.keys())[:5]
            logger.debug(f"Sample material IDs in suppliers: {sample_materials}")

        for material_id, req_data in net_requirements.items():
            net_requirement = req_data['net_requirement']
            if net_requirement <= 0:
                continue

            material_suppliers = suppliers_by_material.get(material_id, [])
            if not material_suppliers:
                logger.info(f"   [WARNING] No suppliers found for material {material_id}")
                # Debug logging
                if len(suppliers_by_material) > 0:
                    sample_keys = list(suppliers_by_material.keys())[:5]
                    logger.debug(f"   Sample supplier material IDs: {sample_keys}")
                    logger.debug(f"   Looking for: {material_id} (type: {type(material_id)})")
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
                selected_supplier = self.supplier_selector.select_optimal_supplier(
                    material_id=material_id,
                    suppliers=material_suppliers,
                    required_quantity=buffered_requirement
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
            # Check if we should use the pre-generated forecasts
            forecast_file = Path('output/generated_forecasts.csv')
            integration_file = Path('output/sales_forecast_integration.json')

            # If recent forecast file exists, use it
            if forecast_file.exists() and integration_file.exists():
                # Check if forecast is recent (within 24 hours)
                file_age = datetime.now() - datetime.fromtimestamp(forecast_file.stat().st_mtime)
                if file_age.total_seconds() < 86400:  # 24 hours
                    logger.info("   Using pre-generated forecasts from sales analysis")

                    # Load integration metadata
                    with open(integration_file, 'r') as f:
                        integration_data = json.load(f)

                    # Load forecasts
                    forecast_df = pd.read_csv(forecast_file)
                    forecasts = []

                    for _, row in forecast_df.iterrows():
                        # Handle both 'quantity' and 'forecast_qty' column names
                        qty = row.get('forecast_qty', row.get('quantity', 0))
                        forecast = FinishedGoodsForecast(
                            sku_id=row['sku_id'],
                            forecast_qty=qty,
                            source=row.get('source', 'sales_history'),
                            confidence=row.get('confidence', 0.8),
                            forecast_date=pd.to_datetime(row.get('forecast_date', datetime.now().date())),
                            unit=row.get('unit', 'yards'),
                            notes=row.get('notes', 'Generated from sales history')
                        )
                        forecasts.append(forecast)

                    logger.info(f"   [OK] Loaded {len(forecasts)} forecasts from file")
                    logger.info(f"   Total forecast quantity: {integration_data.get('total_forecast_qty', 0):,.0f}")
                    return forecasts

            # Otherwise, generate new forecasts
            logger.info("   🔄 Generating new forecasts from sales data...")
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
                logger.info(f"   Exploding {len(style_forecasts)} style forecasts to yarn requirements")
                yarn_requirements = integrator.explode_style_forecast_to_yarn(style_forecasts)

                # Log summary
                total_yarn_qty = sum(req['total_qty'] for req in yarn_requirements.values())
                logger.info(f"   [OK] Generated requirements for {len(yarn_requirements)} yarns")
                logger.info(f"   Total yarn required: {total_yarn_qty:,.0f} yards")

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

    def get_planning_stats(self) -> Dict[str, any]:
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

    def _generate_reports(self, recommendations: List[ProcurementRecommendation]):
        """Generate output reports from recommendations"""
        # For now, just log a summary
        if recommendations:
            total_cost = sum(r.total_cost for r in recommendations)
            logger.info(f"   Total procurement cost: ${total_cost:,.2f}")
            logger.info(f"   Number of purchase orders: {len(recommendations)}")
        else:
            logger.info("   No procurement recommendations generated")

        # In a real implementation, this would generate CSV/Excel reports
        # For now, we'll just store the recommendations
        self._recommendations = recommendations


class MaterialPlanner:
    """
    Simplified MaterialPlanner class for backward compatibility with tests
    This is a wrapper around RawMaterialPlanner with the expected interface
    """
    
    def __init__(self, config=None):
        """Initialize with optional config"""
        if config is None:
            # Create a minimal config for testing
            config = {
                'safety_buffer': 0.1,
                'enable_multi_supplier': True
            }
        
        # If config is a dict, convert to object-like structure
        if isinstance(config, dict):
            class ConfigObject:
                def __init__(self, config_dict):
                    for key, value in config_dict.items():
                        setattr(self, key, value)
            config = ConfigObject(config)
        
        self.config = config
        self.planner = RawMaterialPlanner(config) if hasattr(config, '__dict__') else None
    
    def unify_forecasts(self, forecast_data):
        """Unify forecast data from multiple sources"""
        if isinstance(forecast_data, pd.DataFrame):
            # Convert DataFrame to simple dict for testing
            unified = {}
            for _, row in forecast_data.iterrows():
                sku_id = row.get('sku_id', 'unknown')
                qty = row.get('forecast_qty', 0)
                unified[sku_id] = qty
            return pd.DataFrame(list(unified.items()), columns=['sku_id', 'unified_qty'])
        return forecast_data
    
    def explode_bom(self, bom_data, forecast_data):
        """Explode BOM to material requirements"""
        if isinstance(bom_data, pd.DataFrame) and isinstance(forecast_data, pd.DataFrame):
            # Simple BOM explosion for testing
            requirements = []
            for _, bom_row in bom_data.iterrows():
                sku_id = bom_row.get('sku_id', '')
                material_id = bom_row.get('material_id', '')
                qty_per_unit = bom_row.get('qty_per_unit', 1.0)
                
                # Find matching forecast
                forecast_match = forecast_data[forecast_data['sku_id'] == sku_id]
                if not forecast_match.empty:
                    forecast_qty = forecast_match.iloc[0].get('unified_qty', 0)
                    total_requirement = forecast_qty * qty_per_unit
                    requirements.append({
                        'material_id': material_id,
                        'requirement': total_requirement
                    })
            
            return pd.DataFrame(requirements)
        return bom_data
    
    def net_inventory(self, requirements_data, inventory_data):
        """Calculate net requirements after inventory"""
        if isinstance(requirements_data, pd.DataFrame) and isinstance(inventory_data, pd.DataFrame):
            # Simple netting for testing
            net_requirements = []
            for _, req_row in requirements_data.iterrows():
                material_id = req_row.get('material_id', '')
                gross_requirement = req_row.get('requirement', 0)
                
                # Find matching inventory
                inventory_match = inventory_data[inventory_data['material_id'] == material_id]
                on_hand = inventory_match.iloc[0].get('on_hand_qty', 0) if not inventory_match.empty else 0
                
                net_requirement = max(0, gross_requirement - on_hand)
                net_requirements.append({
                    'material_id': material_id,
                    'net_requirement': net_requirement
                })
            
            return pd.DataFrame(net_requirements)
        return requirements_data
    
    def optimize_procurement(self, net_requirements):
        """Optimize procurement quantities"""
        if isinstance(net_requirements, pd.DataFrame):
            # Simple optimization for testing
            optimized = []
            for _, row in net_requirements.iterrows():
                material_id = row.get('material_id', '')
                net_req = row.get('net_requirement', 0)
                
                # Apply simple optimization (add safety stock)
                optimized_qty = net_req * 1.1  # 10% safety buffer
                optimized.append({
                    'material_id': material_id,
                    'optimized_qty': optimized_qty
                })
            
            return pd.DataFrame(optimized)
        return net_requirements
    
    def select_suppliers(self, optimized_requirements, suppliers_data):
        """Select suppliers for materials"""
        if isinstance(optimized_requirements, pd.DataFrame) and isinstance(suppliers_data, pd.DataFrame):
            # Simple supplier selection for testing
            selected = []
            for _, req_row in optimized_requirements.iterrows():
                material_id = req_row.get('material_id', '')
                quantity = req_row.get('optimized_qty', 0)
                
                # Find suppliers for this material
                material_suppliers = suppliers_data[suppliers_data['material_id'] == material_id]
                if not material_suppliers.empty:
                    # Select first supplier (simple logic)
                    supplier = material_suppliers.iloc[0]
                    selected.append({
                        'material_id': material_id,
                        'supplier_id': supplier.get('supplier_id', 'unknown'),
                        'quantity': quantity,
                        'unit_cost': supplier.get('cost_per_unit', 0)
                    })
            
            return pd.DataFrame(selected)
        return optimized_requirements
    
    def generate_recommendations(self, supplier_selections):
        """Generate final procurement recommendations"""
        if isinstance(supplier_selections, pd.DataFrame):
            # Simple recommendations for testing
            recommendations = []
            for _, row in supplier_selections.iterrows():
                material_id = row.get('material_id', '')
                supplier_id = row.get('supplier_id', '')
                quantity = row.get('quantity', 0)
                unit_cost = row.get('unit_cost', 0)
                total_cost = quantity * unit_cost
                
                recommendations.append({
                    'material_id': material_id,
                    'supplier_id': supplier_id,
                    'quantity': quantity,
                    'unit_cost': unit_cost,
                    'total_cost': total_cost
                })
            
            return pd.DataFrame(recommendations)
        return supplier_selections