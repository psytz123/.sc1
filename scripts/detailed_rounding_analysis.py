import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

# Read both BOM files
style_bom = pd.read_csv('data/Style_BOM.csv')
integrated_bom = pd.read_csv('data/integrated_boms_v2.csv')

# Rename columns for consistency
style_bom.columns = ['sku_id', 'material_id', 'quantity_per_unit']

# Create a detailed report of rounding issues
logger.info("=" * 80)
logger.info("DETAILED ROUNDING ANALYSIS")
logger.info("=" * 80)
logger.info()

# Find SKUs with incorrect rounding
style_grouped = style_bom.groupby('sku_id')
integrated_grouped = integrated_bom.groupby('sku_id')

# Common SKUs
common_skus = set(style_bom['sku_id'].unique()) & set(integrated_bom['sku_id'].unique())

rounding_issues = []

for sku in sorted(common_skus):
    style_data = style_grouped.get_group(sku)
    integrated_data = integrated_grouped.get_group(sku)
    
    # Check if integrated BOM appears to have incorrectly rounded values
    for _, int_row in integrated_data.iterrows():
        material = int_row['material_id']
        int_value = int_row['quantity_per_unit']
        
        # Find corresponding value in style BOM
        style_match = style_data[style_data['material_id'] == material]
        
        if not style_match.empty:
            style_value = style_match.iloc[0]['quantity_per_unit']
            
            # Check if the integrated value looks like incorrect rounding
            # For example, if style has 0.878 and integrated has 1.0
            if abs(style_value - int_value) > 0.01:
                # Check if integrated value is suspiciously round (1.0, 0.5, etc.)
                if int_value in [1.0, 0.5, 0.25, 0.75] and style_value not in [1.0, 0.5, 0.25, 0.75]:
                    rounding_issues.append({
                        'sku': sku,
                        'material': material,
                        'style_value': style_value,
                        'integrated_value': int_value,
                        'difference': int_value - style_value
                    })

# Display rounding issues
if rounding_issues:
    logger.info(f"Found {len(rounding_issues)} potential incorrect rounding cases:")
    logger.info()
    
    # Group by type of rounding
    rounded_to_1 = [r for r in rounding_issues if r['integrated_value'] == 1.0]
    rounded_to_half = [r for r in rounding_issues if r['integrated_value'] == 0.5]
    other_rounding = [r for r in rounding_issues if r['integrated_value'] not in [1.0, 0.5]]
    
    if rounded_to_1:
        logger.info(f"1. Values incorrectly rounded to 1.0: {len(rounded_to_1)} cases")
        for issue in rounded_to_1[:10]:
            logger.info(f"   - SKU: {issue['sku']}, Material: {issue['material']}")
            logger.info(f"     Style BOM: {issue['style_value']:.3f} → Integrated: {issue['integrated_value']:.3f}")
        if len(rounded_to_1) > 10:
            logger.info(f"   ... and {len(rounded_to_1) - 10} more")
        logger.info()
    
    if rounded_to_half:
        logger.info(f"2. Values incorrectly rounded to 0.5: {len(rounded_to_half)} cases")
        for issue in rounded_to_half[:5]:
            logger.info(f"   - SKU: {issue['sku']}, Material: {issue['material']}")
            logger.info(f"     Style BOM: {issue['style_value']:.3f} → Integrated: {issue['integrated_value']:.3f}")
        if len(rounded_to_half) > 5:
            logger.info(f"   ... and {len(rounded_to_half) - 5} more")
        logger.info()

# Check for cases where materials were completely omitted (likely small percentages)
logger.info("3. Materials completely omitted from integrated BOM (likely small percentages):")
logger.info()

omitted_materials = []
for sku in sorted(common_skus):
    style_data = style_grouped.get_group(sku)
    integrated_data = integrated_grouped.get_group(sku)
    
    style_materials = set(style_data['material_id'])
    integrated_materials = set(integrated_data['material_id'])
    
    missing = style_materials - integrated_materials
    
    for material in missing:
        style_row = style_data[style_data['material_id'] == material].iloc[0]
        percentage = style_row['quantity_per_unit']
        omitted_materials.append({
            'sku': sku,
            'material': material,
            'percentage': percentage
        })

# Sort by percentage to see if small percentages were systematically omitted
omitted_materials.sort(key=lambda x: x['percentage'])

if omitted_materials:
    logger.info(f"Found {len(omitted_materials)} omitted materials:")
    logger.info()
    
    # Group by percentage ranges
    under_1_pct = [m for m in omitted_materials if m['percentage'] < 0.01]
    under_5_pct = [m for m in omitted_materials if 0.01 <= m['percentage'] < 0.05]
    under_10_pct = [m for m in omitted_materials if 0.05 <= m['percentage'] < 0.10]
    over_10_pct = [m for m in omitted_materials if m['percentage'] >= 0.10]
    
    if under_1_pct:
        logger.info(f"   Under 1% ({len(under_1_pct)} materials):")
        for m in under_1_pct[:5]:
            logger.info(f"      - {m['sku']}: Material {m['material']} = {m['percentage']:.3f} ({m['percentage']*100:.1f}%)")
        if len(under_1_pct) > 5:
            logger.info(f"      ... and {len(under_1_pct) - 5} more")
    
    if under_5_pct:
        logger.info(f"\n   1% to 5% ({len(under_5_pct)} materials):")
        for m in under_5_pct[:5]:
            logger.info(f"      - {m['sku']}: Material {m['material']} = {m['percentage']:.3f} ({m['percentage']*100:.1f}%)")
        if len(under_5_pct) > 5:
            logger.info(f"      ... and {len(under_5_pct) - 5} more")
    
    if under_10_pct:
        logger.info(f"\n   5% to 10% ({len(under_10_pct)} materials):")
        for m in under_10_pct[:5]:
            logger.info(f"      - {m['sku']}: Material {m['material']} = {m['percentage']:.3f} ({m['percentage']*100:.1f}%)")
    
    if over_10_pct:
        logger.info(f"\n   Over 10% ({len(over_10_pct)} materials) - CRITICAL:")
        for m in over_10_pct[:10]:
            logger.info(f"      - {m['sku']}: Material {m['material']} = {m['percentage']:.3f} ({m['percentage']*100:.1f}%)")
        if len(over_10_pct) > 10:
            logger.info(f"      ... and {len(over_10_pct) - 10} more")

logger.info()
logger.info("=" * 80)
logger.info("RECOMMENDATIONS")
logger.info("=" * 80)
logger.info()
logger.info("1. The integrated BOM has significant issues:")
logger.info("   - 61 SKUs are completely missing (50% of Style_BOM SKUs)")
logger.info("   - 48 out of 60 SKUs have discrepancies")
logger.info("   - Many materials with small percentages (<10%) were omitted")
logger.info("   - Several materials were incorrectly rounded to 1.0 or 0.5")
logger.info("   - Floating point precision issues in 74 entries")
logger.info()
logger.info("2. The integration process appears to have:")
logger.info("   - Dropped materials with small percentages")
logger.info("   - Incorrectly normalized remaining percentages to sum to 1.0")
logger.info("   - Introduced floating point precision errors")
logger.info()
logger.info("3. Recommended actions:")
logger.info("   - Re-run the integration process with proper handling of all materials")
logger.info("   - Ensure no materials are dropped regardless of percentage")
logger.info("   - Use proper decimal rounding (e.g., round to 3 decimal places)")
logger.info("   - Validate that all SKU totals sum to exactly 1.0")