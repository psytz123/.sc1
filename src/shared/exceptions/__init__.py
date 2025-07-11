"""
Shared Exception Classes for Beverly Knits Supply Chain Management

This module defines the custom exception hierarchy for the application.
"""

from typing import Dict, Any, Optional, List


class BeverlyKnitsException(Exception):
    """Base exception class for Beverly Knits application"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(BeverlyKnitsException):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, List[str]]] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field_errors = field_errors or {}


class DataNotFoundError(BeverlyKnitsException):
    """Exception raised when required data is not found"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        super().__init__(message, "DATA_NOT_FOUND")
        self.resource_type = resource_type
        self.resource_id = resource_id


class PlanningError(BeverlyKnitsException):
    """Exception raised for planning execution errors"""
    
    def __init__(self, message: str, execution_id: Optional[str] = None):
        super().__init__(message, "PLANNING_ERROR")
        self.execution_id = execution_id


class BOMError(BeverlyKnitsException):
    """Exception raised for BOM-related errors"""
    
    def __init__(self, message: str, sku_id: Optional[str] = None):
        super().__init__(message, "BOM_ERROR")
        self.sku_id = sku_id


class InventoryError(BeverlyKnitsException):
    """Exception raised for inventory-related errors"""
    
    def __init__(self, message: str, material_id: Optional[str] = None):
        super().__init__(message, "INVENTORY_ERROR")
        self.material_id = material_id


class SupplierError(BeverlyKnitsException):
    """Exception raised for supplier-related errors"""
    
    def __init__(self, message: str, supplier_id: Optional[str] = None):
        super().__init__(message, "SUPPLIER_ERROR")
        self.supplier_id = supplier_id


class ConfigurationError(BeverlyKnitsException):
    """Exception raised for configuration errors"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key


class IntegrationError(BeverlyKnitsException):
    """Exception raised for external system integration errors"""
    
    def __init__(self, message: str, system_name: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, "INTEGRATION_ERROR")
        self.system_name = system_name
        self.operation = operation


class CacheError(BeverlyKnitsException):
    """Exception raised for cache-related errors"""
    
    def __init__(self, message: str, cache_key: Optional[str] = None):
        super().__init__(message, "CACHE_ERROR")
        self.cache_key = cache_key


class NotificationError(BeverlyKnitsException):
    """Exception raised for notification errors"""
    
    def __init__(self, message: str, notification_type: Optional[str] = None):
        super().__init__(message, "NOTIFICATION_ERROR")
        self.notification_type = notification_type


class AuthorizationError(BeverlyKnitsException):
    """Exception raised for authorization errors"""
    
    def __init__(self, message: str, user_id: Optional[str] = None, resource: Optional[str] = None):
        super().__init__(message, "AUTHORIZATION_ERROR")
        self.user_id = user_id
        self.resource = resource


class RateLimitError(BeverlyKnitsException):
    """Exception raised when rate limits are exceeded"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, "RATE_LIMIT_ERROR")
        self.retry_after = retry_after


class ExternalServiceError(BeverlyKnitsException):
    """Exception raised for external service errors"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.service_name = service_name
        self.status_code = status_code


class FileLoadError(BeverlyKnitsException):
    """Exception raised for file loading errors"""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message, "FILE_LOAD_ERROR")
        self.file_path = file_path


class DataIntegrityError(BeverlyKnitsException):
    """Exception raised for data integrity violations"""
    
    def __init__(self, message: str, constraint: Optional[str] = None):
        super().__init__(message, "DATA_INTEGRITY_ERROR")
        self.constraint = constraint


class OptimizationError(BeverlyKnitsException):
    """Exception raised for optimization algorithm errors"""
    
    def __init__(self, message: str, algorithm: Optional[str] = None):
        super().__init__(message, "OPTIMIZATION_ERROR")
        self.algorithm = algorithm


class ForecastError(BeverlyKnitsException):
    """Exception raised for forecasting errors"""
    
    def __init__(self, message: str, sku_id: Optional[str] = None, forecast_type: Optional[str] = None):
        super().__init__(message, "FORECAST_ERROR")
        self.sku_id = sku_id
        self.forecast_type = forecast_type


class UnitConversionError(BeverlyKnitsException):
    """Exception raised for unit conversion errors"""
    
    def __init__(self, message: str, from_unit: Optional[str] = None, to_unit: Optional[str] = None):
        super().__init__(message, "UNIT_CONVERSION_ERROR")
        self.from_unit = from_unit
        self.to_unit = to_unit


class ReportingError(BeverlyKnitsException):
    """Exception raised for reporting errors"""
    
    def __init__(self, message: str, report_type: Optional[str] = None):
        super().__init__(message, "REPORTING_ERROR")
        self.report_type = report_type


# Export all exception classes
__all__ = [
    'BeverlyKnitsException',
    'ValidationError',
    'DataNotFoundError',
    'PlanningError',
    'BOMError',
    'InventoryError',
    'SupplierError',
    'ConfigurationError',
    'IntegrationError',
    'CacheError',
    'NotificationError',
    'AuthorizationError',
    'RateLimitError',
    'ExternalServiceError',
    'FileLoadError',
    'DataIntegrityError',
    'OptimizationError',
    'ForecastError',
    'UnitConversionError',
    'ReportingError'
]