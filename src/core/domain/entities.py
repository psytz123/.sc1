"""
Core Domain Entities for Beverly Knits Supply Chain Management

These entities represent the core business objects with clean interfaces
and proper encapsulation of business rules.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4


class MaterialType(Enum):
    """Types of materials in the supply chain"""
    YARN = "yarn"
    FABRIC = "fabric"
    ACCESSORY = "accessory"
    TRIM = "trim"
    PACKAGING = "packaging"


class ForecastSource(Enum):
    """Sources of demand forecasts"""
    SALES_ORDER = "sales_order"
    PRODUCTION_PLAN = "prod_plan"
    PROJECTION = "projection"
    SALES_HISTORY = "sales_history"


class RiskLevel(Enum):
    """Risk levels for procurement decisions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OrderStatus(Enum):
    """Status of procurement orders"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class MaterialId:
    """Value object for material identification"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Material ID cannot be empty")
        object.__setattr__(self, 'value', self.value.strip().upper())


@dataclass(frozen=True)
class SupplierId:
    """Value object for supplier identification"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Supplier ID cannot be empty")
        object.__setattr__(self, 'value', self.value.strip().upper())


@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-character code")
        object.__setattr__(self, 'currency', self.currency.upper())
    
    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def __mul__(self, multiplier: Union[int, float, Decimal]) -> 'Money':
        return Money(self.amount * Decimal(str(multiplier)), self.currency)


@dataclass(frozen=True)
class Quantity:
    """Value object for quantities with units"""
    amount: Decimal
    unit: str
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Quantity amount cannot be negative")
        if not self.unit or not self.unit.strip():
            raise ValueError("Unit cannot be empty")
        object.__setattr__(self, 'unit', self.unit.strip().lower())
    
    def __add__(self, other: 'Quantity') -> 'Quantity':
        if self.unit != other.unit:
            raise ValueError(f"Cannot add different units: {self.unit} and {other.unit}")
        return Quantity(self.amount + other.amount, self.unit)
    
    def __mul__(self, multiplier: Union[int, float, Decimal]) -> 'Quantity':
        return Quantity(self.amount * Decimal(str(multiplier)), self.unit)


@dataclass
class Material:
    """Core material entity"""
    id: MaterialId
    name: str
    type: MaterialType
    description: Optional[str] = None
    specifications: Optional[Dict[str, str]] = None
    is_critical: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def update_specifications(self, specifications: Dict[str, str]) -> None:
        """Update material specifications"""
        self.specifications = specifications.copy() if specifications else {}
        self.updated_at = datetime.now()
    
    def mark_as_critical(self) -> None:
        """Mark material as critical"""
        self.is_critical = True
        self.updated_at = datetime.now()


@dataclass
class Supplier:
    """Core supplier entity"""
    id: SupplierId
    name: str
    contact_info: Dict[str, str]
    reliability_score: float = 1.0
    preferred_payment_terms: str = "NET30"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not 0 <= self.reliability_score <= 1:
            raise ValueError("Reliability score must be between 0 and 1")
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def update_reliability_score(self, score: float) -> None:
        """Update supplier reliability score"""
        if not 0 <= score <= 1:
            raise ValueError("Reliability score must be between 0 and 1")
        self.reliability_score = score
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Deactivate supplier"""
        self.is_active = False
        self.updated_at = datetime.now()


@dataclass
class MaterialSupplierRelation:
    """Relationship between material and supplier with terms"""
    material_id: MaterialId
    supplier_id: SupplierId
    cost_per_unit: Money
    lead_time_days: int
    minimum_order_quantity: Quantity
    maximum_order_quantity: Optional[Quantity] = None
    ordering_cost: Money = Money(Decimal("100.00"))
    holding_cost_rate: float = 0.2
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.lead_time_days < 0:
            raise ValueError("Lead time cannot be negative")
        if not 0 <= self.holding_cost_rate <= 1:
            raise ValueError("Holding cost rate must be between 0 and 1")
        if (self.contract_start_date and self.contract_end_date and 
            self.contract_start_date > self.contract_end_date):
            raise ValueError("Contract start date cannot be after end date")
    
    def is_contract_active(self) -> bool:
        """Check if contract is currently active"""
        if not self.is_active:
            return False
        
        today = date.today()
        if self.contract_start_date and today < self.contract_start_date:
            return False
        if self.contract_end_date and today > self.contract_end_date:
            return False
        
        return True
    
    def calculate_total_cost(self, quantity: Quantity) -> Money:
        """Calculate total cost for given quantity"""
        if self.cost_per_unit.currency != quantity.unit:
            # This should be handled by a unit conversion service
            raise ValueError(f"Unit mismatch: {self.cost_per_unit.currency} vs {quantity.unit}")
        
        return self.cost_per_unit * quantity.amount


@dataclass
class Forecast:
    """Demand forecast entity"""
    id: UUID
    sku_id: str
    forecast_quantity: Quantity
    forecast_date: date
    source: ForecastSource
    confidence_level: float = 0.8
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if not 0 <= self.confidence_level <= 1:
            raise ValueError("Confidence level must be between 0 and 1")
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def adjust_confidence(self, new_confidence: float) -> None:
        """Adjust forecast confidence level"""
        if not 0 <= new_confidence <= 1:
            raise ValueError("Confidence level must be between 0 and 1")
        self.confidence_level = new_confidence
    
    def get_weighted_quantity(self) -> Quantity:
        """Get quantity adjusted by confidence level"""
        return self.forecast_quantity * self.confidence_level


