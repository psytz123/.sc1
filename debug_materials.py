"""
Debug material requirements
"""

import pandas as pd

# Load BOM and check which materials are needed for the forecasted SKUs
forecast_df = pd.read_csv('data/real_data_sample_forecasts.csv')
bom_df = pd.read_csv('data/integrated_boms_v3_corrected.csv')

# Get unique SKUs from forecasts
forecast_skus = forecast_df['sku_id'].unique()
print(f"Forecasted SKUs: {len(forecast_skus)}")
print("Sample SKUs:", forecast_skus[:10])

# Find materials needed for these SKUs
needed_boms = bom_df[bom_df['sku_id'].isin(forecast_skus)]
needed_materials = needed_boms['material_id'].unique()
print(f"\nMaterials needed: {len(needed_materials)}")
print("Sample materials:", needed_materials[:10])