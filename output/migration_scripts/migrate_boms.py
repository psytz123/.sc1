
"""
BOM Migration Script
====================
Converts old BOM format to live data format
"""

import pandas as pd
from pathlib import Path

def migrate_boms(old_bom_file: str, output_file: str):
    """Convert old BOM format to Style_BOM.csv format"""
    
    # Load old format
    old_df = pd.read_csv(old_bom_file)
    
    # Expected old format columns: sku_id, material_id, qty_per_unit, unit
    # Convert to live format columns: Style_ID, Yarn_ID, BOM_Percentage
    
    new_df = pd.DataFrame({
        'Style_ID': old_df['sku_id'],
        'Yarn_ID': old_df['material_id'],
        'BOM_Percentage': old_df['qty_per_unit']  # Assuming already in 0-1 scale
    })
    
    # Save in live format
    new_df.to_csv(output_file, index=False)
    print(f"Migrated {len(new_df)} BOM records to {output_file}")

if __name__ == "__main__":
    migrate_boms("old_boms.csv", "Style_BOM.csv")
