"""
Sample data generator for Beverly Knits Raw Material Planner
"""

import random
from utils.logger import get_logger

logger = get_logger(__name__)
from datetime import datetime, timedelta
from typing import Dict

import pandas as pd


class SampleDataGenerator:
    """Generate realistic sample data for testing the planner"""
    
    @staticmethod
    def generate_forecast_data(num_skus: int = 10) -> pd.DataFrame:
        """Generate sample finished goods forecast data"""
        
        skus = [f"SKU-{i:03d}" for i in range(1, num_skus + 1)]
        sources = ["sales_order", "prod_plan", "projection"]
        
        data = []
        base_date = datetime.now().date()
        
        for sku in skus:
            # Generate multiple forecast entries per SKU from different sources
            for source in sources:
                if random.random() > 0.3:  # 70% chance of having this source
                    forecast_qty = random.randint(100, 2000)
                    forecast_date = base_date + timedelta(days=random.randint(1, 30))
                    
                    data.append({
                        'sku_id': sku,
                        'forecast_qty': forecast_qty,
                        'forecast_date': forecast_date,
                        'source': source
                    })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_bom_data(num_skus: int = 10) -> pd.DataFrame:
        """Generate sample BOM data"""
        
        skus = [f"SKU-{i:03d}" for i in range(1, num_skus + 1)]
        
        # Material types and their typical units
        materials = {
            'YARN-COTTON': 'lb',
            'YARN-WOOL': 'lb', 
            'YARN-POLYESTER': 'lb',
            'FABRIC-DENIM': 'yd',
            'FABRIC-COTTON': 'yd',
            'FABRIC-SILK': 'yd',
            'BUTTON-PLASTIC': 'pcs',
            'BUTTON-METAL': 'pcs',
            'ZIPPER-YKK': 'pcs',
            'THREAD-COTTON': 'lb',
            'THREAD-POLYESTER': 'lb'
        }
        
        data = []
        
        for sku in skus:
            # Each SKU uses 3-6 different materials
            num_materials = random.randint(3, 6)
            sku_materials = random.sample(list(materials.keys()), num_materials)
            
            for material_id in sku_materials:
                unit = materials[material_id]
                
                # Generate realistic quantities based on material type
                if 'YARN' in material_id or 'THREAD' in material_id:
                    qty_per_unit = round(random.uniform(0.5, 3.0), 2)
                elif 'FABRIC' in material_id:
                    qty_per_unit = round(random.uniform(1.0, 5.0), 2)
                else:  # Buttons, zippers, etc.
                    qty_per_unit = random.randint(1, 12)
                
                data.append({
                    'sku_id': sku,
                    'material_id': material_id,
                    'qty_per_unit': qty_per_unit,
                    'unit': unit
                })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_inventory_data() -> pd.DataFrame:
        """Generate sample inventory data"""
        
        materials = [
            'YARN-COTTON', 'YARN-WOOL', 'YARN-POLYESTER',
            'FABRIC-DENIM', 'FABRIC-COTTON', 'FABRIC-SILK',
            'BUTTON-PLASTIC', 'BUTTON-METAL', 'ZIPPER-YKK',
            'THREAD-COTTON', 'THREAD-POLYESTER'
        ]
        
        units = {
            'YARN-COTTON': 'lb', 'YARN-WOOL': 'lb', 'YARN-POLYESTER': 'lb',
            'FABRIC-DENIM': 'yd', 'FABRIC-COTTON': 'yd', 'FABRIC-SILK': 'yd',
            'BUTTON-PLASTIC': 'pcs', 'BUTTON-METAL': 'pcs', 'ZIPPER-YKK': 'pcs',
            'THREAD-COTTON': 'lb', 'THREAD-POLYESTER': 'lb'
        }
        
        data = []
        base_date = datetime.now().date()
        
        for material_id in materials:
            unit = units[material_id]
            
            # Generate realistic inventory levels
            if 'YARN' in material_id or 'FABRIC' in material_id:
                on_hand_qty = random.randint(0, 1000)
                open_po_qty = random.randint(0, 500) if random.random() > 0.4 else 0
            else:  # Small parts
                on_hand_qty = random.randint(0, 5000)
                open_po_qty = random.randint(0, 2000) if random.random() > 0.4 else 0
            
            po_expected_date = None
            if open_po_qty > 0:
                po_expected_date = base_date + timedelta(days=random.randint(5, 25))
            
            data.append({
                'material_id': material_id,
                'on_hand_qty': on_hand_qty,
                'unit': unit,
                'open_po_qty': open_po_qty,
                'po_expected_date': po_expected_date
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_supplier_data() -> pd.DataFrame:
        """Generate sample supplier data"""
        
        materials = [
            'YARN-COTTON', 'YARN-WOOL', 'YARN-POLYESTER',
            'FABRIC-DENIM', 'FABRIC-COTTON', 'FABRIC-SILK',
            'BUTTON-PLASTIC', 'BUTTON-METAL', 'ZIPPER-YKK',
            'THREAD-COTTON', 'THREAD-POLYESTER'
        ]
        
        # Supplier names by category
        yarn_suppliers = ['YarnCorp', 'FiberTech', 'CottonMills']
        fabric_suppliers = ['TextilePro', 'FabricWorld', 'WeaveMaster']
        accessory_suppliers = ['ButtonCo', 'ZipperInc', 'AccessoryPlus']
        
        data = []
        
        for material_id in materials:
            # Each material has 2-3 suppliers
            if 'YARN' in material_id or 'THREAD' in material_id:
                suppliers = random.sample(yarn_suppliers, random.randint(2, 3))
            elif 'FABRIC' in material_id:
                suppliers = random.sample(fabric_suppliers, random.randint(2, 3))
            else:
                suppliers = random.sample(accessory_suppliers, random.randint(2, 3))
            
            for supplier_id in suppliers:
                # Generate realistic pricing and terms
                if 'YARN' in material_id or 'THREAD' in material_id:
                    cost_per_unit = round(random.uniform(2.0, 8.0), 2)
                    moq = random.choice([100, 250, 500])
                elif 'FABRIC' in material_id:
                    cost_per_unit = round(random.uniform(5.0, 25.0), 2)
                    moq = random.choice([50, 100, 200])
                else:  # Accessories
                    cost_per_unit = round(random.uniform(0.10, 2.0), 2)
                    moq = random.choice([500, 1000, 2000])
                
                lead_time_days = random.randint(7, 30)
                reliability_score = round(random.uniform(0.7, 1.0), 2)
                
                # Some suppliers have contract limits
                contract_qty_limit = None
                if random.random() > 0.6:  # 40% have limits
                    contract_qty_limit = moq * random.randint(10, 50)
                
                data.append({
                    'material_id': material_id,
                    'supplier_id': supplier_id,
                    'cost_per_unit': cost_per_unit,
                    'lead_time_days': lead_time_days,
                    'moq': moq,
                    'contract_qty_limit': contract_qty_limit,
                    'reliability_score': reliability_score,
                    # EOQ-related fields
                    'ordering_cost': round(random.uniform(50.0, 200.0), 2),  # Cost per order
                    'holding_cost_rate': round(random.uniform(0.15, 0.25), 3)  # Annual holding cost rate
                })

        return pd.DataFrame(data)
    
    @staticmethod
    def generate_all_sample_data(num_skus: int = 10) -> Dict[str, pd.DataFrame]:
        """Generate complete set of sample data"""
        
        return {
            'forecasts': SampleDataGenerator.generate_forecast_data(num_skus),
            'boms': SampleDataGenerator.generate_bom_data(num_skus),
            'inventory': SampleDataGenerator.generate_inventory_data(),
            'suppliers': SampleDataGenerator.generate_supplier_data()
        }
    
    @staticmethod
    def save_sample_data_to_csv(output_dir: str = "data", num_skus: int = 10):
        """Generate and save sample data to CSV files"""
        import os

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate data
        sample_data = SampleDataGenerator.generate_all_sample_data(num_skus)
        
        # Save to CSV files
        for data_type, df in sample_data.items():
            filename = os.path.join(output_dir, f"sample_{data_type}.csv")
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(df)} records to {filename}")
        
        return sample_data


# Generate sample data when this module is run directly
if __name__ == "__main__":
    logger.info("Generating sample data for Beverly Knits Raw Material Planner...")
    sample_data = SampleDataGenerator.save_sample_data_to_csv()
    
    logger.info("\nSample data summary:")
    for data_type, df in sample_data.items():
        logger.info(f"  {data_type}: {len(df)} records")
    
    logger.info("\nSample data files created in 'data/' directory")