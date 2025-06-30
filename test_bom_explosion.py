"""
Test BOM explosion material IDs
"""

import pandas as pd
from models.forecast import FinishedGoodsForecast as Forecast, ForecastProcessor
from models.bom import BillOfMaterials
from engine.planner import RawMaterialPlanner
from config.settings import PlanningConfig

# Load forecasts
forecast_df = pd.read_csv('data/real_data_sample_forecasts.csv')
forecast_df['forecast_qty'] = forecast_df['quantity']
forecast_df['source'] = forecast_df['source'].replace({'Historical': 'sales_history'})

# Create Forecast objects
forecasts = []
for _, row in forecast_df.iterrows():
    forecast = Forecast(
        sku_id=row['sku_id'],
        forecast_qty=row['forecast_qty'],
        forecast_date=pd.to_datetime(row['forecast_date']),
        source=row['source'],
        confidence=row.get('confidence', 0.8)
    )
    forecasts.append(forecast)

# Load BOMs
bom_df = pd.read_csv('data/integrated_boms_v3_corrected.csv')
boms = []
for _, row in bom_df.iterrows():
    bom = BillOfMaterials(
        sku_id=str(row['sku_id']),
        material_id=str(row['material_id']),
        qty_per_unit=row['quantity_per_unit'],
        unit=row.get('unit', 'kg')
    )
    boms.append(bom)

# Initialize planner
config = PlanningConfig()
planner = RawMaterialPlanner(config)

# Test BOM explosion
unified_forecasts = planner._unify_forecasts(forecasts)
material_requirements = planner._explode_boms(unified_forecasts, boms)

print(f"Material requirements: {len(material_requirements)}")
for mat_id, req in list(material_requirements.items())[:5]:
    print(f"Material ID: {mat_id} (type: {type(mat_id)}), Required: {req['total_requirement']}")