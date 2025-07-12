"""
Live Data Integration for Beverly Knits
=======================================
Processes live CSV files directly without requiring preprocessing:
- Loads all live data CSV files
- Converts to planning system format
- Validates data quality
- Generates planning inputs
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from models.live_data_models import (
    YarnDemandByStyle, SalesOrder, StyleBOM, InventoryItem, 
    SupplierInfo, YarnMaster, LiveDataValidator
)
from models.bom import BillOfMaterials
from models.forecast import FinishedGoodsForecast
from models.inventory import Inventory
from models.supplier import Supplier
from utils.logger import get_logger

logger = get_logger(__name__)


class LiveDataIntegrator:
    """Integrates live CSV files directly into the planning system"""
    
    def __init__(self, data_path: str = "data/"):
        self.data_path = Path(data_path)
        self.live_data = {}
        self.processed_data = {}
        self.validation_results = {}
        
    def load_all_live_data(self) -> Dict[str, Any]:
        """Load all live CSV files"""
        logger.info("Loading Beverly Knits live data files...")
        
        # Load all live data files
        self.live_data = {
            'yarn_demand_by_style': self._load_yarn_demand_by_style(),
            'sales_orders': self._load_sales_orders(),
            'style_bom': self._load_style_bom(),
            'inventory': self._load_inventory(),
            'suppliers': self._load_suppliers(),
            'yarn_master': self._load_yarn_master()
        }
        
        # Validate all data
        self._validate_all_data()
        
        logger.info("✅ Live data loading complete")
        return self.live_data
    
    def _load_yarn_demand_by_style(self) -> List[YarnDemandByStyle]:
        """Load cfab_Yarn_Demand_By_Style.csv"""
        file_path = self.data_path / "cfab_Yarn_Demand_By_Style.csv"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        df = pd.read_csv(file_path)
        data = [YarnDemandByStyle.from_csv_row(row) for _, row in df.iterrows()]
        logger.info(f"✅ Loaded {len(data)} yarn demand records")
        return data
    
    def _load_sales_orders(self) -> List[SalesOrder]:
        """Load eFab_SO_List.csv"""
        file_path = self.data_path / "eFab_SO_List.csv"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        df = pd.read_csv(file_path)
        data = [SalesOrder.from_csv_row(row) for _, row in df.iterrows()]
        logger.info(f"✅ Loaded {len(data)} sales orders")
        return data
    
    def _load_style_bom(self) -> List[StyleBOM]:
        """Load Style_BOM.csv"""
        file_path = self.data_path / "Style_BOM.csv"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        df = pd.read_csv(file_path)
        data = [StyleBOM.from_csv_row(row) for _, row in df.iterrows()]
        logger.info(f"✅ Loaded {len(data)} BOM records")
        return data
    
    def _load_inventory(self) -> List[InventoryItem]:
        """Load Inventory.csv"""
        file_path = self.data_path / "Inventory.csv"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        df = pd.read_csv(file_path)
        data = [InventoryItem.from_csv_row(row) for _, row in df.iterrows()]
        logger.info(f"✅ Loaded {len(data)} inventory records")
        return data
    
    def _load_suppliers(self) -> List[SupplierInfo]:
        """Load Supplier_ID.csv"""
        file_path = self.data_path / "Supplier_ID.csv"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        df = pd.read_csv(file_path)
        data = [SupplierInfo.from_csv_row(row) for _, row in df.iterrows()]
        # Filter out inactive suppliers
        active_data = [s for s in data if s.is_active()]
        logger.info(f"✅ Loaded {len(active_data)} active suppliers ({len(data)} total)")
        return active_data
    
    def _load_yarn_master(self) -> List[YarnMaster]:
        """Load Yarn_ID.csv"""
        file_path = self.data_path / "Yarn_ID.csv"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        df = pd.read_csv(file_path)
        data = [YarnMaster.from_csv_row(row) for _, row in df.iterrows()]
        logger.info(f"✅ Loaded {len(data)} yarn master records")
        return data
    
    def _validate_all_data(self):
        """Validate all loaded data"""
        logger.info("Validating live data quality...")
        
        # Individual file validations
        if self.live_data.get('yarn_demand_by_style'):
            yarn_demand_df = pd.read_csv(self.data_path / "cfab_Yarn_Demand_By_Style.csv")
            self.validation_results['yarn_demand'] = LiveDataValidator.validate_yarn_demand_by_style(yarn_demand_df)
        
        if self.live_data.get('style_bom'):
            style_bom_df = pd.read_csv(self.data_path / "Style_BOM.csv")
            self.validation_results['style_bom'] = LiveDataValidator.validate_style_bom(style_bom_df)
        
        if self.live_data.get('sales_orders'):
            sales_orders_df = pd.read_csv(self.data_path / "eFab_SO_List.csv")
            self.validation_results['sales_orders'] = LiveDataValidator.validate_sales_orders(sales_orders_df)
        
        # Cross-validation between BOM files
        if self.live_data.get('yarn_demand_by_style') and self.live_data.get('style_bom'):
            yarn_demand_df = pd.read_csv(self.data_path / "cfab_Yarn_Demand_By_Style.csv")
            style_bom_df = pd.read_csv(self.data_path / "Style_BOM.csv")
            self.validation_results['cross_validation'] = LiveDataValidator.cross_validate_bom_files(
                yarn_demand_df, style_bom_df
            )
        
        # Log validation results
        for validation_type, results in self.validation_results.items():
            if results.get('issues'):
                logger.warning(f"Data quality issues in {validation_type}: {results['issues']}")
            else:
                logger.info(f"✅ {validation_type} validation passed")
    
    def convert_to_planning_format(self) -> Dict[str, List]:
        """Convert live data to standard planning system format"""
        logger.info("Converting live data to planning format...")
        
        # Load live data if not already loaded
        if not self.live_data:
            self.load_all_live_data()
        
        # Convert to planning format
        planning_data = {
            'forecasts': self._convert_to_forecasts(),
            'boms': self._convert_to_boms(),
            'inventory': self._convert_to_inventory(),
            'suppliers': self._convert_to_suppliers()
        }
        
        self.processed_data = planning_data
        logger.info("✅ Live data conversion complete")
        return planning_data
    
    def _convert_to_forecasts(self) -> List[FinishedGoodsForecast]:
        """Convert sales orders to forecasts"""
        forecasts = []
        
        # Convert sales orders to forecasts
        for order in self.live_data.get('sales_orders', []):
            if order.ordered > 0 and not order.is_on_hold():
                forecast = FinishedGoodsForecast(
                    sku_id=order.cf_version,
                    forecast_qty=order.ordered,
                    forecast_date=datetime.now().date() + timedelta(days=14),  # Default lead time
                    source="sales_order",
                    unit=order.uom,
                    confidence=1.0,
                    notes=f"From SO {order.sop}"
                )
                forecasts.append(forecast)
        
        logger.info(f"✅ Generated {len(forecasts)} forecasts from sales orders")
        return forecasts
    
    def _convert_to_boms(self) -> List[BillOfMaterials]:
        """Convert Style_BOM.csv to BOM format"""
        boms = []
        
        for style_bom in self.live_data.get('style_bom', []):
            bom = BillOfMaterials(
                sku_id=style_bom.style_id,
                material_id=style_bom.yarn_id,
                qty_per_unit=style_bom.bom_percentage,  # Keep as 0-1 scale
                unit="percentage",
                percentage=style_bom.bom_percentage * 100  # Convert to 0-100 scale
            )
            boms.append(bom)
        
        logger.info(f"✅ Generated {len(boms)} BOM entries")
        return boms
    
    def _convert_to_inventory(self) -> List[Inventory]:
        """Convert inventory and yarn master data to inventory format"""
        inventory_list = []
        
        # Create inventory from yarn master data
        for yarn in self.live_data.get('yarn_master', []):
            inventory = Inventory(
                material_id=yarn.yarn_id,
                on_hand_qty=max(0, yarn.planning_balance),  # Use positive planning balance
                unit="lbs",
                open_po_qty=yarn.on_order,
                po_expected_date=datetime.now().date() + timedelta(days=14),  # Default
                cost_per_unit=yarn.get_cost_per_pound(),
                location="Main"
            )
            inventory_list.append(inventory)
        
        logger.info(f"✅ Generated {len(inventory_list)} inventory records")
        return inventory_list
    
    def _convert_to_suppliers(self) -> List[Supplier]:
        """Convert supplier and yarn data to supplier format"""
        suppliers = []
        
        # Create supplier lookup from SupplierInfo
        supplier_lookup = {s.supplier: s for s in self.live_data.get('suppliers', [])}
        
        # Create supplier records for each yarn-supplier combination
        for yarn in self.live_data.get('yarn_master', []):
            supplier_info = supplier_lookup.get(yarn.supplier)
            if supplier_info and yarn.get_cost_per_pound() > 0:
                supplier = Supplier(
                    material_id=yarn.yarn_id,
                    supplier_id=f"{supplier_info.supplier_id}_{yarn.yarn_id}",
                    cost_per_unit=yarn.get_cost_per_pound(),
                    lead_time_days=supplier_info.get_lead_time_days(),
                    moq=1000,  # Default MOQ, can be updated with actual data
                    reliability_score=0.95,  # Default reliability
                    ordering_cost=100.0,  # Default ordering cost
                    holding_cost_rate=0.25,  # Default holding cost
                    supplier_name=supplier_info.supplier,
                    supplier_type=supplier_info.type
                )
                suppliers.append(supplier)
        
        logger.info(f"✅ Generated {len(suppliers)} supplier records")
        return suppliers
    
    def generate_planning_inputs(self) -> Dict[str, Any]:
        """Generate complete planning inputs from live data"""
        logger.info("Generating planning inputs from live data...")
        
        # Convert to planning format
        planning_data = self.convert_to_planning_format()
        
        # Add enhanced forecasts from yarn demand data
        enhanced_forecasts = self._generate_enhanced_forecasts()
        planning_data['forecasts'].extend(enhanced_forecasts)
        
        # Generate summary statistics
        summary = self._generate_summary_statistics()
        
        result = {
            'planning_data': planning_data,
            'summary': summary,
            'validation_results': self.validation_results,
            'data_quality_report': self._generate_data_quality_report()
        }
        
        logger.info("✅ Planning inputs generation complete")
        return result
    
    def _generate_enhanced_forecasts(self) -> List[FinishedGoodsForecast]:
        """Generate additional forecasts from yarn demand data"""
        forecasts = []
        
        # Group yarn demand by style and sum totals
        style_demands = {}
        for demand in self.live_data.get('yarn_demand_by_style', []):
            if demand.style not in style_demands:
                style_demands[demand.style] = 0
            style_demands[demand.style] += demand.total
        
        # Convert to forecasts
        for style, total_demand in style_demands.items():
            if total_demand > 0:
                forecast = FinishedGoodsForecast(
                    sku_id=style,
                    forecast_qty=int(total_demand),
                    forecast_date=datetime.now().date() + timedelta(days=7),
                    source="yarn_demand",
                    unit="yards",
                    confidence=0.8,
                    notes="Generated from yarn demand data"
                )
                forecasts.append(forecast)
        
        logger.info(f"✅ Generated {len(forecasts)} enhanced forecasts from yarn demand")
        return forecasts
    
    def _generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics for the loaded data"""
        return {
            'data_files_loaded': len([k for k, v in self.live_data.items() if v]),
            'total_records': {
                'yarn_demand': len(self.live_data.get('yarn_demand_by_style', [])),
                'sales_orders': len(self.live_data.get('sales_orders', [])),
                'style_bom': len(self.live_data.get('style_bom', [])),
                'inventory': len(self.live_data.get('inventory', [])),
                'suppliers': len(self.live_data.get('suppliers', [])),
                'yarn_master': len(self.live_data.get('yarn_master', []))
            },
            'unique_counts': {
                'styles': len(set(item.style for item in self.live_data.get('yarn_demand_by_style', []))),
                'yarns': len(set(item.yarn_id for item in self.live_data.get('yarn_master', []))),
                'suppliers': len(set(item.supplier for item in self.live_data.get('suppliers', []))),
                'sales_orders': len(set(item.sop for item in self.live_data.get('sales_orders', [])))
            },
            'validation_status': {
                validation_type: len(results.get('issues', [])) == 0 
                for validation_type, results in self.validation_results.items()
            }
        }
    
    def _generate_data_quality_report(self) -> str:
        """Generate a comprehensive data quality report"""
        report_lines = [
            "Beverly Knits Live Data Quality Report",
            "=" * 40,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Summary statistics
        summary = self._generate_summary_statistics()
        report_lines.extend([
            "DATA LOADING SUMMARY:",
            f"Files loaded: {summary['data_files_loaded']}/6",
            ""
        ])
        
        for data_type, count in summary['total_records'].items():
            report_lines.append(f"{data_type}: {count} records")
        
        report_lines.append("")
        
        # Validation results
        report_lines.append("VALIDATION RESULTS:")
        for validation_type, results in self.validation_results.items():
            if results.get('issues'):
                report_lines.append(f"❌ {validation_type}: {len(results['issues'])} issues")
                for issue in results['issues']:
                    report_lines.append(f"   - {issue}")
            else:
                report_lines.append(f"✅ {validation_type}: No issues")
        
        report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "RECOMMENDATIONS:",
            "1. Review and resolve any validation issues above",
            "2. Verify BOM percentage totals for flagged styles",
            "3. Ensure all cost data is available and accurate",
            "4. Check for missing supplier information",
            "5. Validate forecast quantities against business expectations"
        ])
        
        return "\n".join(report_lines)
    
    def export_processed_data(self, output_path: str = "output/"):
        """Export processed data to CSV files"""
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        if not self.processed_data:
            self.convert_to_planning_format()
        
        # Export to CSV files
        for data_type, data_list in self.processed_data.items():
            if data_list:
                # Convert to DataFrame
                if data_type == 'forecasts':
                    df = pd.DataFrame([
                        {
                            'sku_id': f.sku_id,
                            'forecast_qty': f.forecast_qty,
                            'forecast_date': f.forecast_date,
                            'source': f.source,
                            'unit': f.unit,
                            'confidence': f.confidence,
                            'notes': f.notes
                        }
                        for f in data_list
                    ])
                elif data_type == 'boms':
                    df = pd.DataFrame([
                        {
                            'sku_id': b.sku_id,
                            'material_id': b.material_id,
                            'qty_per_unit': b.qty_per_unit,
                            'unit': b.unit,
                            'percentage': b.percentage
                        }
                        for b in data_list
                    ])
                elif data_type == 'inventory':
                    df = pd.DataFrame([
                        {
                            'material_id': i.material_id,
                            'on_hand_qty': i.on_hand_qty,
                            'unit': i.unit,
                            'open_po_qty': i.open_po_qty,
                            'po_expected_date': i.po_expected_date,
                            'cost_per_unit': i.cost_per_unit,
                            'location': i.location
                        }
                        for i in data_list
                    ])
                elif data_type == 'suppliers':
                    df = pd.DataFrame([
                        {
                            'material_id': s.material_id,
                            'supplier_id': s.supplier_id,
                            'cost_per_unit': s.cost_per_unit,
                            'lead_time_days': s.lead_time_days,
                            'moq': s.moq,
                            'reliability_score': s.reliability_score,
                            'ordering_cost': s.ordering_cost,
                            'holding_cost_rate': s.holding_cost_rate,
                            'supplier_name': s.supplier_name,
                            'supplier_type': s.supplier_type
                        }
                        for s in data_list
                    ])
                
                # Save to CSV
                output_file = output_dir / f"live_data_{data_type}.csv"
                df.to_csv(output_file, index=False)
                logger.info(f"✅ Exported {len(df)} {data_type} records to {output_file}")
        
        # Export data quality report
        report_file = output_dir / "live_data_quality_report.txt"
        with open(report_file, 'w') as f:
            f.write(self._generate_data_quality_report())
        logger.info(f"✅ Exported data quality report to {report_file}")


def main():
    """Main function for testing the live data integrator"""
    integrator = LiveDataIntegrator()
    
    # Load and process all live data
    live_data = integrator.load_all_live_data()
    
    # Generate planning inputs
    planning_inputs = integrator.generate_planning_inputs()
    
    # Export processed data
    integrator.export_processed_data()
    
    print("\nLive Data Integration Summary:")
    print(f"Files loaded: {len([k for k, v in live_data.items() if v])}/6")
    print(f"Total forecasts: {len(planning_inputs['planning_data']['forecasts'])}")
    print(f"Total BOMs: {len(planning_inputs['planning_data']['boms'])}")
    print(f"Total inventory records: {len(planning_inputs['planning_data']['inventory'])}")
    print(f"Total suppliers: {len(planning_inputs['planning_data']['suppliers'])}")
    
    return planning_inputs


if __name__ == "__main__":
    main()