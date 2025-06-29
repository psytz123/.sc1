"""
Beverly Knits Real Data Loader
Loads integrated real data into the planning system
"""

import os
from utils.logger import get_logger

logger = get_logger(__name__)
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

from models.bom import BillOfMaterials
from models.inventory import Inventory
from models.supplier import Supplier


class RealDataLoader:
    """Loads Beverly Knits real data into planning system format"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
    
    def load_materials(self) -> pd.DataFrame:
        """Load integrated materials data"""
        return pd.read_csv(self.data_dir / "integrated_materials.csv")
    
    def load_suppliers(self) -> pd.DataFrame:
        """Load integrated suppliers data"""
        return pd.read_csv(self.data_dir / "integrated_suppliers.csv")
    
    def load_inventory(self) -> pd.DataFrame:
        """Load integrated inventory data"""
        return pd.read_csv(self.data_dir / "integrated_inventory.csv")
    
    def load_boms(self) -> pd.DataFrame:
        """Load integrated BOMs data"""
        return pd.read_csv(self.data_dir / "integrated_boms.csv")
    
    def load_interchangeable_yarns(self) -> dict:
        """Load interchangeable yarn groups"""
        with open(self.data_dir / "interchangeable_yarns.json", 'r') as f:
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
        """Create Inventory objects from real data"""
        inventory_df = self.load_inventory()
        inventory_items = []

        for _, row in inventory_df.iterrows():
            if pd.notna(row['material_id']):
                # Handle negative inventory values by setting to 0
                current_stock = float(row['current_stock']) if pd.notna(row['current_stock']) else 0.0
                incoming_stock = float(row['incoming_stock']) if pd.notna(row['incoming_stock']) else 0.0

                # Ensure non-negative values
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
        """Create BillOfMaterials objects from real data"""
        boms_df = self.load_boms()
        bom_items = []

        for _, row in boms_df.iterrows():
            if pd.notna(row['material_id']) and pd.notna(row['sku_id']):
                item = BillOfMaterials(
                    sku_id=str(row['sku_id']),
                    material_id=str(row['material_id']),
                    qty_per_unit=float(row['quantity_per_unit']),
                    unit="lbs"  # Default unit for yarn
                )
                bom_items.append(item)

        return bom_items
        """Create BOMItem objects from real data"""
        boms_df = self.load_boms()
        bom_items = []
        
        for _, row in boms_df.iterrows():
            if pd.notna(row['material_id']) and pd.notna(row['sku_id']):
                item = BOMItem(
                    sku_id=str(row['sku_id']),
                    material_id=str(row['material_id']),
                    quantity_per_unit=float(row['quantity_per_unit'])
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
                'supplier': row['Supplier'],
                'description': row['Description'],
                'blend': row['Blend'],
                'type': row['Type'],
                'color': row['Color'],
                'cost_per_unit': row['cost_per_unit']
            }
        return None
    
    def get_interchangeable_materials(self, material_id: str) -> list:
        """Get list of interchangeable materials for a given material"""
        interchangeable = self.load_interchangeable_yarns()
        
        for group_name, group_data in interchangeable.items():
            if material_id in [str(y) for y in group_data['yarn_ids']]:
                return [str(y) for y in group_data['yarn_ids'] if str(y) != material_id]
        
        return []
    
    def generate_sample_forecasts(self) -> pd.DataFrame:
        """Generate sample forecasts for real styles"""
        boms_df = self.load_boms()
        unique_styles = boms_df['sku_id'].unique()
        
        # Create sample forecasts for first 10 styles
        import random
        forecasts = []
        
        for style in unique_styles[:10]:
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
    """Demonstrate real data loading"""
    logger.info("🔄 Loading Beverly Knits Real Data...")
    
    loader = RealDataLoader()
    
    # Load all datasets
    materials = loader.load_materials()
    suppliers = loader.load_suppliers()
    inventory = loader.load_inventory()
    boms = loader.load_boms()
    interchangeable = loader.load_interchangeable_yarns()
    
    logger.info(f"📊 Loaded Data Summary:")
    logger.info(f"   Materials: {len(materials)} yarns")
    logger.info(f"   Suppliers: {len(suppliers)} supplier-material relationships")
    logger.info(f"   Inventory: {len(inventory)} inventory records")
    logger.info(f"   BOMs: {len(boms)} BOM lines for {boms['sku_id'].nunique()} styles")
    logger.info(f"   Interchangeable Groups: {len(interchangeable)} groups")
    
    # Create objects for planning system
    supplier_objects = loader.create_supplier_objects()
    inventory_objects = loader.create_inventory_objects()
    bom_objects = loader.create_bom_objects()
    
    logger.info(f"\n🏭 Planning System Objects:")
    logger.info(f"   Supplier Objects: {len(supplier_objects)}")
    logger.info(f"   Inventory Objects: {len(inventory_objects)}")
    logger.info(f"   BOM Objects: {len(bom_objects)}")
    
    # Show sample material info
    sample_material = materials.iloc[0]['material_id']
    material_info = loader.get_material_info(str(sample_material))
    logger.info(f"\n📋 Sample Material Info (ID: {sample_material}):")
    for key, value in material_info.items():
        logger.info(f"   {key}: {value}")
    
    # Show interchangeable materials
    interchangeable_mats = loader.get_interchangeable_materials(str(sample_material))
    if interchangeable_mats:
        logger.info(f"   Interchangeable with: {interchangeable_mats}")
    
    # Generate sample forecasts
    sample_forecasts = loader.generate_sample_forecasts()
    sample_forecasts.to_csv('data/real_data_sample_forecasts.csv', index=False)
    logger.info(f"\n📈 Generated sample forecasts: {len(sample_forecasts)} records")
    
    logger.info("\n✅ Real data loading complete!")
    logger.info("💡 Use RealDataLoader class to integrate with planning system")

if __name__ == "__main__":
    main()