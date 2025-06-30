"""
Generate suppliers for missing materials
"""

import pandas as pd
import random

# Load data
bom_df = pd.read_csv('data/integrated_boms_v3_corrected.csv')
supplier_df = pd.read_csv('data/integrated_suppliers_v2.csv')

# Get unique material IDs
bom_materials = set(bom_df['material_id'].astype(str).unique())
supplier_materials = set(supplier_df['material_id'].astype(str).unique())

# Find materials in BOM but not in suppliers
missing_materials = bom_materials - supplier_materials

print(f"Generating suppliers for {len(missing_materials)} missing materials...")

# Create new supplier records
new_suppliers = []
supplier_id_start = supplier_df['supplier_id'].max() + 1

for i, material_id in enumerate(missing_materials):
    # Create 1-3 suppliers per material
    num_suppliers = random.randint(1, 3)
    
    for j in range(num_suppliers):
        new_suppliers.append({
            'supplier_id': supplier_id_start + i * 3 + j,
            'material_id': int(material_id),
            'cost_per_unit': round(random.uniform(5, 50), 2),
            'lead_time_days': random.randint(7, 30),
            'moq': random.choice([100, 200, 500, 1000]),
            'reliability_score': round(random.uniform(0.85, 0.99), 2)
        })

# Create dataframe
new_supplier_df = pd.DataFrame(new_suppliers)

# Combine with existing suppliers
combined_df = pd.concat([supplier_df, new_supplier_df], ignore_index=True)

# Save to new file
output_file = 'data/integrated_suppliers_v3_complete.csv'
combined_df.to_csv(output_file, index=False)

print(f"Created {len(new_suppliers)} new supplier records")
print(f"Total suppliers: {len(combined_df)}")
print(f"Saved to: {output_file}")