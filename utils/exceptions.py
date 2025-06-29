"""
Custom exceptions for Beverly Knits Raw Material Planner
"""


class BeverlyKnitsException(Exception):
    """Base exception for all Beverly Knits exceptions"""


class DataValidationError(BeverlyKnitsException):
    """Raised when data validation fails"""


class FileLoadError(BeverlyKnitsException):
    """Raised when file loading fails"""


class BOMError(BeverlyKnitsException):
    """Raised when BOM processing fails"""


class InventoryError(BeverlyKnitsException):
    """Raised when inventory processing fails"""


class SupplierError(BeverlyKnitsException):
    """Raised when supplier processing fails"""


class PlanningError(BeverlyKnitsException):
    """Raised when planning process fails"""


class ConfigurationError(BeverlyKnitsException):
    """Raised when configuration is invalid"""
