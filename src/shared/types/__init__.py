"""
Shared Type Definitions for Beverly Knits Supply Chain Management

This module provides common type definitions and type aliases
used throughout the application.
"""

from typing import Dict, List, Optional, Union, Any, Tuple, TypeVar, Generic, Protocol
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum

# Type variables for generics
T = TypeVar('T')
ID = TypeVar('ID')

# Common type aliases
JsonDict = Dict[str, Any]
JsonList = List[Any]
JsonValue = Union[str, int, float, bool, None, JsonDict, JsonList]

# Date/Time types
DateRange = Tuple[date, date]
DateTimeRange = Tuple[datetime, datetime]

# Quantity and Money types
QuantityDict = Dict[str, Union[Decimal, float]]
MoneyDict = Dict[str, Union[Decimal, float]]

# Planning types
PlanningConfig = Dict[str, Any]
RequirementDict = Dict[str, Any]
RecommendationDict = Dict[str, Any]

# Cache types
CacheKey = str
CacheValue = Any

# File types
FilePath = str
FileContent = Union[str, bytes]

# Database types
DatabaseRow = Dict[str, Any]
DatabaseResult = List[DatabaseRow]

# API types
APIResponse = Dict[str, Any]
APIError = Dict[str, Any]

# Event types
EventData = Dict[str, Any]
EventType = str

# Validation types
ValidationResult = Tuple[bool, List[str]]
ValidationErrors = Dict[str, List[str]]

# Pagination types
PageInfo = Dict[str, Union[int, bool]]
PaginatedResult = Tuple[List[T], PageInfo]

# Filter types
FilterCriteria = Dict[str, Any]
SortCriteria = List[Tuple[str, str]]  # [(field, direction)]

# Notification types
NotificationChannelType = str
NotificationMessage = str

# Report types
ReportFormat = str
ReportData = bytes

# Configuration types
ConfigKey = str
ConfigValue = Any

# Integration types
IntegrationConfig = Dict[str, Any]
IntegrationResult = Dict[str, Any]

# Permission types
Permission = str
Role = str

# Audit types
AuditAction = str
AuditContext = Dict[str, Any]


class Priority(Enum):
    """Priority levels for various operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(Enum):
    """General status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStatus(Enum):
    """Status for processing operations"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class DataFormat(Enum):
    """Supported data formats"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    XML = "xml"
    PARQUET = "parquet"


class TimeGranularity(Enum):
    """Time granularity options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class AggregationMethod(Enum):
    """Methods for data aggregation"""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    MEDIAN = "median"


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"  # Time to live
    LRU = "lru"  # Least recently used
    FIFO = "fifo"  # First in, first out
    MANUAL = "manual"  # Manual invalidation


class SortDirection(Enum):
    """Sort direction options"""
    ASC = "asc"
    DESC = "desc"


class ComparisonOperator(Enum):
    """Comparison operators for filters"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"


class EntityState(Enum):
    """Entity state for tracking changes"""
    UNCHANGED = "unchanged"
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class ValidationSeverity(Enum):
    """Severity levels for validation messages"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# Protocol definitions for type checking
class Identifiable(Protocol):
    """Protocol for entities with an ID"""
    id: Any


class Timestamped(Protocol):
    """Protocol for entities with timestamps"""
    created_at: datetime
    updated_at: datetime


class Auditable(Protocol):
    """Protocol for auditable entities"""
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]


class Cacheable(Protocol):
    """Protocol for cacheable objects"""
    def get_cache_key(self) -> CacheKey:
        ...
    
    def get_cache_ttl(self) -> int:
        ...


class Serializable(Protocol):
    """Protocol for serializable objects"""
    def to_dict(self) -> JsonDict:
        ...
    
    @classmethod
    def from_dict(cls, data: JsonDict) -> 'Serializable':
        ...


class Validatable(Protocol):
    """Protocol for objects that can be validated"""
    def validate(self) -> ValidationResult:
        ...


class Comparable(Protocol):
    """Protocol for comparable objects"""
    def __lt__(self, other: Any) -> bool:
        ...
    
    def __le__(self, other: Any) -> bool:
        ...
    
    def __gt__(self, other: Any) -> bool:
        ...
    
    def __ge__(self, other: Any) -> bool:
        ...


class Filterable(Protocol):
    """Protocol for filterable objects"""
    def matches_filter(self, criteria: FilterCriteria) -> bool:
        ...


class Sortable(Protocol):
    """Protocol for sortable objects"""
    def get_sort_key(self, field: str) -> Any:
        ...


# Generic repository pattern types
class Repository(Protocol, Generic[T, ID]):
    """Generic repository protocol"""
    async def get_by_id(self, id: ID) -> Optional[T]:
        ...
    
    async def save(self, entity: T) -> T:
        ...
    
    async def delete(self, id: ID) -> bool:
        ...
    
    async def list_all(self) -> List[T]:
        ...


# Generic service pattern types
class Service(Protocol, Generic[T]):
    """Generic service protocol"""
    async def process(self, data: T) -> T:
        ...


# Generic use case pattern types
class UseCase(Protocol, Generic[T]):
    """Generic use case protocol"""
    async def execute(self, request: T) -> Any:
        ...


# Helper type functions
def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID"""
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def is_valid_email(value: str) -> bool:
    """Check if a string is a valid email address"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, value) is not None


def is_positive_number(value: Union[int, float, Decimal]) -> bool:
    """Check if a number is positive"""
    return value > 0


def is_valid_percentage(value: Union[int, float, Decimal]) -> bool:
    """Check if a number is a valid percentage (0-100)"""
    return 0 <= value <= 100


def is_valid_date_range(start: date, end: date) -> bool:
    """Check if a date range is valid"""
    return start <= end


def is_valid_datetime_range(start: datetime, end: datetime) -> bool:
    """Check if a datetime range is valid"""
    return start <= end


# Export all types and functions
__all__ = [
    # Type variables
    'T', 'ID',
    
    # Type aliases
    'JsonDict', 'JsonList', 'JsonValue',
    'DateRange', 'DateTimeRange',
    'QuantityDict', 'MoneyDict',
    'PlanningConfig', 'RequirementDict', 'RecommendationDict',
    'CacheKey', 'CacheValue',
    'FilePath', 'FileContent',
    'DatabaseRow', 'DatabaseResult',
    'APIResponse', 'APIError',
    'EventData', 'EventType',
    'ValidationResult', 'ValidationErrors',
    'PageInfo', 'PaginatedResult',
    'FilterCriteria', 'SortCriteria',
    'NotificationChannel', 'NotificationMessage',
    'ReportFormat', 'ReportData',
    'ConfigKey', 'ConfigValue',
    'IntegrationConfig', 'IntegrationResult',
    'Permission', 'Role',
    'AuditAction', 'AuditContext',
    
    # Enums
    'Priority', 'Status', 'ProcessingStatus', 'DataFormat',
    'TimeGranularity', 'AggregationMethod', 'NotificationChannel',
    'LogLevel', 'CacheStrategy', 'SortDirection',
    'ComparisonOperator', 'EntityState', 'ValidationSeverity',
    
    # Protocols
    'Identifiable', 'Timestamped', 'Auditable', 'Cacheable',
    'Serializable', 'Validatable', 'Comparable', 'Filterable',
    'Sortable', 'Repository', 'Service', 'UseCase',
    
    # Helper functions
    'is_valid_uuid', 'is_valid_email', 'is_positive_number',
    'is_valid_percentage', 'is_valid_date_range', 'is_valid_datetime_range'
]