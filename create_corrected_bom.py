import pandas as pd
import numpy as np

# Read the original Style_BOM
style_bom = pd.read_csv('data/Style_BOM.csv')

# Create the corrected integrated BOM
corrected_bom = []

# Process each row from Style_BOM
for _, row in style_bom.iterrows():
    sku_id = row['Style_ID']
    material_id = row['Yarn_ID']
    quantity = round(row['BOM_Percentage'], 3)  # Round to 3 decimal places
    
    corrected_bom.append({
        'sku_id': sku_id,
        'material_id': material_id,
        'quantity_per_unit': quantity
    })

# Convert to DataFrame
corrected_df = pd.DataFrame(corrected_bom)

# Verify totals sum to 1.0 for each SKU
print("Verifying SKU totals...")
sku_totals = corrected_df.groupby('sku_id')['quantity_per_unit'].sum()
problematic_skus = sku_totals[abs(sku_totals - 1.0) > 0.001]

if len(problematic_skus) > 0:
    print(f"\nWARNING: {len(problematic_skus)} SKUs don't sum to 1.0:")
    for sku, total in problematic_skus.items():
        print(f"  - {sku}: {total:.6f}")
else:
    print("✓ All SKUs sum to 1.0")

# Save the corrected BOM
corrected_df.to_csv('data/integrated_boms_v3_corrected.csv', index=False)
print(f"\nCorrected BOM saved to: data/integrated_boms_v3_corrected.csv")
print(f"Total rows: {len(corrected_df)}")
print(f"Total SKUs: {corrected_df['sku_id'].nunique()}")
print(f"Total unique materials: {corrected_df['material_id'].nunique()}")

# Compare with the original integrated BOM
original_integrated = pd.read_csv('data/integrated_boms_v2.csv')
print(f"\nComparison with original integrated BOM:")
print(f"  Original rows: {len(original_integrated)}")
print(f"  Corrected rows: {len(corrected_df)}")
print(f"  Difference: {len(corrected_df) - len(original_integrated)} rows")

# Show a sample of the corrected data
print("\nSample of corrected data:")
print(corrected_df.head(20).to_string(index=False))