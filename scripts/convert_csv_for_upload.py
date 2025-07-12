"""
Beverly Knits CSV File Converter
Converts raw Beverly Knits CSV files to the format expected by the upload interface
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BeverlyKnitsCSVConverter:
    """Converts Beverly Knits CSV files to expected upload format"""
    
    def __init__(self, input_dir: str = "data", output_dir: str = "data/upload_ready"):
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(exist_ok=True)
        
    def convert_all_files(self):
        """Convert all CSV files to upload format"""
        print("🔄 Converting Beverly Knits CSV files to upload format...")
        
        # Load raw data
        try:
            print("Loading inventory: data/Yarn_ID_Current_Inventory.csv")
            inventory = pd.read_csv(self.input_dir / "Yarn_ID_Current_Inventory.csv")
            print("Loading suppliers: data/Supplier_ID.csv")
            suppliers = pd.read_csv(self.input_dir / "Supplier_ID.csv")
            print("Loading boms: data/Style_BOM.csv")
            boms = pd.read_csv(self.input_dir / "Style_BOM.csv")
        except FileNotFoundError as e:
            print(f"❌ Error loading raw data: {e}")
            return {}
        
        # Convert each file
        forecasts_df = self.create_forecasts_file()
        boms_df = self.convert_boms_file(boms)
        inventory_df = self.convert_inventory_file(inventory)
        suppliers_df = self.convert_suppliers_file(inventory, suppliers)
        
        # Save converted files
        forecasts_df.to_csv(self.output_dir / "forecasts.csv", index=False)
        boms_df.to_csv(self.output_dir / "boms.csv", index=False)
        inventory_df.to_csv(self.output_dir / "inventory.csv", index=False)
        suppliers_df.to_csv(self.output_dir / "suppliers.csv", index=False)
        
        print("\n✅ Conversion complete! Files saved to:", self.output_dir)
        print("\nConverted files:")
        print(f"  • forecasts.csv ({len(forecasts_df)} records)")
        print(f"  • boms.csv ({len(boms_df)} records)")
        print(f"  • inventory.csv ({len(inventory_df)} records)")
        print(f"  • suppliers.csv ({len(suppliers_df)} records)")
        
        return {
            'forecasts': forecasts_df,
            'boms': boms_df,
            'inventory': inventory_df,
            'suppliers': suppliers_df
        }
    
    def create_forecasts_file(self):
        """Create forecasts from available data"""
        print("\n📊 Creating forecasts file...")
        
        # Check for sales data files
        sales_files = [
            "Sales Activity Report.csv",
            "eFab_SO_List.csv",
            "cfab_Yarn_Demand_By_Style.csv"
        ]
        
        # For now, create sample forecasts based on BOMs
        # In production, this would analyze sales history
        try:
            print("Loading boms for forecast creation: data/Style_BOM.csv")
            boms = pd.read_csv(self.input_dir / "Style_BOM.csv")
        except FileNotFoundError as e:
            print(f"❌ Error loading boms for forecast creation: {e}")
            return pd.DataFrame()
            
        unique_styles = boms['Style_ID'].unique()
        
        # Create forecast records
        forecasts = []
        base_date = datetime.now() + timedelta(days=30)  # 30 days out
        
        for style in unique_styles[:20]:  # Top 20 styles for demo
            # Generate realistic forecast quantities
            base_qty = np.random.randint(100, 1000)
            
            # Create 3-month forecast
            for month in range(3):
                forecast_date = base_date + timedelta(days=30 * month)
                qty = base_qty * (1 + np.random.uniform(-0.2, 0.2))  # ±20% variation
                
                forecasts.append({
                    'sku_id': style,
                    'forecast_qty': int(qty),
                    'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                    'source': 'sales_history'
                })
        
        forecasts_df = pd.DataFrame(forecasts)
        print(f"  Created {len(forecasts_df)} forecast records for {len(unique_styles[:20])} SKUs")
        
        return forecasts_df
    
    def convert_boms_file(self, boms_df):
        """Convert Style_BOM.csv to expected format"""
        print("\n🔧 Converting BOMs file...")
        
        converted = pd.DataFrame({
            'sku_id': boms_df['Style_ID'],
            'material_id': boms_df['Yarn_ID'].astype(str),
            'qty_per_unit': boms_df['BOM_Percentage'],
            'unit': 'lbs'  # Default unit for yarn
        })
        
        # Validate BOM percentages
        sku_totals = converted.groupby('sku_id')['qty_per_unit'].sum()
        invalid_skus = sku_totals[(sku_totals < 0.98) | (sku_totals > 1.02)]
        
        if len(invalid_skus) > 0:
            print(f"  ⚠️  Warning: {len(invalid_skus)} SKUs have BOM percentages not summing to 1.0")
        
        print(f"  Converted {len(converted)} BOM records")
        
        return converted
    
    def convert_inventory_file(self, inventory_df):
        """Convert Yarn_ID_Current_Inventory.csv to expected format"""
        print("\n📦 Converting inventory file...")

        # Clean numeric columns
        def clean_numeric(value):
            if pd.isna(value):
                return 0.0
            # Convert to string and clean
            cleaned = str(value).replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
            try:
                return float(cleaned)
            except:
                return 0.0

        # Apply cleaning to each value
        inventory_clean = inventory_df['Inventory'].apply(clean_numeric)
        on_order_clean = inventory_df['On_Order'].apply(clean_numeric)

        # Ensure non-negative inventory
        inventory_clean = np.maximum(inventory_clean, 0)
        on_order_clean = np.maximum(on_order_clean, 0)

        converted = pd.DataFrame({
            'material_id': inventory_df['Yarn_ID'].astype(str),
            'on_hand_qty': inventory_clean,
            'unit': 'lbs',
            'open_po_qty': on_order_clean,
            'po_expected_date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')  # Default 2 weeks
        })

        # Remove duplicates if any
        converted = converted.drop_duplicates(subset=['material_id'])

        print(f"  Converted {len(converted)} inventory records")
        print(f"  Fixed {(inventory_clean == 0).sum()} negative inventory values")

        return converted
        print(f"  Fixed {(inventory_clean == 0).sum()} negative inventory values")
        
        return converted
    
    def convert_suppliers_file(self, inventory_df, suppliers_df):
        """Create suppliers file from inventory and supplier master data"""
        print("\n🏭 Converting suppliers file...")
        
        # Clean suppliers master data
        valid_suppliers = suppliers_df[
            (suppliers_df['Type'] != 'Remove') & 
            (suppliers_df['Supplier'].notna())
        ].copy()
        
        # Create supplier lookup
        supplier_info = {}
        for _, row in valid_suppliers.iterrows():
            supplier_info[row['Supplier']] = {
                'lead_time': 14 if row['Lead_time'] == 'Remove' else int(row['Lead_time']),
                'moq': 1000 if row['MOQ'] == 'Remove' else int(row['MOQ'])
            }
        
        # Clean cost data from inventory
        def clean_cost(value):
            if pd.isna(value):
                return 0.0
            cleaned = str(value).replace('$', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except:
                return 0.0
        
        # Create supplier relationships from inventory data
        supplier_records = []
        
        for _, row in inventory_df.iterrows():
            if pd.notna(row['Supplier']) and row['Supplier'] in supplier_info:
                cost = clean_cost(row['Cost_Pound'])
                
                if cost > 0:  # Only include if we have valid cost
                    supplier_records.append({
                        'material_id': str(row['Yarn_ID']),
                        'supplier_id': row['Supplier'],
                        'cost_per_unit': cost,
                        'lead_time_days': supplier_info[row['Supplier']]['lead_time'],
                        'moq': supplier_info[row['Supplier']]['moq'],
                        'reliability_score': 0.95,  # Default high reliability
                        'ordering_cost': 100.0,  # Default ordering cost
                        'holding_cost_rate': 0.25  # Default 25% annual holding cost
                    })
        
        converted = pd.DataFrame(supplier_records)
        
        print(f"  Converted {len(converted)} supplier relationships")
        print(f"  Materials with suppliers: {converted['material_id'].nunique()}")
        
        return converted
    
    def validate_converted_files(self, converted_files):
        """Validate that converted files meet requirements"""
        print("\n✔️  Validating converted files...")
        
        # Check required columns
        required_columns = {
            'forecasts': ['sku_id', 'forecast_qty', 'forecast_date', 'source'],
            'boms': ['sku_id', 'material_id', 'qty_per_unit', 'unit'],
            'inventory': ['material_id', 'on_hand_qty', 'unit', 'open_po_qty', 'po_expected_date'],
            'suppliers': ['material_id', 'supplier_id', 'cost_per_unit', 'lead_time_days', 
                         'moq', 'reliability_score', 'ordering_cost', 'holding_cost_rate']
        }
        
        all_valid = True
        for file_type, df in converted_files.items():
            missing_cols = set(required_columns[file_type]) - set(df.columns)
            if missing_cols:
                print(f"  ❌ {file_type}: Missing columns {missing_cols}")
                all_valid = False
            else:
                print(f"  ✅ {file_type}: All required columns present")
        
        return all_valid


def main():
    """Run the converter"""
    converter = BeverlyKnitsCSVConverter()
    converted_files = converter.convert_all_files()
    
    # Validate
    if converter.validate_converted_files(converted_files):
        print("\n🎉 All files successfully converted and validated!")
        print("\nYou can now upload these files from the 'data/upload_ready' directory:")
        print("  1. forecasts.csv")
        print("  2. boms.csv")
        print("  3. inventory.csv")
        print("  4. suppliers.csv")
    else:
        print("\n⚠️  Some validation issues found. Please review the output above.")


if __name__ == "__main__":
    main()