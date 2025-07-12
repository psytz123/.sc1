
"""
Inventory Migration Script
==========================
Converts old inventory format to live data format
"""

import pandas as pd

def migrate_inventory(old_inventory_file: str, output_file: str):
    """Convert old inventory format to Inventory.csv format"""
    
    # Load old format
    old_df = pd.read_csv(old_inventory_file)
    
    # Expected old format: material_id, on_hand_qty, unit, open_po_qty, po_expected_date
    # Convert to live format: style_id, yds, lbs
    
    new_df = pd.DataFrame({
        'style_id': old_df['material_id'],
        'yds': old_df['on_hand_qty'],
        'lbs': old_df['on_hand_qty']  # Assuming same value for demo
    })
    
    # Format numbers with commas for large values
    new_df['yds'] = new_df['yds'].apply(lambda x: f"{x:,.0f}" if x >= 1000 else str(x))
    new_df['lbs'] = new_df['lbs'].apply(lambda x: f"{x:,.0f}" if x >= 1000 else str(x))
    
    # Save in live format
    new_df.to_csv(output_file, index=False)
    print(f"Migrated {len(new_df)} inventory records to {output_file}")

if __name__ == "__main__":
    migrate_inventory("old_inventory.csv", "Inventory.csv")
