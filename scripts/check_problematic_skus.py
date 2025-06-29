import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

# Read the Style_BOM
style_bom = pd.read_csv('data/Style_BOM.csv')

# Check the problematic SKUs
problematic_skus = ['205FLX2006/M', 'C1B4545A/1D', 'C1B4637A/1', 'CF5492/0', 
                   'FF 10008/0005C', 'FF 10008/0009A', 'FF 10008/0010C', 
                   'FF 10008/0011C', 'FF 10008/0014C', 'FF25002/0008A']

logger.info("Investigating SKUs that don't sum to 1.0 in Style_BOM:")
logger.info("=" * 60)

for sku in problematic_skus:
    sku_data = style_bom[style_bom['Style_ID'] == sku]
    if not sku_data.empty:
        logger.info(f"\nSKU: {sku}")
        logger.info(f"Materials and percentages:")
        total = 0
        for _, row in sku_data.iterrows():
            logger.info(f"  Material {row['Yarn_ID']}: {row['BOM_Percentage']:.3f}")
            total += row['BOM_Percentage']
        logger.info(f"  TOTAL: {total:.6f}")
        
        # Check if this might be a data entry error
        if abs(total - 1.0) > 0.1:
            logger.info(f"  ⚠️  WARNING: Total is significantly off from 1.0!")
    else:
        logger.info(f"\nSKU: {sku} - NOT FOUND in Style_BOM")