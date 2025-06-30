"""
Check material IDs in BOM after loading
"""

import pandas as pd
from models.bom import BillOfMaterials

# Load BOMs as done in run_planner.py
bom_df = pd.read_csv('data/integrated_boms_v3_corrected.csv')
boms = []
for _, row in bom_df.iterrows():
    bom = BillOfMaterials(
        sku_id=str(row['sku_id']),
        material_id=str(row['material_id']),
        qty_per_unit=row['quantity_per_unit'],
        unit=row.get('unit', 'kg')
    )
    boms.append(bom)

# Check material IDs
material_ids = [b.material_id for b in boms[:10]]
print(f"Sample BOM material IDs: {material_ids}")
print(f"Type of first material ID: {type(material_ids[0])}")