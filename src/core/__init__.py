"""
Beverly Knits Core Integration Package

This package contains the core integration clients for:
- ML/AI capabilities
- Code management
- Data processing
"""

from .code_management_client import BeverlyKnitsCodeManager
from .data_processing_client import BeverlyKnitsDataProcessor
from .ml_integration_client import BeverlyKnitsMLClient

__all__ = [
    'BeverlyKnitsMLClient',
    'BeverlyKnitsCodeManager',
    'BeverlyKnitsDataProcessor'
]

__version__ = '0.1.0'