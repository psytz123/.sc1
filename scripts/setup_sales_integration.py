"""
Configuration updater for enabling sales-based forecasting
"""

import json
from pathlib import Path

def update_planning_config():
    """Update the planning configuration to enable sales forecasting"""

    # Use JSON format for configuration
    config_file = Path('config/planning_config.json')

    config_data = {
        'planning': {
            'enable_sales_forecasting': True,
            'sales_lookback_days': 90,
            'planning_horizon_days': 90,
            'aggregation_period': 'weekly',
            'safety_stock_method': 'statistical',
            'safety_stock_percentage': 0.1,
            'enable_multi_supplier': True,
            'use_style_yarn_bom': True,
            'style_yarn_bom_file': 'data/cfab_Yarn_Demand_By_Style.csv'
        },
        'forecasting': {
            'confidence_threshold': 0.7,
            'min_history_days': 30,
            'service_level': 0.95
        },
        'inventory': {
            'lead_time_buffer_days': 7,
            'min_coverage_months': 2
        }
    }

    # Check if config exists and merge
    if config_file.exists():
        # Load existing config
        with open(config_file, 'r') as f:
            existing_config = json.load(f)

        # Merge with new settings
        for key, value in config_data.items():
            if key in existing_config:
                existing_config[key].update(value)
            else:
                existing_config[key] = value

        config_data = existing_config

    # Ensure config directory exists
    config_file.parent.mkdir(exist_ok=True)

    # Save config
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)

    print(f"✅ Configuration saved to: {config_file}")

    # Also update settings.py if it exists
    settings_file = Path('config/settings.py')
    if settings_file.exists():
        # Add a comment to settings.py about the JSON config
        with open(settings_file, 'r') as f:
            content = f.read()

        if 'enable_sales_forecasting' not in content:
            # Add the setting to the file
            additional_settings = '''
# Sales forecasting integration
# These settings can also be configured in planning_config.json
ENABLE_SALES_FORECASTING = True
SALES_LOOKBACK_DAYS = 90
PLANNING_HORIZON_DAYS = 90
AGGREGATION_PERIOD = 'weekly'
SAFETY_STOCK_METHOD = 'statistical'
'''
            with open(settings_file, 'a') as f:
                f.write(additional_settings)
            print(f"✅ Updated settings.py with sales forecasting configuration")

    return config_data
    
    return config_data

def create_integration_readme():
    """Create a README for the sales-planning integration"""
    
    readme_content = """# Sales-Based Forecasting Integration

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
"""
    
    readme_file = Path('SALES_FORECAST_INTEGRATION.md')
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"📚 Created integration documentation: {readme_file}")

def main():
    """Main function to set up sales forecasting integration"""
    print("🔧 Setting up Sales-Based Forecasting Integration")
    print("=" * 50)
    
    # Update configuration
    config = update_planning_config()
    
    # Create documentation
    create_integration_readme()
    
    print("\n✅ Sales forecasting integration setup complete!")
    print("\nNext steps:")
    print("1. Run: python scripts/analyze_sales_inventory.py")
    print("2. Run: python main.py")
    print("\nThe planner will now automatically use sales-based forecasts!")

if __name__ == "__main__":
    main()