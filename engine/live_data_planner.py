"""
Live Data Planning Engine for Beverly Knits
===========================================
Planning engine optimized for live CSV data format:
- Direct integration with live data models
- Enhanced BOM explosion for style-to-yarn mapping
- Live data specific safety stock calculations
- Risk assessment based on live data patterns
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import numpy as np
from pathlib import Path

from data.live_data_integration import LiveDataIntegrator
from models.live_data_models import YarnDemandByStyle, SalesOrder, StyleBOM, YarnMaster
from models.recommendation import ProcurementRecommendation
from models.supplier import EOQCalculator
from utils.logger import get_logger

logger = get_logger(__name__)


class LiveDataPlanner:
    """Planning engine optimized for Beverly Knits live data format"""
    
    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        self.integrator = LiveDataIntegrator(data_path)
        self.eoq_calculator = EOQCalculator()
        
        # Planning parameters
        self.config = {
            'safety_stock_percentage': 0.2,
            'lead_time_buffer_days': 7,
            'min_order_threshold': 100,
            'max_order_multiple': 10000,
            'planning_horizon_days': 90,
            'enable_multi_supplier': True,
            'service_level': 0.95
        }
        
        # Storage for planning results
        self.planning_data = {}
        self.material_requirements = {}
        self.procurement_recommendations = []
        self.risk_assessments = {}
        self.planning_summary = {}
    
    def run_full_planning_cycle(self) -> Dict[str, Any]:
        """Execute complete planning cycle with live data"""
        logger.info("Starting Beverly Knits Live Data Planning Cycle")
        logger.info("=" * 55)
        
        # Step 1: Load and integrate live data
        logger.info("Step 1: Loading live data...")
        planning_inputs = self.integrator.generate_planning_inputs()
        self.planning_data = planning_inputs['planning_data']
        
        # Step 2: Explode style forecasts to yarn requirements
        logger.info("Step 2: Exploding style forecasts to yarn requirements...")
        self.material_requirements = self._explode_style_to_yarn_requirements()
        
        # Step 3: Calculate net requirements
        logger.info("Step 3: Calculating net requirements...")
        net_requirements = self._calculate_net_requirements()
        
        # Step 4: Generate procurement recommendations
        logger.info("Step 4: Generating procurement recommendations...")
        self.procurement_recommendations = self._generate_procurement_recommendations(net_requirements)
        
        # Step 5: Assess risks
        logger.info("Step 5: Assessing risks...")
        self.risk_assessments = self._assess_procurement_risks()
        
        # Step 6: Generate planning summary
        logger.info("Step 6: Generating planning summary...")
        self.planning_summary = self._generate_planning_summary()
        
        logger.info("✅ Live data planning cycle completed successfully")
        return self._compile_planning_results()
    
    def _explode_style_to_yarn_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Explode style forecasts to yarn requirements using live BOM data"""
        yarn_requirements = defaultdict(lambda: {
            'total_requirement': 0.0,
            'sources': [],
            'unit': 'lbs',
            'planning_weeks': defaultdict(float)
        })
        
        # Load live BOM data
        bom_data = self.integrator.live_data.get('style_bom', [])
        yarn_demand_data = self.integrator.live_data.get('yarn_demand_by_style', [])
        
        # Create BOM lookup
        bom_lookup = defaultdict(list)
        for bom in bom_data:
            bom_lookup[bom.style_id].append(bom)
        
        # Process forecasts
        for forecast in self.planning_data.get('forecasts', []):
            style_id = forecast.sku_id
            forecast_qty = forecast.forecast_qty
            
            # Get BOM for this style
            style_boms = bom_lookup.get(style_id, [])
            
            if not style_boms:
                logger.warning(f"No BOM found for style {style_id}")
                continue
            
            # Explode to yarn requirements
            for bom in style_boms:
                yarn_requirement = forecast_qty * bom.bom_percentage
                
                yarn_requirements[bom.yarn_id]['total_requirement'] += yarn_requirement
                yarn_requirements[bom.yarn_id]['sources'].append({
                    'style_id': style_id,
                    'forecast_qty': forecast_qty,
                    'bom_percentage': bom.bom_percentage,
                    'yarn_requirement': yarn_requirement,
                    'source': forecast.source
                })
        
        # Add yarn demand data for enhanced planning
        for yarn_demand in yarn_demand_data:
            yarn_id = yarn_demand.yarn
            
            # Add weekly demand breakdown
            weekly_demands = {
                'this_week': yarn_demand.this_week,
                'week_17': yarn_demand.week_17,
                'week_18': yarn_demand.week_18,
                'week_19': yarn_demand.week_19,
                'week_20': yarn_demand.week_20,
                'week_21': yarn_demand.week_21,
                'week_22': yarn_demand.week_22,
                'week_23': yarn_demand.week_23,
                'week_24': yarn_demand.week_24,
                'later': yarn_demand.later
            }
            
            for week, demand in weekly_demands.items():
                if demand > 0:
                    yarn_requirements[yarn_id]['planning_weeks'][week] += demand
            
            # Add to total requirement if not already included
            if yarn_demand.total > yarn_requirements[yarn_id]['total_requirement']:
                yarn_requirements[yarn_id]['total_requirement'] = max(
                    yarn_requirements[yarn_id]['total_requirement'],
                    yarn_demand.total
                )
        
        logger.info(f"✅ Generated requirements for {len(yarn_requirements)} yarns")
        return dict(yarn_requirements)
    
    def _calculate_net_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Calculate net requirements after inventory netting"""
        net_requirements = {}
        
        # Create inventory lookup
        inventory_lookup = {}
        for inv in self.planning_data.get('inventory', []):
            inventory_lookup[inv.material_id] = inv
        
        for yarn_id, req_data in self.material_requirements.items():
            gross_requirement = req_data['total_requirement']
            
            # Get inventory
            inventory = inventory_lookup.get(yarn_id)
            if inventory:
                on_hand = inventory.on_hand_qty
                on_order = inventory.open_po_qty
                available = on_hand + on_order
            else:
                available = 0
            
            # Calculate net requirement
            net_requirement = max(0, gross_requirement - available)
            
            # Add safety stock
            safety_stock = gross_requirement * self.config['safety_stock_percentage']
            buffered_requirement = net_requirement + safety_stock
            
            if buffered_requirement > 0:
                net_requirements[yarn_id] = {
                    'yarn_id': yarn_id,
                    'gross_requirement': gross_requirement,
                    'available_inventory': available,
                    'net_requirement': net_requirement,
                    'safety_stock': safety_stock,
                    'total_requirement': buffered_requirement,
                    'sources': req_data['sources'],
                    'planning_weeks': req_data['planning_weeks']
                }
        
        logger.info(f"✅ Calculated net requirements for {len(net_requirements)} yarns")
        return net_requirements
    
    def _generate_procurement_recommendations(self, net_requirements: Dict[str, Dict[str, Any]]) -> List[ProcurementRecommendation]:
        """Generate procurement recommendations"""
        recommendations = []
        
        # Create supplier lookup
        supplier_lookup = defaultdict(list)
        for supplier in self.planning_data.get('suppliers', []):
            supplier_lookup[supplier.material_id].append(supplier)
        
        # Create yarn master lookup for additional info
        yarn_master_lookup = {}
        for yarn in self.integrator.live_data.get('yarn_master', []):
            yarn_master_lookup[yarn.yarn_id] = yarn
        
        for yarn_id, req_data in net_requirements.items():
            requirement = req_data['total_requirement']
            
            # Get suppliers for this yarn
            suppliers = supplier_lookup.get(yarn_id, [])
            if not suppliers:
                logger.warning(f"No suppliers found for yarn {yarn_id}")
                continue
            
            # Get yarn master data
            yarn_master = yarn_master_lookup.get(yarn_id)
            
            # Select best supplier (lowest cost)
            best_supplier = min(suppliers, key=lambda s: s.cost_per_unit)
            
            # Calculate EOQ
            eoq = self.eoq_calculator.calculate_eoq(
                requirement,
                best_supplier.ordering_cost,
                best_supplier.cost_per_unit,
                best_supplier.holding_cost_rate
            )
            
            # Apply MOQ constraint
            order_qty = max(eoq, best_supplier.moq)
            
            # Round to reasonable order multiple
            order_multiple = min(self.config['max_order_multiple'], max(100, int(order_qty * 0.1)))
            order_qty = np.ceil(order_qty / order_multiple) * order_multiple
            
            # Calculate delivery date
            delivery_date = datetime.now().date() + timedelta(
                days=best_supplier.lead_time_days + self.config['lead_time_buffer_days']
            )
            
            # Determine urgency
            urgency = self._calculate_urgency(req_data, best_supplier.lead_time_days)
            
            # Create recommendation
            recommendation = ProcurementRecommendation(
                material_id=yarn_id,
                supplier_id=best_supplier.supplier_id,
                order_qty=order_qty,
                unit_price=best_supplier.cost_per_unit,
                total_cost=order_qty * best_supplier.cost_per_unit,
                order_date=datetime.now().date(),
                delivery_date=delivery_date,
                urgency=urgency,
                notes=self._generate_recommendation_notes(req_data, yarn_master, best_supplier),
                risk_flags=self._assess_yarn_risks(yarn_id, req_data, yarn_master, best_supplier)
            )
            
            recommendations.append(recommendation)
        
        # Sort by urgency and total cost
        recommendations.sort(key=lambda r: (r.urgency != 'high', r.total_cost), reverse=True)
        
        logger.info(f"✅ Generated {len(recommendations)} procurement recommendations")
        return recommendations
    
    def _calculate_urgency(self, req_data: Dict[str, Any], lead_time_days: int) -> str:
        """Calculate urgency based on planning weeks and lead time"""
        planning_weeks = req_data.get('planning_weeks', {})
        
        # Check if demand is needed in current week or next week
        current_week_demand = planning_weeks.get('this_week', 0)
        near_term_demand = current_week_demand + planning_weeks.get('week_17', 0)
        
        # Calculate urgency
        if current_week_demand > 0:
            return 'high'
        elif near_term_demand > 0 and lead_time_days > 7:
            return 'high'
        elif lead_time_days > 21:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendation_notes(self, req_data: Dict[str, Any], 
                                     yarn_master: Optional[YarnMaster], 
                                     supplier) -> str:
        """Generate detailed notes for procurement recommendation"""
        notes = []
        
        # Add requirement sources
        sources = req_data.get('sources', [])
        if sources:
            style_count = len(set(s['style_id'] for s in sources))
            notes.append(f"Required by {style_count} styles")
        
        # Add yarn details
        if yarn_master:
            notes.append(f"Yarn: {yarn_master.description}")
            notes.append(f"Blend: {yarn_master.blend}")
            if yarn_master.planning_balance < 0:
                notes.append(f"Current shortage: {abs(yarn_master.planning_balance):.0f} lbs")
        
        # Add supplier info
        notes.append(f"Supplier: {supplier.supplier_name}")
        notes.append(f"Lead time: {supplier.lead_time_days} days")
        
        return " | ".join(notes)
    
    def _assess_yarn_risks(self, yarn_id: str, req_data: Dict[str, Any], 
                          yarn_master: Optional[YarnMaster], supplier) -> List[str]:
        """Assess risks for yarn procurement"""
        risks = []
        
        # Supply risk
        if supplier.lead_time_days > 30:
            risks.append("Long lead time")
        
        if supplier.supplier_type == "Import":
            risks.append("Import supplier")
        
        # Demand risk
        total_requirement = req_data['total_requirement']
        if total_requirement > 10000:
            risks.append("High volume requirement")
        
        # Inventory risk
        if yarn_master and yarn_master.planning_balance < 0:
            risks.append("Current stockout")
        
        # Cost risk
        if supplier.cost_per_unit > 10:
            risks.append("High cost material")
        
        return risks
    
    def _assess_procurement_risks(self) -> Dict[str, Dict[str, Any]]:
        """Assess overall procurement risks"""
        risks = {}
        
        # Supplier concentration risk
        supplier_loads = defaultdict(list)
        for rec in self.procurement_recommendations:
            supplier_loads[rec.supplier_id].append(rec)
        
        # High concentration suppliers
        high_concentration = []
        for supplier_id, recs in supplier_loads.items():
            total_value = sum(r.total_cost for r in recs)
            if total_value > 100000:  # $100K threshold
                high_concentration.append({
                    'supplier_id': supplier_id,
                    'total_value': total_value,
                    'order_count': len(recs)
                })
        
        # Lead time risk
        long_lead_time = [
            r for r in self.procurement_recommendations 
            if r.delivery_date > datetime.now().date() + timedelta(days=30)
        ]
        
        # Cost risk
        high_cost_items = sorted(
            self.procurement_recommendations,
            key=lambda r: r.total_cost,
            reverse=True
        )[:10]
        
        risks['summary'] = {
            'total_recommendations': len(self.procurement_recommendations),
            'high_concentration_suppliers': len(high_concentration),
            'long_lead_time_items': len(long_lead_time),
            'high_cost_items': len(high_cost_items)
        }
        
        risks['details'] = {
            'supplier_concentration': high_concentration,
            'lead_time_risks': [
                {'material_id': r.material_id, 'delivery_date': r.delivery_date, 
                 'lead_time_days': (r.delivery_date - datetime.now().date()).days}
                for r in long_lead_time
            ],
            'cost_risks': [
                {'material_id': r.material_id, 'total_cost': r.total_cost}
                for r in high_cost_items
            ]
        }
        
        return risks
    
    def _generate_planning_summary(self) -> Dict[str, Any]:
        """Generate comprehensive planning summary"""
        if not self.procurement_recommendations:
            return {'error': 'No procurement recommendations generated'}
        
        # Calculate summary statistics
        total_cost = sum(r.total_cost for r in self.procurement_recommendations)
        total_materials = len(set(r.material_id for r in self.procurement_recommendations))
        total_suppliers = len(set(r.supplier_id for r in self.procurement_recommendations))
        
        # Urgency breakdown
        urgency_counts = defaultdict(int)
        for rec in self.procurement_recommendations:
            urgency_counts[rec.urgency] += 1
        
        # Cost breakdown
        cost_ranges = {
            'under_1k': 0,
            '1k_to_5k': 0,
            '5k_to_10k': 0,
            'over_10k': 0
        }
        
        for rec in self.procurement_recommendations:
            cost = rec.total_cost
            if cost < 1000:
                cost_ranges['under_1k'] += 1
            elif cost < 5000:
                cost_ranges['1k_to_5k'] += 1
            elif cost < 10000:
                cost_ranges['5k_to_10k'] += 1
            else:
                cost_ranges['over_10k'] += 1
        
        # Timeline analysis
        delivery_dates = [r.delivery_date for r in self.procurement_recommendations]
        earliest_delivery = min(delivery_dates)
        latest_delivery = max(delivery_dates)
        
        return {
            'planning_date': datetime.now().date(),
            'data_source': 'live_csv_files',
            'totals': {
                'total_cost': total_cost,
                'total_materials': total_materials,
                'total_suppliers': total_suppliers,
                'total_orders': len(self.procurement_recommendations)
            },
            'urgency_breakdown': dict(urgency_counts),
            'cost_breakdown': cost_ranges,
            'timeline': {
                'earliest_delivery': earliest_delivery,
                'latest_delivery': latest_delivery,
                'planning_horizon_days': (latest_delivery - earliest_delivery).days
            },
            'top_cost_items': [
                {
                    'material_id': r.material_id,
                    'supplier_id': r.supplier_id,
                    'total_cost': r.total_cost,
                    'urgency': r.urgency
                }
                for r in sorted(self.procurement_recommendations, 
                              key=lambda x: x.total_cost, reverse=True)[:10]
            ]
        }
    
    def _compile_planning_results(self) -> Dict[str, Any]:
        """Compile all planning results into a comprehensive report"""
        return {
            'planning_summary': self.planning_summary,
            'procurement_recommendations': [
                {
                    'material_id': r.material_id,
                    'supplier_id': r.supplier_id,
                    'order_qty': r.order_qty,
                    'unit_price': r.unit_price,
                    'total_cost': r.total_cost,
                    'order_date': r.order_date,
                    'delivery_date': r.delivery_date,
                    'urgency': r.urgency,
                    'notes': r.notes,
                    'risk_flags': r.risk_flags
                }
                for r in self.procurement_recommendations
            ],
            'material_requirements': self.material_requirements,
            'risk_assessment': self.risk_assessments,
            'data_quality': self.integrator.validation_results,
            'planning_config': self.config
        }
    
    def export_planning_results(self, output_path: str = "output/") -> Dict[str, str]:
        """Export planning results to files"""
        
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        exported_files = {}
        
        # Export procurement recommendations
        if self.procurement_recommendations:
            recommendations_df = pd.DataFrame([
                {
                    'Material_ID': r.material_id,
                    'Supplier_ID': r.supplier_id,
                    'Order_Quantity': r.order_qty,
                    'Unit_Price': r.unit_price,
                    'Total_Cost': r.total_cost,
                    'Order_Date': r.order_date,
                    'Delivery_Date': r.delivery_date,
                    'Urgency': r.urgency,
                    'Notes': r.notes,
                    'Risk_Flags': ', '.join(r.risk_flags)
                }
                for r in self.procurement_recommendations
            ])
            
            rec_file = output_dir / "live_data_procurement_recommendations.csv"
            recommendations_df.to_csv(rec_file, index=False)
            exported_files['recommendations'] = str(rec_file)
        
        # Export material requirements
        if self.material_requirements:
            requirements_df = pd.DataFrame([
                {
                    'Yarn_ID': yarn_id,
                    'Total_Requirement': f"{req['total_requirement']:,.0f}",
                    'Unit': req['unit'],
                    'Source_Styles': len(set(s['style_id'] for s in req['sources'])),
                    'This_Week': req['planning_weeks'].get('this_week', 0),
                    'Week_17_24': sum(req['planning_weeks'].get(f'week_{i}', 0) for i in range(17, 25)),
                    'Later': req['planning_weeks'].get('later', 0)
                }
                for yarn_id, req in self.material_requirements.items()
            ])
            
            req_file = output_dir / "live_data_material_requirements.csv"
            requirements_df.to_csv(req_file, index=False)
            exported_files['requirements'] = str(req_file)
        
        # Export planning summary
        if self.planning_summary:
            summary_file = output_dir / "live_data_planning_summary.json"
            import json
            with open(summary_file, 'w') as f:
                json.dump(self.planning_summary, f, indent=2, default=str)
            exported_files['summary'] = str(summary_file)
        
        # Export to Excel for business users
        self._export_to_excel(output_dir)
        exported_files['excel'] = str(output_dir / "live_data_planning_results.xlsx")
        
        return exported_files
    
    def _export_to_excel(self, output_dir: Path):
        """Export planning results to Excel with multiple sheets"""
        try:
            with pd.ExcelWriter(output_dir / "live_data_planning_results.xlsx", engine='openpyxl') as writer:
                # Sheet 1: Procurement Recommendations
                if self.procurement_recommendations:
                    recommendations_df = pd.DataFrame([
                        {
                            'Material_ID': r.material_id,
                            'Supplier_ID': r.supplier_id,
                            'Order_Quantity': r.order_qty,
                            'Unit_Price': f"${r.unit_price:.2f}",
                            'Total_Cost': f"${r.total_cost:,.2f}",
                            'Order_Date': r.order_date,
                            'Delivery_Date': r.delivery_date,
                            'Urgency': r.urgency,
                            'Risk_Flags': ', '.join(r.risk_flags)
                        }
                        for r in self.procurement_recommendations
                    ])
                    recommendations_df.to_excel(writer, sheet_name='Procurement_Recommendations', index=False)
                
                # Sheet 2: Material Requirements
                if self.material_requirements:
                    requirements_df = pd.DataFrame([
                        {
                            'Yarn_ID': yarn_id,
                            'Total_Requirement': f"{req['total_requirement']:,.0f}",
                            'Unit': req['unit'],
                            'Source_Styles': len(set(s['style_id'] for s in req['sources'])),
                            'This_Week': req['planning_weeks'].get('this_week', 0),
                            'Week_17_24': sum(req['planning_weeks'].get(f'week_{i}', 0) for i in range(17, 25)),
                            'Later': req['planning_weeks'].get('later', 0)
                        }
                        for yarn_id, req in self.material_requirements.items()
                    ])
                    requirements_df.to_excel(writer, sheet_name='Material_Requirements', index=False)
                
                # Sheet 3: Planning Summary
                if self.planning_summary:
                    summary_data = []
                    for key, value in self.planning_summary.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                summary_data.append({
                                    'Category': key,
                                    'Metric': sub_key,
                                    'Value': sub_value
                                })
                        else:
                            summary_data.append({
                                'Category': 'General',
                                'Metric': key,
                                'Value': value
                            })
                    
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Planning_Summary', index=False)
                
                logger.info("✅ Exported planning results to Excel")
        
        except Exception as e:
            logger.warning(f"Could not export to Excel: {e}")


def main():
    """Main function for testing the live data planner"""
    planner = LiveDataPlanner()
    
    # Run full planning cycle
    results = planner.run_full_planning_cycle()
    
    # Export results
    exported_files = planner.export_planning_results()
    
    # Print summary
    print("\nLive Data Planning Summary:")
    print(f"Total recommendations: {len(results['procurement_recommendations'])}")
    print(f"Total cost: ${results['planning_summary']['totals']['total_cost']:,.2f}")
    print(f"Materials planned: {results['planning_summary']['totals']['total_materials']}")
    print(f"Suppliers involved: {results['planning_summary']['totals']['total_suppliers']}")
    print(f"Files exported: {len(exported_files)}")
    
    return results


if __name__ == "__main__":
    main()