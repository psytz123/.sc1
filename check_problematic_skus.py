import pandas as pd

# Read the Style_BOM
style_bom = pd.read_csv('data/Style_BOM.csv')

# Check the problematic SKUs
problematic_skus = ['205FLX2006/M', 'C1B4545A/1D', 'C1B4637A/1', 'CF5492/0', 
                   'FF 10008/0005C', 'FF 10008/0009A', 'FF 10008/0010C', 
                   'FF 10008/0011C', 'FF 10008/0014C', 'FF25002/0008A']

print("Investigating SKUs that don't sum to 1.0 in Style_BOM:")
print("=" * 60)

for sku in problematic_skus:
    sku_data = style_bom[style_bom['Style_ID'] == sku]
    if not sku_data.empty:
        print(f"\nSKU: {sku}")
        print(f"Materials and percentages:")
        total = 0
        for _, row in sku_data.iterrows():
            print(f"  Material {row['Yarn_ID']}: {row['BOM_Percentage']:.3f}")
            total += row['BOM_Percentage']
        print(f"  TOTAL: {total:.6f}")
        
        # Check if this might be a data entry error
        if abs(total - 1.0) > 0.1:
            print(f"  ⚠️  WARNING: Total is significantly off from 1.0!")
    else:
        print(f"\nSKU: {sku} - NOT FOUND in Style_BOM")