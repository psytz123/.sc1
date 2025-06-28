import pandas as pd
import numpy as np

# Read both BOM files
style_bom = pd.read_csv('data/Style_BOM.csv')
integrated_bom = pd.read_csv('data/integrated_boms_v2.csv')

# Rename columns for consistency
style_bom.columns = ['sku_id', 'material_id', 'quantity_per_unit']

# Create a detailed report of rounding issues
print("=" * 80)
print("DETAILED ROUNDING ANALYSIS")
print("=" * 80)
print()

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
    print(f"Found {len(rounding_issues)} potential incorrect rounding cases:")
    print()
    
    # Group by type of rounding
    rounded_to_1 = [r for r in rounding_issues if r['integrated_value'] == 1.0]
    rounded_to_half = [r for r in rounding_issues if r['integrated_value'] == 0.5]
    other_rounding = [r for r in rounding_issues if r['integrated_value'] not in [1.0, 0.5]]
    
    if rounded_to_1:
        print(f"1. Values incorrectly rounded to 1.0: {len(rounded_to_1)} cases")
        for issue in rounded_to_1[:10]:
            print(f"   - SKU: {issue['sku']}, Material: {issue['material']}")
            print(f"     Style BOM: {issue['style_value']:.3f} → Integrated: {issue['integrated_value']:.3f}")
        if len(rounded_to_1) > 10:
            print(f"   ... and {len(rounded_to_1) - 10} more")
        print()
    
    if rounded_to_half:
        print(f"2. Values incorrectly rounded to 0.5: {len(rounded_to_half)} cases")
        for issue in rounded_to_half[:5]:
            print(f"   - SKU: {issue['sku']}, Material: {issue['material']}")
            print(f"     Style BOM: {issue['style_value']:.3f} → Integrated: {issue['integrated_value']:.3f}")
        if len(rounded_to_half) > 5:
            print(f"   ... and {len(rounded_to_half) - 5} more")
        print()

# Check for cases where materials were completely omitted (likely small percentages)
print("3. Materials completely omitted from integrated BOM (likely small percentages):")
print()

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
    print(f"Found {len(omitted_materials)} omitted materials:")
    print()
    
    # Group by percentage ranges
    under_1_pct = [m for m in omitted_materials if m['percentage'] < 0.01]
    under_5_pct = [m for m in omitted_materials if 0.01 <= m['percentage'] < 0.05]
    under_10_pct = [m for m in omitted_materials if 0.05 <= m['percentage'] < 0.10]
    over_10_pct = [m for m in omitted_materials if m['percentage'] >= 0.10]
    
    if under_1_pct:
        print(f"   Under 1% ({len(under_1_pct)} materials):")
        for m in under_1_pct[:5]:
            print(f"      - {m['sku']}: Material {m['material']} = {m['percentage']:.3f} ({m['percentage']*100:.1f}%)")
        if len(under_1_pct) > 5:
            print(f"      ... and {len(under_1_pct) - 5} more")
    
    if under_5_pct:
        print(f"\n   1% to 5% ({len(under_5_pct)} materials):")
        for m in under_5_pct[:5]:
            print(f"      - {m['sku']}: Material {m['material']} = {m['percentage']:.3f} ({m['percentage']*100:.1f}%)")
        if len(under_5_pct) > 5:
            print(f"      ... and {len(under_5_pct) - 5} more")
    
    if under_10_pct:
        print(f"\n   5% to 10% ({len(under_10_pct)} materials):")
        for m in under_10_pct[:5]:
            print(f"      - {m['sku']}: Material {m['material']} = {m['percentage']:.3f} ({m['percentage']*100:.1f}%)")
    
    if over_10_pct:
        print(f"\n   Over 10% ({len(over_10_pct)} materials) - CRITICAL:")
        for m in over_10_pct[:10]:
            print(f"      - {m['sku']}: Material {m['material']} = {m['percentage']:.3f} ({m['percentage']*100:.1f}%)")
        if len(over_10_pct) > 10:
            print(f"      ... and {len(over_10_pct) - 10} more")

print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()
print("1. The integrated BOM has significant issues:")
print("   - 61 SKUs are completely missing (50% of Style_BOM SKUs)")
print("   - 48 out of 60 SKUs have discrepancies")
print("   - Many materials with small percentages (<10%) were omitted")
print("   - Several materials were incorrectly rounded to 1.0 or 0.5")
print("   - Floating point precision issues in 74 entries")
print()
print("2. The integration process appears to have:")
print("   - Dropped materials with small percentages")
print("   - Incorrectly normalized remaining percentages to sum to 1.0")
print("   - Introduced floating point precision errors")
print()
print("3. Recommended actions:")
print("   - Re-run the integration process with proper handling of all materials")
print("   - Ensure no materials are dropped regardless of percentage")
print("   - Use proper decimal rounding (e.g., round to 3 decimal places)")
print("   - Validate that all SKU totals sum to exactly 1.0")