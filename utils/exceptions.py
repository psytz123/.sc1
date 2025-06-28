"""
Custom exceptions for Beverly Knits Raw Material Planner
"""


class BeverlyKnitsException(Exception):
    """Base exception for all Beverly Knits exceptions"""
    pass


class DataValidationError(BeverlyKnitsException):
    """Raised when data validation fails"""
    pass


class FileLoadError(BeverlyKnitsException):
    """Raised when file loading fails"""
    pass


class BOMError(BeverlyKnitsException):
    """Raised when BOM processing fails"""
    pass


class InventoryError(BeverlyKnitsException):
    """Raised when inventory processing fails"""
    pass


class SupplierError(BeverlyKnitsException):
    """Raised when supplier processing fails"""
    pass


class PlanningError(BeverlyKnitsException):
    """Raised when planning process fails"""
    pass


class ConfigurationError(BeverlyKnitsException):
    """Raised when configuration is invalid"""
    pass