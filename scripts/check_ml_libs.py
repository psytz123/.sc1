import sys
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info(f"Python version: {sys.version}")

# Check TensorFlow
try:
    import tensorflow as tf
    try:
        logger.info(f"TensorFlow IS installed: version {tf.__version__}")
    except AttributeError:
        logger.info("TensorFlow module found but version unavailable (possibly incompatible with Python 3.13)")
except ImportError:
    logger.info("TensorFlow is NOT installed")

# Check other ML libraries
libraries = {
    'sklearn': 'scikit-learn',
    'xgboost': 'XGBoost',
    'lightgbm': 'LightGBM',
    'torch': 'PyTorch',
    'statsmodels': 'statsmodels',
    'prophet': 'Prophet'
}

logger.info("\nML Library Status:")
for module, name in libraries.items():
    try:
        mod = __import__(module)
        version = "installed"
        if hasattr(mod, '__version__'):
            version = f"version {mod.__version__}"
        logger.info(f"✓ {name} is installed ({version})")
    except ImportError:
        logger.info(f"✗ {name} is NOT installed")