"""
Beverly Knits Data Integration Module
=====================================
This module provides comprehensive data integration for all CSV files
in the Beverly Knits raw material planning system, aligning with the
process outlined in DATA_INTEGRATION_GUIDE.md.
"""

import pandas as pd
import numpy as np
import os

class BeverlyKnitsDataIntegrator:
    """
    Integrates Beverly Knits data files based on the enhanced v2 process.
    Processes real data files with automatic quality fixes.
    """
    
    def __init__(self, data_path: str = "data/", output_path: str = "output/"):
        self.data_path = data_path
        self.output_path = output_path
        self.raw_data = {}
        self.processed_data = {}
        self.quality_report = []
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)

    def load_data(self):
        """Loads all required source CSV files."""
        print("Loading source data files...")
        files_to_load = {
            "yarn_master": "Yarn_ID_1.csv",
            "inventory": "Yarn_ID_Current_Inventory.csv",
            "suppliers": "Supplier_ID.csv",
            "boms": "Style_BOM.csv"
        }
        for key, filename in files_to_load.items():
            try:
                filepath = os.path.join(self.data_path, filename)
                self.raw_data[key] = pd.read_csv(filepath)
                print(f"✓ Loaded {filename}")
            except FileNotFoundError:
                print(f"✗ ERROR: {filename} not found in {self.data_path}")
                raise

    def _fix_negative_inventory(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converts negative inventory values to 0."""
        negative_mask = df['Inventory'] < 0
        count = negative_mask.sum()
        if count > 0:
            self.quality_report.append(f"Fixed {count} instances of negative inventory by converting to 0.")
            df.loc[negative_mask, 'Inventory'] = 0
        return df

    def _fix_bom_percentages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rounds BOM percentages > 0.99 to 1.0 for completeness."""
        rounding_mask = (df['Percentage'] > 0.99) & (df['Percentage'] < 1.0)
        count = rounding_mask.sum()
        if count > 0:
            self.quality_report.append(f"Rounded {count} BOM percentages > 0.99 to 1.0.")
            df.loc[rounding_mask, 'Percentage'] = 1.0
        return df

    def _clean_cost_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Removes '$' symbols and commas from cost data."""
        if 'Cost' in df.columns:
            original_dtype = df['Cost'].dtype
            if original_dtype == 'object':
                df['Cost'] = df['Cost'].astype(str).str.replace(r'[$,]', '', regex=True)
                df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce').fillna(0)
                self.quality_report.append("Cleaned cost data by removing '$' and commas.")
        return df

    def process_data(self):
        """Runs the full data processing and cleaning pipeline."""
        print("\nProcessing and cleaning data...")
        
        # Process Yarn Master
        yarn_master = self.raw_data['yarn_master'].copy()
        yarn_master = self._clean_cost_data(yarn_master)
        self.processed_data['materials'] = yarn_master
        print(f"✓ Processed {len(yarn_master)} materials.")

        # Process Inventory
        inventory = self.raw_data['inventory'].copy()
        inventory = self._fix_negative_inventory(inventory)
        self.processed_data['inventory'] = inventory
        print(f"✓ Processed {len(inventory)} inventory records.")

        # Process Suppliers
        suppliers = self.raw_data['suppliers'].copy()
        # Handle potential data type mismatches if necessary
        self.processed_data['suppliers'] = suppliers
        print(f"✓ Processed {len(suppliers)} supplier relationships.")

        # Process BOMs
        boms = self.raw_data['boms'].copy()
        boms = self._fix_bom_percentages(boms)
        # Ensure all materials in BOM sum to 100% for each style
        style_sums = boms.groupby('Style_ID')['Percentage'].sum()
        incomplete_boms = style_sums[~style_sums.between(0.99, 1.01)]
        if not incomplete_boms.empty:
            self.quality_report.append(f"Flagged {len(incomplete_boms)} SKUs with incomplete BOMs for review.")
        self.processed_data['boms'] = boms
        print(f"✓ Processed {len(boms)} BOM records.")

    def save_integrated_files(self):
        """Saves the processed dataframes to CSV files."""
        print("\nSaving integrated files...")
        output_files = {
            "integrated_materials_v2.csv": self.processed_data.get('materials'),
            "integrated_suppliers_v2.csv": self.processed_data.get('suppliers'),
            "integrated_inventory_v2.csv": self.processed_data.get('inventory'),
            "integrated_boms_v2.csv": self.processed_data.get('boms')
        }
        for filename, df in output_files.items():
            if df is not None:
                filepath = os.path.join(self.output_path, filename)
                df.to_csv(filepath, index=False)
                print(f"✓ Saved {filename}")

    def save_quality_report(self):
        """Saves the data quality report to a text file."""
        report_path = os.path.join(self.output_path, "data_quality_report_v2.txt")
        with open(report_path, 'w') as f:
            f.write("Data Quality and Automatic Fix Report\n")
            f.write("="*40 + "\n")
            for item in self.quality_report:
                f.write(f"- {item}\n")
        print(f"✓ Saved data quality report to {report_path}")

    def run_full_integration(self):
        """Executes the complete data integration process."""
        print("="*60)
        print("Beverly Knits Data Integration Process (v2)")
        print("="*60)
        
        try:
            self.load_data()
            self.process_data()
            self.save_integrated_files()
            self.save_quality_report()
            print("\n✓ Data integration completed successfully!")
        except Exception as e:
            print(f"\n✗ An error occurred during integration: {e}")

if __name__ == "__main__":
    # Initialize the integrator with specified data and output paths
    integrator = BeverlyKnitsDataIntegrator(data_path="data/", output_path="output/")
    
    # Run the full integration process
    integrator.run_full_integration()