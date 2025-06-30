"""
Test material ID matching issue
"""

import pandas as pd
from models.supplier import Supplier

# Load suppliers
supplier_df = pd.read_csv('data/integrated_suppliers_v3_complete.csv')

# Convert to Supplier objects as done in run_planner.py
suppliers = []
for _, row in supplier_df.iterrows():
    supplier = Supplier(
        supplier_id=str(row['supplier_id']),  # Convert to string
        material_id=str(row['material_id']),  # Convert to string
        cost_per_unit=row['cost_per_unit'],
        lead_time_days=row['lead_time_days'],
        moq=row.get('moq', 0),
        reliability_score=row.get('reliability_score', 0.95)
    )
    suppliers.append(supplier)

# Check what material IDs we have
material_ids = [s.material_id for s in suppliers]
print(f"Total suppliers: {len(suppliers)}")
print(f"Unique materials: {len(set(material_ids))}")
print(f"Sample material IDs: {material_ids[:10]}")

# Check if specific materials exist
needed = ['18767', '18929', '18320', '18707', '18708']
for mat_id in needed:
    found = [s for s in suppliers if s.material_id == mat_id]
    print(f"Material {mat_id}: {len(found)} suppliers found")