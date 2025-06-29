"""
Planning Engine - Orchestrates the raw material planning process
"""

from collections import defaultdict
from utils.logger import get_logger

logger = get_logger(__name__)
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from config.settings import PlanningConfig
from models.bom import BillOfMaterials, BOMExploder
from models.forecast import FinishedGoodsForecast, ForecastProcessor
from models.inventory import Inventory, InventoryNetter
from models.recommendation import ProcurementRecommendation
from models.supplier import EOQCalculator, Supplier, SupplierSelector


class RawMaterialPlanner:
    """Main planning engine that orchestrates the planning process"""
    
    def __init__(self, config: PlanningConfig):
        self.config = config
        self.forecast_processor = ForecastProcessor(config)
        self.bom_exploder = BOMExploder()
        self.inventory_netter = InventoryNetter()
        self.supplier_selector = SupplierSelector(config)
        self.eoq_calculator = EOQCalculator()
        
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
                        selected_supplier.setup_cost,
                        selected_supplier.holding_cost_rate
                    )

                    # Apply MOQ constraint
                    order_qty = max(eoq, selected_supplier.moq)

                    # Round to order multiple if specified
                    if selected_supplier.order_multiple > 1:
                        order_qty = np.ceil(order_qty / selected_supplier.order_multiple) * selected_supplier.order_multiple

                    # Create recommendation
                    recommendation = ProcurementRecommendation(
                        material_id=material_id,
                        supplier_id=selected_supplier.supplier_id,
                        order_qty=order_qty,
                        unit_price=selected_supplier.unit_price,
                        total_cost=order_qty * selected_supplier.unit_price,
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
            logger.info(f"   ⚠️  Enhanced BOM integration not available, falling back to standard method")
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

        # Sort suppliers by total cost (price + shipping)
        sorted_suppliers = sorted(suppliers, key=lambda s: s.unit_price + (s.shipping_cost / 1000))

        for supplier in sorted_suppliers:
            if remaining_qty <= 0:
                break

            # Calculate optimal quantity for this supplier
            if remaining_qty >= supplier.moq:
                # Calculate EOQ for this supplier
                eoq = self.eoq_calculator.calculate_eoq(
                    remaining_qty,
                    supplier.setup_cost,
                    supplier.holding_cost_rate
                )

                # Apply constraints
                order_qty = max(eoq, supplier.moq)
                order_qty = min(order_qty, remaining_qty)

                # Round to order multiple
                if supplier.order_multiple > 1:
                    order_qty = np.ceil(order_qty / supplier.order_multiple) * supplier.order_multiple

                # Create recommendation
                recommendation = ProcurementRecommendation(
                    material_id=material_id,
                    supplier_id=supplier.supplier_id,
                    order_qty=order_qty,
                    unit_price=supplier.unit_price,
                    total_cost=order_qty * supplier.unit_price,
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