# Beverly Knits AI Integration - Project Structure

This document describes the project structure created during Phase 1 of the Beverly Knits AI Raw Material Planner integration.

## Directory Structure

```
beverly-knits/
├── config/                      # Configuration files
│   ├── zen_ml_config.json      # ML/AI settings and parameters
│   ├── zen_code_config.json    # Code management settings
│   └── zen_data_config.json    # Data processing rules
│
├── src/                        # Source code
│   └── core/                   # Core integration modules
│       ├── __init__.py
│       ├── ml_integration_client.py      # ML/AI client
│       ├── code_management_client.py     # Code analysis/generation
│       └── data_processing_client.py     # Data validation/cleaning
│
├── models/                     # Model storage
│   └── ml_models/             # Trained ML models
│
├── temp/                       # Temporary processing files
│   ├── ml_processing/         # ML processing workspace
│   └── data_processing/       # Data processing workspace
│
├── integrations/              # External integrations
│   └── suppliers/             # Supplier-specific integrations
│
├── tests/                     # Test suite
│   ├── __init__.py
│   └── conftest.py           # Pytest configuration
│
├── templates/                 # Code generation templates
├── generated/                 # Generated code output
│
├── venv/                      # Python virtual environment
├── requirements.txt           # Python dependencies
└── verify_setup.py           # Setup verification script
```

## Configuration Files

### zen_ml_config.json
- Model storage location
- Temporary directory for ML processing
- Default algorithms for different ML tasks
- Training parameters

### zen_code_config.json
- Supported programming languages
- Code quality thresholds
- Template and output paths

### zen_data_config.json
- Data validation rules
- Processing tolerances
- Temporary directory for data operations

## Core Modules

### ml_integration_client.py
- `BeverlyKnitsMLClient`: Main class for ML operations
- Handles demand forecasting, risk assessment, inventory optimization, and price prediction

### code_management_client.py
- `BeverlyKnitsCodeManager`: Code analysis and generation
- Provides code quality metrics and automated code generation

### data_processing_client.py
- `BeverlyKnitsDataProcessor`: Data validation and cleaning
- Ensures data quality and consistency

## Next Steps

1. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Proceed to Phase 2: Core Client Implementation

## Verification

Run `python verify_setup.py` to verify the Phase 1 setup is complete.