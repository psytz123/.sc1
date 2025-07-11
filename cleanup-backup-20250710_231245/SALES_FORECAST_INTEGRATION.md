# Sales-Based Forecasting Integration

## Overview
The Beverly Knits planning system now includes automated sales-based forecasting that integrates historical sales data with the raw material planning engine.

## How It Works

### 1. Sales Analysis and Forecast Generation
Run the enhanced sales analyzer to:
- Analyze historical sales patterns
- Generate forecasts for each style
- Calculate inventory alerts
- Save results for planner integration

```bash
python scripts/analyze_sales_inventory.py
```

This creates:
- `output/generated_forecasts.csv` - Forecasts for each style
- `output/sales_inventory_analysis.json` - Detailed analysis results
- `output/inventory_alerts.csv` - Styles with low inventory coverage
- `output/sales_forecast_integration.json` - Integration metadata

### 2. Planning Engine Integration
The main planner automatically:
- Checks for pre-generated forecasts (if less than 24 hours old)
- Loads forecasts from the sales analysis
- Combines them with other forecast sources
- Proceeds with BOM explosion and procurement planning

### 3. Configuration
Enable sales forecasting in `config/planning_config.yaml`:

```yaml
planning:
  enable_sales_forecasting: true
  sales_lookback_days: 90
  planning_horizon_days: 90
  aggregation_period: weekly
  safety_stock_method: statistical
```

## Workflow

1. **Regular Sales Analysis** (Daily/Weekly)
   ```bash
   python scripts/analyze_sales_inventory.py
   ```

2. **Run Planning Engine**
   ```bash
   python main.py
   ```

## Key Features

- **Automated Forecast Generation**: Based on historical sales patterns
- **Statistical Safety Stock**: Calculated based on demand variability
- **Inventory Alerts**: Identifies styles with low coverage
- **Seamless Integration**: Forecasts automatically used by planner
- **Configurable Parameters**: Adjust lookback period, horizon, etc.

## Benefits

1. **Data-Driven Planning**: Uses actual sales history
2. **Reduced Manual Work**: Automates forecast creation
3. **Better Inventory Management**: Proactive alerts
4. **Improved Accuracy**: Statistical methods for safety stock

## Monitoring

Check the logs for:
- Number of forecasts generated
- Total forecast quantity
- Integration status
- Any warnings or errors

## Troubleshooting

If forecasts aren't being used:
1. Check if `enable_sales_forecasting` is true in config
2. Verify forecast files exist in `output/` directory
3. Ensure forecast files are less than 24 hours old
4. Check logs for error messages
