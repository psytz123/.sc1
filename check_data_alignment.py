"""
Check data alignment between BOM materials and suppliers
"""

import pandas as pd

# Load data
bom_df = pd.read_csv('data/integrated_boms_v3_corrected.csv')
supplier_df = pd.read_csv('data/integrated_suppliers_v2.csv')

# Get unique material IDs
bom_materials = set(bom_df['material_id'].astype(str).unique())
supplier_materials = set(supplier_df['material_id'].astype(str).unique())

print("BOM Materials:", len(bom_materials))
print("Supplier Materials:", len(supplier_materials))

# Find materials in BOM but not in suppliers
missing_suppliers = bom_materials - supplier_materials
print(f"\nMaterials in BOM but not in suppliers: {len(missing_suppliers)}")
if missing_suppliers:
    print("Sample missing:", list(missing_suppliers)[:10])

# Find materials in suppliers but not in BOM
extra_suppliers = supplier_materials - bom_materials
print(f"\nMaterials in suppliers but not in BOM: {len(extra_suppliers)}")
if extra_suppliers:
    print("Sample extra:", list(extra_suppliers)[:10])

# Find common materials
common_materials = bom_materials & supplier_materials
print(f"\nCommon materials: {len(common_materials)}")
if common_materials:
    print("Sample common:", list(common_materials)[:10])