@dataclass
class BillOfMaterial:
    """Bill of Materials relationship"""
    sku_id: str
    material_id: MaterialId
    quantity_per_unit: Quantity
    percentage: Optional[float] = None
    is_critical_component: bool = False
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    
    def __post_init__(self):
        if self.percentage is not None:
            if not 0 <= self.percentage <= 100:
                raise ValueError("Percentage must be between 0 and 100")
    
    def is_effective(self) -> bool:
        """Check if BOM relationship is currently effective"""
        today = date.today()
        if self.effective_date and today < self.effective_date:
            return False
        if self.expiry_date and today > self.expiry_date:
            return False
        return True
    
    def calculate_material_requirement(self, sku_quantity: Quantity) -> Quantity:
        """Calculate material requirement for given SKU quantity"""
        if self.percentage is not None:
            # Percentage-based calculation
            multiplier = Decimal(str(self.percentage / 100))
            return sku_quantity * multiplier
        else:
            # Direct quantity calculation
            return self.quantity_per_unit * sku_quantity.amount


@dataclass
class Inventory:
    """Inventory entity"""
    material_id: MaterialId
    on_hand_quantity: Quantity
    available_quantity: Quantity
    reserved_quantity: Quantity
    safety_stock_quantity: Quantity
    reorder_point: Quantity
    last_updated: Optional[datetime] = None
    location: Optional[str] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def reserve_quantity(self, quantity: Quantity) -> None:
        """Reserve inventory quantity"""
        if quantity.unit != self.available_quantity.unit:
            raise ValueError(f"Unit mismatch: {quantity.unit} vs {self.available_quantity.unit}")
        
        if quantity.amount > self.available_quantity.amount:
            raise ValueError("Cannot reserve more than available quantity")
        
        self.available_quantity = Quantity(
            self.available_quantity.amount - quantity.amount,
            self.available_quantity.unit
        )
        self.reserved_quantity = self.reserved_quantity + quantity
        self.last_updated = datetime.now()
    
    def is_below_reorder_point(self) -> bool:
        """Check if inventory is below reorder point"""
        return self.available_quantity.amount <= self.reorder_point.amount
    
    def is_below_safety_stock(self) -> bool:
        """Check if inventory is below safety stock"""
        return self.available_quantity.amount <= self.safety_stock_quantity.amount


@dataclass
class ProcurementRecommendation:
    """Procurement recommendation entity"""
    id: UUID
    material_id: MaterialId
    supplier_id: SupplierId
    recommended_quantity: Quantity
    estimated_cost: Money
    recommended_order_date: date
    expected_delivery_date: date
    risk_level: RiskLevel
    urgency_score: float
    reasoning: str
    eoq_quantity: Optional[Quantity] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if not 0 <= self.urgency_score <= 1:
            raise ValueError("Urgency score must be between 0 and 1")
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.recommended_order_date > self.expected_delivery_date:
            raise ValueError("Order date cannot be after delivery date")
    
    def is_expired(self) -> bool:
        """Check if recommendation has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def calculate_cost_per_unit(self) -> Money:
        """Calculate cost per unit"""
        if self.recommended_quantity.amount == 0:
            return Money(Decimal("0"))
        
        return Money(
            self.estimated_cost.amount / self.recommended_quantity.amount,
            self.estimated_cost.currency
        )
    
    def update_risk_level(self, risk_level: RiskLevel, reasoning: str) -> None:
        """Update risk level and reasoning"""
        self.risk_level = risk_level
        self.reasoning = reasoning
        # Note: In a real system, this would trigger domain events


@dataclass
class ProcurementOrder:
    """Procurement order entity"""
    id: UUID
    material_id: MaterialId
    supplier_id: SupplierId
    order_quantity: Quantity
    unit_cost: Money
    total_cost: Money
    order_date: date
    expected_delivery_date: date
    actual_delivery_date: Optional[date] = None
    status: OrderStatus = OrderStatus.PENDING
    purchase_order_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def confirm_order(self, po_number: str) -> None:
        """Confirm the order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order with status: {self.status}")
        
        self.status = OrderStatus.CONFIRMED
        self.purchase_order_number = po_number
        self.updated_at = datetime.now()
    
    def ship_order(self) -> None:
        """Mark order as shipped"""
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError(f"Cannot ship order with status: {self.status}")
        
        self.status = OrderStatus.SHIPPED
        self.updated_at = datetime.now()
    
    def deliver_order(self, delivery_date: date) -> None:
        """Mark order as delivered"""
        if self.status != OrderStatus.SHIPPED:
            raise ValueError(f"Cannot deliver order with status: {self.status}")
        
        self.status = OrderStatus.DELIVERED
        self.actual_delivery_date = delivery_date
        self.updated_at = datetime.now()
    
    def cancel_order(self, reason: str) -> None:
        """Cancel the order"""
        if self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel order with status: {self.status}")
        
        self.status = OrderStatus.CANCELLED
        self.notes = f"Cancelled: {reason}"
        self.updated_at = datetime.now()
    
    def is_overdue(self) -> bool:
        """Check if order is overdue"""
        if self.status == OrderStatus.DELIVERED:
            return False
        
        return date.today() > self.expected_delivery_date
    
    def calculate_lead_time_variance(self) -> Optional[int]:
        """Calculate lead time variance in days"""
        if self.actual_delivery_date is None:
            return None
        
        expected_lead_time = (self.expected_delivery_date - self.order_date).days
        actual_lead_time = (self.actual_delivery_date - self.order_date).days
        
        return actual_lead_time - expected_lead_time