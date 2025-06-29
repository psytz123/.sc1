import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

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
logger.info("Verifying SKU totals...")
sku_totals = corrected_df.groupby('sku_id')['quantity_per_unit'].sum()
problematic_skus = sku_totals[abs(sku_totals - 1.0) > 0.001]

if len(problematic_skus) > 0:
    logger.info(f"\nWARNING: {len(problematic_skus)} SKUs don't sum to 1.0:")
    for sku, total in problematic_skus.items():
        logger.info(f"  - {sku}: {total:.6f}")
else:
    logger.info("✓ All SKUs sum to 1.0")

# Save the corrected BOM
corrected_df.to_csv('data/integrated_boms_v3_corrected.csv', index=False)
logger.info(f"\nCorrected BOM saved to: data/integrated_boms_v3_corrected.csv")
logger.info(f"Total rows: {len(corrected_df)}")
logger.info(f"Total SKUs: {corrected_df['sku_id'].nunique()}")
logger.info(f"Total unique materials: {corrected_df['material_id'].nunique()}")

# Compare with the original integrated BOM
original_integrated = pd.read_csv('data/integrated_boms_v2.csv')
logger.info(f"\nComparison with original integrated BOM:")
logger.info(f"  Original rows: {len(original_integrated)}")
logger.info(f"  Corrected rows: {len(corrected_df)}")
logger.info(f"  Difference: {len(corrected_df) - len(original_integrated)} rows")

# Show a sample of the corrected data
logger.info("\nSample of corrected data:")
logger.info(corrected_df.head(20).to_string(index=False))