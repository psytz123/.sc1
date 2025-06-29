# Beverly Knits Project Structure

## Directory Organization

```
beverly-knits/
├── config/               # Configuration files
│   ├── __init__.py
│   ├── settings.py      # Business rules and settings
│   └── secure_config.py # Secure configuration management
├── data/                # Data processing and sample data
│   ├── __init__.py
│   ├── sample_data_generator.py
│   └── sales_data_processor.py
├── engine/              # Core planning engine
│   ├── __init__.py
│   ├── planner.py
│   ├── sales_planning_integration.py
│   └── style_yarn_bom_integration.py
├── integrations/        # External system integrations
│   └── suppliers/
├── models/              # Data models
│   ├── __init__.py
│   ├── bom.py
│   ├── forecast.py
│   ├── inventory.py
│   ├── recommendation.py
│   ├── sales_forecast_generator.py
│   └── supplier.py
├── scripts/             # Utility scripts
│   ├── demo_*.py        # Demo scripts
│   ├── check_*.py       # Verification scripts
│   └── setup_*.py       # Setup scripts
├── tests/               # Test files
│   ├── __init__.py
│   └── test_*.py        # Unit tests
├── utils/               # Utility modules
│   ├── __init__.py
│   ├── helpers.py
│   └── logger.py        # Centralized logging
├── logs/                # Log files
├── reports/             # Generated reports
├── main.py              # Main application entry point
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Code Standards

- Use type hints for all function parameters and returns
- Follow PEP 8 naming conventions
- Add docstrings to all classes and functions
- Use logging instead of print statements
- No hardcoded secrets or credentials
- Proper error handling with try/except blocks