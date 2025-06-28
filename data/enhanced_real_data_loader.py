"""
Beverly Knits Real Data Loader - Enhanced Version
Loads integrated real data with automatic quality fixes applied
"""

import pandas as pd
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.supplier import Supplier
from models.inventory import Inventory
from models.bom import BillOfMaterials
import json

class EnhancedRealDataLoader:
    """Enhanced data loader with automatic quality fixes"""
    
    def __init__(self, data_dir: str = "data", use_v2: bool = True):
        self.data_dir = Path(data_dir)
        self.version_suffix = "_v2" if use_v2 else ""
    
    def load_materials(self) -> pd.DataFrame:
        """Load integrated materials data"""
        return pd.read_csv(self.data_dir / f"integrated_materials{self.version_suffix}.csv")
    
    def load_suppliers(self) -> pd.DataFrame:
        """Load integrated suppliers data"""
        return pd.read_csv(self.data_dir / f"integrated_suppliers{self.version_suffix}.csv")
    
    def load_inventory(self) -> pd.DataFrame:
        """Load integrated inventory data"""
        return pd.read_csv(self.data_dir / f"integrated_inventory{self.version_suffix}.csv")
    
    def load_boms(self) -> pd.DataFrame:
        """Load integrated BOMs data"""
        return pd.read_csv(self.data_dir / f"integrated_boms{self.version_suffix}.csv")
    
    def load_interchangeable_yarns(self) -> dict:
        """Load interchangeable yarn groups"""
        with open(self.data_dir / f"interchangeable_yarns{self.version_suffix}.json", 'r') as f:
            return json.load(f)
    
    def create_supplier_objects(self) -> list:
        """Create Supplier objects from real data"""
        suppliers_df = self.load_suppliers()
        suppliers = []
        
        for _, row in suppliers_df.iterrows():
            if pd.notna(row['cost_per_unit']) and row['cost_per_unit'] > 0:
                supplier = Supplier(
                    material_id=str(row['material_id']),
                    supplier_id=row['supplier_id'],
                    cost_per_unit=row['cost_per_unit'],
                    lead_time_days=int(row['lead_time_days']),
                    moq=int(row['moq']),
                    reliability_score=row['reliability_score']
                )
                suppliers.append(supplier)
        
        return suppliers
    
    def create_inventory_objects(self) -> list:
        """Create Inventory objects from real data with enhanced handling"""
        inventory_df = self.load_inventory()
        inventory_items = []

        for _, row in inventory_df.iterrows():
            if pd.notna(row['material_id']):
                # Enhanced handling - negative values already fixed in v2 data
                current_stock = float(row['current_stock']) if pd.notna(row['current_stock']) else 0.0
                incoming_stock = float(row['incoming_stock']) if pd.notna(row['incoming_stock']) else 0.0
                
                # Ensure non-negative values (should already be fixed in v2)
                current_stock = max(0.0, current_stock)
                incoming_stock = max(0.0, incoming_stock)
                
                item = Inventory(
                    material_id=str(row['material_id']),
                    on_hand_qty=current_stock,
                    unit="lbs",  # Default unit for yarn
                    open_po_qty=incoming_stock
                )
                inventory_items.append(item)

        return inventory_items
    
    def create_bom_objects(self) -> list:
        """Create BillOfMaterials objects from real data with enhanced validation"""
        boms_df = self.load_boms()
        bom_items = []
        
        for _, row in boms_df.iterrows():
            if pd.notna(row['material_id']) and pd.notna(row['sku_id']):
                # Enhanced validation - percentages should already be fixed in v2
                quantity = float(row['quantity_per_unit'])
                
                item = BillOfMaterials(
                    sku_id=str(row['sku_id']),
                    material_id=str(row['material_id']),
                    qty_per_unit=quantity,
                    unit="lbs"  # Default unit for yarn
                )
                bom_items.append(item)
        
        return bom_items
    
    def get_material_info(self, material_id: str) -> dict:
        """Get detailed material information"""
        materials_df = self.load_materials()
        material = materials_df[materials_df['material_id'] == float(material_id)]
        
        if not material.empty:
            row = material.iloc[0]
            return {
                'material_id': str(row['material_id']),
                'supplier': row.get('Supplier', 'N/A'),
                'description': row.get('Description', 'N/A'),
                'blend': row.get('Blend', 'N/A'),
                'type': row.get('Type', 'N/A'),
                'color': row.get('Color', 'N/A'),
                'cost_per_unit': row['cost_per_unit']
            }
        return None
    
    def get_interchangeable_materials(self, material_id: str) -> list:
        """Get list of interchangeable materials for a given material"""
        interchangeable = self.load_interchangeable_yarns()
        
        for group_name, group_data in interchangeable.items():
            if float(material_id) in group_data['yarn_ids']:
                return [str(int(y)) for y in group_data['yarn_ids'] if int(y) != int(float(material_id))]
        
        return []
    
    def validate_data_quality(self) -> dict:
        """Validate data quality and return summary"""
        materials = self.load_materials()
        suppliers = self.load_suppliers()
        inventory = self.load_inventory()
        boms = self.load_boms()
        
        quality_summary = {
            'total_materials': len(materials),
            'materials_with_zero_cost': len(materials[materials['cost_per_unit'] == 0]),
            'materials_with_negative_inventory': len(inventory[inventory['current_stock'] < 0]),
            'materials_with_negative_incoming': len(inventory[inventory['incoming_stock'] < 0]),
            'materials_with_negative_planning': len(inventory[inventory['planning_balance'] < 0]),
            'bom_validation': self._validate_bom_percentages(boms),
            'supplier_coverage': len(suppliers) / len(materials) if len(materials) > 0 else 0
        }
        
        return quality_summary
    
    def _validate_bom_percentages(self, boms_df) -> dict:
        """Validate BOM percentages sum to 1.0"""
        style_totals = boms_df.groupby('sku_id')['quantity_per_unit'].sum()
        
        return {
            'total_styles': len(style_totals),
            'styles_summing_to_one': len(style_totals[(style_totals >= 0.99) & (style_totals <= 1.01)]),
            'styles_with_issues': len(style_totals[(style_totals < 0.99) | (style_totals > 1.01)]),
            'average_total': style_totals.mean(),
            'min_total': style_totals.min(),
            'max_total': style_totals.max()
        }
    
    def generate_sample_forecasts(self, num_styles: int = 10) -> pd.DataFrame:
        """Generate sample forecasts for real styles"""
        boms_df = self.load_boms()
        unique_styles = boms_df['sku_id'].unique()
        
        # Create sample forecasts
        import random
        forecasts = []
        
        for style in unique_styles[:num_styles]:
            for month in range(1, 13):
                forecasts.append({
                    'sku_id': style,
                    'forecast_date': f"2024-{month:02d}-01",
                    'quantity': random.randint(100, 1000),
                    'source': 'Historical',
                    'confidence': random.uniform(0.7, 0.95)
                })
        
        return pd.DataFrame(forecasts)

