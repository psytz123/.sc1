# Beverly Knits - Sales Integration Documentation

## Overview

The Beverly Knits Sales Integration module provides comprehensive functionality for converting historical sales data into forecasts and integrating them with the raw material planning system. This module includes automated forecast generation, seasonality detection, safety stock calculation, and style-to-yarn BOM explosion.

## Key Components

### 1. Sales Forecast Generator (`models/sales_forecast_generator.py`)

The Sales Forecast Generator is an enhanced module that converts historical sales data into forecasts compatible with the planning system.

#### Features:
- **Automatic Seasonality Detection**: Analyzes historical patterns for monthly seasonality
- **Statistical Safety Stock**: Multiple calculation methods (percentage, statistical, min-max, dynamic)
- **Weekly Demand Calculation**: Flexible aggregation periods (daily, weekly, monthly, quarterly)
- **Confidence Scoring**: Based on demand variability and data availability

#### Usage Example:
```python
from models.sales_forecast_generator import SalesForecastGenerator
import pandas as pd

# Load sales data
sales_df = pd.read_csv('sales_data.csv')

# Initialize generator
generator = SalesForecastGenerator(
    sales_df=sales_df,
    planning_horizon_days=90,
    lookback_days=365,
    aggregation_period='weekly',
    safety_stock_method='statistical',
    service_level=0.95
)

# Generate forecasts with auto-seasonality
forecasts = generator.generate_forecasts_with_auto_seasonality(
    include_safety_stock=True,
    growth_factor=1.05,  # 5% growth
    auto_detect_seasonality=True
)
```

### 2. Sales Data Processor (`data/sales_data_processor.py`)

Handles the complete pipeline from raw sales data to planning-ready forecasts.

#### Capabilities:
- Loads and validates sales, inventory, and orders data
- Merges sales with inventory for comprehensive analysis
- Identifies low-stock items requiring immediate attention
- Validates style-to-yarn mappings
- Creates automated forecast pipeline

#### Pipeline Example:
```python
from data.sales_data_processor import SalesDataProcessor

processor = SalesDataProcessor()
output_files = processor.create_automated_forecast_pipeline(
    sales_file="data/Sales Activity Report.csv",
    inventory_file="data/Inventory.csv",
    bom_file="data/cfab_Yarn_Demand_By_Style.csv"
)
```

### 3. Style-to-Yarn BOM Integration (`engine/style_yarn_bom_integration.py`)

Provides accurate explosion of style-level forecasts to yarn requirements using percentage-based compositions.

#### Features:
- Reads style-to-yarn mappings from cfab_Yarn_Demand_By_Style.csv
- Handles percentage-based yarn compositions
- Validates yarn percentages sum to 100%
- Provides unit conversion capabilities
- Tracks weekly demand patterns

#### Integration Example:
```python
from engine.style_yarn_bom_integration import StyleYarnBOMIntegrator

# Initialize integrator
integrator = StyleYarnBOMIntegrator('data/cfab_Yarn_Demand_By_Style.csv')

# Define style forecasts (in yards)
style_forecasts = {
    '1853/L': 10000.0,      # 10,000 yards
    '180001/20ST2': 5000.0, # 5,000 yards
}

# Explode to yarn requirements
yarn_requirements = integrator.explode_style_forecast_to_yarn(style_forecasts)
```

### 4. Sales Planning Integration (`engine/sales_planning_integration.py`)

Orchestrates the integration between sales-based forecasts and the main planning system.

#### Capabilities:
- Combines forecasts from multiple sources (sales, manual, orders)
- Integrates with existing planning engine
- Provides validation capabilities
- Generates comprehensive reports

## Configuration

### Sales Forecast Configuration (`config/settings.py`):
```python
DEFAULT_SALES_FORECAST_CONFIG = {
    'lookback_days': 90,              # Historical period for analysis
    'planning_horizon_days': 90,      # Future planning period
    'min_sales_history_days': 30,     # Minimum history required
    'safety_stock_method': 'statistical',  # Method for safety stock
    'aggregation_period': 'weekly',   # Time aggregation period
    'enable_sales_forecasting': True, # Enable sales-based forecasts
    'use_style_yarn_bom': True       # Use style-to-yarn explosion
}

SAFETY_STOCK_CONFIG = {
    'method': 'statistical',          # Calculation method
    'service_level': 0.95,           # Target service level
    'min_safety_percentage': 0.1,     # Minimum safety stock %
    'max_safety_percentage': 0.5,     # Maximum safety stock %
    'variability_threshold': 0.3,     # CV threshold for high variability
    'lead_time_factor': True         # Include lead time in calculation
}
```

## Data Requirements

### Input Files:
1. **Sales Activity Report.csv**
   - Columns: Invoice Date, Style, Yds_ordered, Line Price
   - Historical sales transactions

2. **Inventory.csv**
   - Current inventory levels by style/yarn
   - On-hand, on-order, and allocated quantities

3. **cfab_Yarn_Demand_By_Style.csv**
   - Style-to-yarn mapping with percentages
   - Historical weekly demand patterns

### Output Files:
- `sales_based_forecasts.csv` - Generated forecasts
- `yarn_requirements.json` - Exploded yarn requirements
- `sales_inventory_summary.json` - Analysis summary

## Implementation Status

### Completed Features ✅:
1. **BOM Data Quality Fix** - Preserves all materials and handles precision
2. **Sales Forecast Generator** - Full statistical forecasting capabilities
3. **Sales Data Processor** - Complete data pipeline
4. **Configuration Updates** - All parameters integrated
5. **Sales Planning Integration** - Multi-source forecast combination
6. **Test Suite** - Comprehensive testing coverage
7. **Style-to-Yarn BOM Explosion** - Percentage-based explosion
8. **Automated Forecast Creation** - End-to-end automation
9. **Weekly/Monthly Aggregation** - Flexible time periods
10. **Safety Stock Calculation** - Multiple methods implemented

### Integration Points:
- Seamlessly integrates with existing planning engine
- Compatible with all data models
- Works with Streamlit interface
- Supports real Beverly Knits data formats

## Running the Integration

### Step 1: Fix BOM Data Issues
```bash
python fix_bom_integration.py
```

### Step 2: Run Sales Integration
```bash
python integrate_sales_planning.py
```

### Step 3: Test the Integration
```bash
python test_sales_integration.py
python test_enhanced_sales_integration.py
python test_style_yarn_bom_integration.py
```

### Step 4: Use in Production
Enable in configuration and run through Streamlit interface or command line.

## Benefits

1. **Improved Accuracy**: Data-driven demand predictions from actual sales
2. **Better Inventory Management**: Statistical safety stock optimization
3. **Flexibility**: Multiple aggregation and calculation methods
4. **Automation**: Reduced manual effort in planning
5. **Risk Mitigation**: Variability-based safety stock handling

## Next Steps

1. **Validate with Full Dataset**: Run complete Beverly Knits data
2. **Tune Parameters**: Adjust based on business requirements
3. **Monitor Accuracy**: Track forecast vs actual performance
4. **Enhance UI**: Add sales integration controls to web interface
5. **Schedule Automation**: Set up daily/weekly regeneration

## Troubleshooting

### Common Issues:
1. **Missing Style in BOM**: Check cfab_Yarn_Demand_By_Style.csv for style entry
2. **Percentage Validation Warnings**: Review and fix BOM percentages
3. **Insufficient History**: Ensure minimum 30 days of sales data
4. **Unit Conversion Errors**: Verify unit specifications in data

### Debug Mode:
Enable detailed logging in configuration for troubleshooting:
```python
config['debug_mode'] = True
config['log_level'] = 'DEBUG'
```