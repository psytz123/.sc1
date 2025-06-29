import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

# Read both BOM files
style_bom = pd.read_csv('data/Style_BOM.csv')
integrated_bom = pd.read_csv('data/integrated_boms_v2.csv')

# Rename columns for consistency
style_bom.columns = ['sku_id', 'material_id', 'quantity_per_unit']

# Group by SKU to compare
style_grouped = style_bom.groupby('sku_id')
integrated_grouped = integrated_bom.groupby('sku_id')

# Find discrepancies
logger.info("=" * 80)
logger.info("BOM COMPARISON REPORT")
logger.info("=" * 80)
logger.info()

# 1. SKUs missing from integrated BOM
style_skus = set(style_bom['sku_id'].unique())
integrated_skus = set(integrated_bom['sku_id'].unique())

missing_skus = style_skus - integrated_skus
if missing_skus:
    logger.info(f"1. SKUs in Style_BOM but missing from Integrated BOM: {len(missing_skus)}")
    for sku in sorted(missing_skus)[:10]:  # Show first 10
        logger.info(f"   - {sku}")
    if len(missing_skus) > 10:
        logger.info(f"   ... and {len(missing_skus) - 10} more")
    logger.info()

# 2. SKUs with missing materials or incorrect percentages
logger.info("2. SKUs with discrepancies in materials or percentages:")
logger.info()

discrepancy_count = 0
for sku in sorted(integrated_skus):
    if sku in style_skus:
        style_data = style_grouped.get_group(sku).set_index('material_id')['quantity_per_unit']
        integrated_data = integrated_grouped.get_group(sku).set_index('material_id')['quantity_per_unit']
        
        # Check for missing materials
        style_materials = set(style_data.index)
        integrated_materials = set(integrated_data.index)
        
        missing_materials = style_materials - integrated_materials
        extra_materials = integrated_materials - style_materials
        
        # Check for percentage mismatches
        common_materials = style_materials & integrated_materials
        mismatches = []
        
        for material in common_materials:
            style_pct = style_data[material]
            integrated_pct = integrated_data[material]
            
            # Check if values differ by more than 0.001 (0.1%)
            if abs(style_pct - integrated_pct) > 0.001:
                mismatches.append((material, style_pct, integrated_pct))
        
        # Check total percentages
        style_total = style_data.sum()
        integrated_total = integrated_data.sum()
        
        if missing_materials or extra_materials or mismatches or abs(style_total - integrated_total) > 0.001:
            discrepancy_count += 1
            if discrepancy_count <= 20:  # Show first 20 discrepancies
                logger.info(f"   SKU: {sku}")
                
                if missing_materials:
                    logger.info(f"      Missing materials in integrated BOM:")
                    for mat in missing_materials:
                        logger.info(f"         - Material {mat}: {style_data[mat]:.3f} (from Style_BOM)")
                
                if extra_materials:
                    logger.info(f"      Extra materials in integrated BOM:")
                    for mat in extra_materials:
                        logger.info(f"         - Material {mat}: {integrated_data[mat]:.3f}")
                
                if mismatches:
                    logger.info(f"      Percentage mismatches:")
                    for mat, style_val, integrated_val in mismatches:
                        logger.info(f"         - Material {mat}: Style_BOM={style_val:.3f}, Integrated={integrated_val:.3f}")
                
                logger.info(f"      Total percentages: Style_BOM={style_total:.3f}, Integrated={integrated_total:.3f}")
                logger.info()

if discrepancy_count > 20:
    logger.info(f"   ... and {discrepancy_count - 20} more SKUs with discrepancies")
    logger.info()

# 3. Floating point precision issues
logger.info("3. Floating point precision issues in integrated BOM:")
precision_issues = integrated_bom[integrated_bom['quantity_per_unit'].astype(str).str.contains(r'\d{10,}')]
if len(precision_issues) > 0:
    logger.info(f"   Found {len(precision_issues)} entries with precision issues")
    for idx, row in precision_issues.head(10).iterrows():
        logger.info(f"   - {row['sku_id']}, Material {row['material_id']}: {row['quantity_per_unit']}")
    if len(precision_issues) > 10:
        logger.info(f"   ... and {len(precision_issues) - 10} more")
else:
    logger.info("   No precision issues found")

logger.info()
logger.info("=" * 80)
logger.info("SUMMARY")
logger.info("=" * 80)
logger.info(f"Total SKUs in Style_BOM: {len(style_skus)}")
logger.info(f"Total SKUs in Integrated BOM: {len(integrated_skus)}")
logger.info(f"SKUs with discrepancies: {discrepancy_count}")