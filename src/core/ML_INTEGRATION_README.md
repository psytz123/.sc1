# Beverly Knits ML Integration Client

## Overview

The ML Integration Client provides advanced machine learning capabilities for the Beverly Knits Raw Material Planner. It supports both local ML libraries and optional integration with zen-mcp-server for enhanced AI features.

## Features

- **Demand Forecasting**: Predict future material requirements using time series analysis
- **Supplier Risk Assessment**: ML-based evaluation of supplier reliability and performance
- **Inventory Optimization**: AI-driven recommendations for optimal stock levels
- **Price Prediction**: Forecast material price trends
- **Automatic Fallback**: Seamlessly switches between zen-mcp-server and local ML libraries

## Installation

### Basic Installation (Local ML Only)
```bash
pip install -r requirements.txt
```

### Full Installation (With Deep Learning Support)
```bash
pip install -r requirements-deep-learning.txt
```

### Python 3.13 Compatibility
```bash
pip install -r requirements-python313.txt
```

## Configuration

The ML client uses a JSON configuration file located at `config/zen_ml_config.json`. Key settings include:

```json
{
  "zen_mcp_server": {
    "enabled": false,  // Set to true to enable zen-mcp-server
    "url": "http://localhost:8080/api",
    "timeout": 30,
    "retries": 3
  },
  "ml_settings": {
    "default_model": "auto",
    "confidence_level": 0.95
  }
}
```

## Usage

### Basic Example

```python
import asyncio
from src.core.ml_integration_client import BeverlyKnitsMLClient

async def main():
    # Initialize client
    client = BeverlyKnitsMLClient()
    
    # Check server status
    status = await client.check_zen_server_status()
    print(f"ML Server Available: {status['available']}")
    
    # Train a demand forecast model
    result = await client.train_demand_forecast_model(
        historical_data=demand_df,
        material_type="yarn"
    )
    
    # Generate predictions
    predictions = await client.predict_demand(
        model_id=result['model_id'],
        features=feature_df,
        horizon=30
    )
    
    # Clean up
    await client.close()

# Run
asyncio.run(main())
```

### Advanced Features

#### Supplier Risk Analysis
```python
risk_analysis = await client.analyze_supplier_risk(supplier_data)
```

#### Inventory Optimization
```python
optimization = await client.optimize_inventory_levels(
    inventory_data=current_inventory,
    demand_forecast=forecast_data
)
```

## Error Handling

The client includes comprehensive error handling:

- **Connection Timeouts**: Configurable timeout with automatic retry
- **Fallback to Local ML**: Automatically uses local libraries if zen-mcp-server is unavailable
- **Detailed Logging**: All operations are logged with timing information

## Testing

Run the test suite:
```bash
pytest tests/test_ml_integration_client.py -v
```

Run with coverage:
```bash
pytest tests/test_ml_integration_client.py --cov=src.core.ml_integration_client
```

## Logging

Logs are written to `logs/ml_integration.log` with automatic rotation. Configure logging in `config/zen_ml_config.json`:

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/ml_integration.log",
    "max_file_size_mb": 100,
    "backup_count": 5
  }
}
```

## Performance Considerations

- **Model Caching**: Recently used models are kept in memory
- **Batch Processing**: Large datasets are processed in configurable batches
- **Async Operations**: All ML operations are asynchronous for better performance
- **Connection Pooling**: HTTP connections are reused for zen-mcp-server calls

## Troubleshooting

### Common Issues

1. **"scikit-learn not installed"**
   - Solution: `pip install scikit-learn`

2. **"Connection to zen-mcp-server failed"**
   - Check if zen-mcp-server is running
   - Verify URL in configuration
   - Check firewall settings

3. **"Model not found"**
   - Ensure model was trained successfully
   - Check `models/ml_models/` directory

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('src.core.ml_integration_client').setLevel(logging.DEBUG)
```

## API Reference

### BeverlyKnitsMLClient

#### Methods

- `__init__(config_path: Optional[str] = None)`: Initialize the client
- `check_zen_server_status() -> Dict[str, Any]`: Check ML server availability
- `train_demand_forecast_model(historical_data, material_type, model_type) -> Dict[str, Any]`: Train forecasting model
- `predict_demand(model_id, features, horizon) -> Dict[str, Any]`: Generate predictions
- `analyze_supplier_risk(supplier_data) -> Dict[str, Any]`: Assess supplier risks
- `optimize_inventory_levels(inventory_data, demand_forecast) -> Dict[str, Any]`: Optimize stock levels
- `close()`: Clean up resources

## Contributing

When adding new ML features:

1. Add the feature to the client class
2. Implement both zen-mcp-server and local fallback versions
3. Add comprehensive unit tests
4. Update this documentation

## License

Part of Beverly Knits Raw Material Planner