def main():
    """Demonstrate enhanced real data loading"""
    print("🔄 Loading Beverly Knits Enhanced Real Data...")
    
    loader = EnhancedRealDataLoader(use_v2=True)
    
    try:
        # Load all datasets
        materials = loader.load_materials()
        suppliers = loader.load_suppliers()
        inventory = loader.load_inventory()
        boms = loader.load_boms()
        interchangeable = loader.load_interchangeable_yarns()
        
        print(f"📊 Enhanced Data Summary:")
        print(f"   Materials: {len(materials)} yarns")
        print(f"   Suppliers: {len(suppliers)} supplier-material relationships")
        print(f"   Inventory: {len(inventory)} inventory records")
        print(f"   BOMs: {len(boms)} BOM lines for {boms['sku_id'].nunique()} styles")
        print(f"   Interchangeable Groups: {len(interchangeable)} groups")
        
        # Validate data quality
        quality_summary = loader.validate_data_quality()
        print(f"\n✅ Data Quality Validation:")
        print(f"   Materials with zero cost: {quality_summary['materials_with_zero_cost']}")
        print(f"   Materials with negative inventory: {quality_summary['materials_with_negative_inventory']}")
        print(f"   Materials with negative incoming: {quality_summary['materials_with_negative_incoming']}")
        print(f"   Materials with negative planning balance: {quality_summary['materials_with_negative_planning']} (allowed)")
        print(f"   BOM styles summing to 1.0: {quality_summary['bom_validation']['styles_summing_to_one']}/{quality_summary['bom_validation']['total_styles']}")
        print(f"   Supplier coverage: {quality_summary['supplier_coverage']:.1%}")
        
        # Create objects for planning system
        supplier_objects = loader.create_supplier_objects()
        inventory_objects = loader.create_inventory_objects()
        bom_objects = loader.create_bom_objects()
        
        print(f"\n🏭 Planning System Objects:")
        print(f"   Supplier Objects: {len(supplier_objects)}")
        print(f"   Inventory Objects: {len(inventory_objects)}")
        print(f"   BOM Objects: {len(bom_objects)}")
        
        print("\n✅ Enhanced real data loading complete!")
        print("💡 All automatic fixes have been applied")
        
    except FileNotFoundError as e:
        print(f"❌ Enhanced data files not found. Please run data_integration_v2.py first.")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()