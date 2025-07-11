"""
Repository Interfaces for Beverly Knits Supply Chain Management

These interfaces define the contracts for data access operations,
following the Repository pattern for clean architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID

from src.core.domain.entities import (
    Material, MaterialId, Supplier, SupplierId, MaterialSupplierRelation,
    Forecast, BillOfMaterial, Inventory, ProcurementRecommendation,
    ProcurementOrder, ForecastSource, OrderStatus, RiskLevel
)


class MaterialRepository(ABC):
    """Repository interface for material operations"""

    @abstractmethod
    async def save(self, material: Material) -> Material:
        """Save a material entity"""
        pass

    @abstractmethod
    async def get_by_id(self, material_id: MaterialId) -> Optional[Material]:
        """Get material by ID"""
        pass

    @abstractmethod
    async def get_by_ids(self, material_ids: List[MaterialId]) -> List[Material]:
        """Get materials by multiple IDs"""
        pass

    @abstractmethod
    async def get_all(self) -> List[Material]:
        """Get all materials"""
        pass

    @abstractmethod
    async def get_by_type(self, material_type: str) -> List[Material]:
        """Get materials by type"""
        pass

    @abstractmethod
    async def get_critical_materials(self) -> List[Material]:
        """Get all critical materials"""
        pass

    @abstractmethod
    async def search_by_name(self, name_pattern: str) -> List[Material]:
        """Search materials by name pattern"""
        pass

    @abstractmethod
    async def delete(self, material_id: MaterialId) -> bool:
        """Delete a material"""
        pass

    @abstractmethod
    async def exists(self, material_id: MaterialId) -> bool:
        """Check if material exists"""
        pass


class SupplierRepository(ABC):
    """Repository interface for supplier operations"""

    @abstractmethod
    async def save(self, supplier: Supplier) -> Supplier:
        """Save a supplier entity"""
        pass

    @abstractmethod
    async def get_by_id(self, supplier_id: SupplierId) -> Optional[Supplier]:
        """Get supplier by ID"""
        pass

    @abstractmethod
    async def get_by_ids(self, supplier_ids: List[SupplierId]) -> List[Supplier]:
        """Get suppliers by multiple IDs"""
        pass

    @abstractmethod
    async def get_all(self) -> List[Supplier]:
        """Get all suppliers"""
        pass

    @abstractmethod
    async def get_active_suppliers(self) -> List[Supplier]:
        """Get all active suppliers"""
        pass

    @abstractmethod
    async def get_by_reliability_threshold(self, min_reliability: float) -> List[Supplier]:
        """Get suppliers above reliability threshold"""
        pass

    @abstractmethod
    async def search_by_name(self, name_pattern: str) -> List[Supplier]:
        """Search suppliers by name pattern"""
        pass

    @abstractmethod
    async def delete(self, supplier_id: SupplierId) -> bool:
        """Delete a supplier"""
        pass

    @abstractmethod
    async def exists(self, supplier_id: SupplierId) -> bool:
        """Check if supplier exists"""
        pass


class MaterialSupplierRepository(ABC):
    """Repository interface for material-supplier relationships"""

    @abstractmethod
    async def save(self, relation: MaterialSupplierRelation) -> MaterialSupplierRelation:
        """Save a material-supplier relationship"""
        pass

    @abstractmethod
    async def get_by_material_id(self, material_id: MaterialId) -> List[MaterialSupplierRelation]:
        """Get all supplier relationships for a material"""
        pass

    @abstractmethod
    async def get_by_supplier_id(self, supplier_id: SupplierId) -> List[MaterialSupplierRelation]:
        """Get all material relationships for a supplier"""
        pass

    @abstractmethod
    async def get_by_material_and_supplier(
        self, 
        material_id: MaterialId, 
        supplier_id: SupplierId
    ) -> Optional[MaterialSupplierRelation]:
        """Get specific material-supplier relationship"""
        pass

    @abstractmethod
    async def get_active_relations(self) -> List[MaterialSupplierRelation]:
        """Get all active material-supplier relationships"""
        pass

    @abstractmethod
    async def get_by_lead_time_threshold(self, max_lead_time: int) -> List[MaterialSupplierRelation]:
        """Get relationships with lead time below threshold"""
        pass

    @abstractmethod
    async def delete(self, material_id: MaterialId, supplier_id: SupplierId) -> bool:
        """Delete a material-supplier relationship"""
        pass


class ForecastRepository(ABC):
    """Repository interface for forecast operations"""

    @abstractmethod
    async def save(self, forecast: Forecast) -> Forecast:
        """Save a forecast entity"""
        pass

    @abstractmethod
    async def save_batch(self, forecasts: List[Forecast]) -> List[Forecast]:
        """Save multiple forecasts in batch"""
        pass

    @abstractmethod
    async def get_by_id(self, forecast_id: UUID) -> Optional[Forecast]:
        """Get forecast by ID"""
        pass

    @abstractmethod
    async def get_by_sku_id(self, sku_id: str) -> List[Forecast]:
        """Get forecasts for a specific SKU"""
        pass

    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[Forecast]:
        """Get forecasts within date range"""
        pass

    @abstractmethod
    async def get_by_source(self, source: ForecastSource) -> List[Forecast]:
        """Get forecasts by source"""
        pass

    @abstractmethod
    async def get_recent_forecasts(self, days: int = 30) -> List[Forecast]:
        """Get recent forecasts within specified days"""
        pass

    @abstractmethod
    async def get_by_confidence_threshold(self, min_confidence: float) -> List[Forecast]:
        """Get forecasts above confidence threshold"""
        pass

    @abstractmethod
    async def delete(self, forecast_id: UUID) -> bool:
        """Delete a forecast"""
        pass

    @abstractmethod
    async def delete_by_sku_id(self, sku_id: str) -> int:
        """Delete all forecasts for a SKU, return count deleted"""
        pass


class BillOfMaterialRepository(ABC):
    """Repository interface for BOM operations"""

    @abstractmethod
    async def save(self, bom: BillOfMaterial) -> BillOfMaterial:
        """Save a BOM entry"""
        pass

    @abstractmethod
    async def save_batch(self, boms: List[BillOfMaterial]) -> List[BillOfMaterial]:
        """Save multiple BOM entries in batch"""
        pass

    @abstractmethod
    async def get_by_sku_id(self, sku_id: str) -> List[BillOfMaterial]:
        """Get BOM entries for a specific SKU"""
        pass

    @abstractmethod
    async def get_by_material_id(self, material_id: MaterialId) -> List[BillOfMaterial]:
        """Get BOM entries for a specific material"""
        pass

    @abstractmethod
    async def get_effective_boms(self, reference_date: Optional[date] = None) -> List[BillOfMaterial]:
        """Get all effective BOM entries for a date (defaults to today)"""
        pass

    @abstractmethod
    async def get_critical_boms(self) -> List[BillOfMaterial]:
        """Get BOM entries for critical components"""
        pass

    @abstractmethod
    async def delete(self, sku_id: str, material_id: MaterialId) -> bool:
        """Delete a BOM entry"""
        pass

    @abstractmethod
    async def delete_by_sku_id(self, sku_id: str) -> int:
        """Delete all BOM entries for a SKU, return count deleted"""
        pass


class InventoryRepository(ABC):
    """Repository interface for inventory operations"""

    @abstractmethod
    async def save(self, inventory: Inventory) -> Inventory:
        """Save an inventory record"""
        pass

    @abstractmethod
    async def get_by_material_id(self, material_id: MaterialId) -> Optional[Inventory]:
        """Get inventory for a specific material"""
        pass

    @abstractmethod
    async def get_by_material_ids(self, material_ids: List[MaterialId]) -> List[Inventory]:
        """Get inventory for multiple materials"""
        pass

    @abstractmethod
    async def get_all(self) -> List[Inventory]:
        """Get all inventory records"""
        pass

    @abstractmethod
    async def get_below_reorder_point(self) -> List[Inventory]:
        """Get inventory items below reorder point"""
        pass

    @abstractmethod
    async def get_below_safety_stock(self) -> List[Inventory]:
        """Get inventory items below safety stock"""
        pass

    @abstractmethod
    async def get_by_location(self, location: str) -> List[Inventory]:
        """Get inventory by location"""
        pass

    @abstractmethod
    async def update_quantities(
        self, 
        material_id: MaterialId, 
        quantity_changes: Dict[str, float]
    ) -> Inventory:
        """Update inventory quantities (on_hand, available, reserved)"""
        pass

    @abstractmethod
    async def delete(self, material_id: MaterialId) -> bool:
        """Delete an inventory record"""
        pass


class ProcurementRecommendationRepository(ABC):
    """Repository interface for procurement recommendation operations"""

    @abstractmethod
    async def save(self, recommendation: ProcurementRecommendation) -> ProcurementRecommendation:
        """Save a procurement recommendation"""
        pass

    @abstractmethod
    async def save_batch(self, recommendations: List[ProcurementRecommendation]) -> List[ProcurementRecommendation]:
        """Save multiple recommendations in batch"""
        pass

    @abstractmethod
    async def get_by_id(self, recommendation_id: UUID) -> Optional[ProcurementRecommendation]:
        """Get recommendation by ID"""
        pass

    @abstractmethod
    async def get_by_material_id(self, material_id: MaterialId) -> List[ProcurementRecommendation]:
        """Get recommendations for a specific material"""
        pass

    @abstractmethod
    async def get_by_supplier_id(self, supplier_id: SupplierId) -> List[ProcurementRecommendation]:
        """Get recommendations for a specific supplier"""
        pass

    @abstractmethod
    async def get_by_risk_level(self, risk_level: RiskLevel) -> List[ProcurementRecommendation]:
        """Get recommendations by risk level"""
        pass

    @abstractmethod
    async def get_by_urgency_threshold(self, min_urgency: float) -> List[ProcurementRecommendation]:
        """Get recommendations above urgency threshold"""
        pass

    @abstractmethod
    async def get_active_recommendations(self) -> List[ProcurementRecommendation]:
        """Get all non-expired recommendations"""
        pass

    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[ProcurementRecommendation]:
        """Get recommendations within date range"""
        pass

    @abstractmethod
    async def delete(self, recommendation_id: UUID) -> bool:
        """Delete a recommendation"""
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete all expired recommendations, return count deleted"""
        pass


class ProcurementOrderRepository(ABC):
    """Repository interface for procurement order operations"""

    @abstractmethod
    async def save(self, order: ProcurementOrder) -> ProcurementOrder:
        """Save a procurement order"""
        pass

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Optional[ProcurementOrder]:
        """Get order by ID"""
        pass

    @abstractmethod
    async def get_by_material_id(self, material_id: MaterialId) -> List[ProcurementOrder]:
        """Get orders for a specific material"""
        pass

    @abstractmethod
    async def get_by_supplier_id(self, supplier_id: SupplierId) -> List[ProcurementOrder]:
        """Get orders for a specific supplier"""
        pass

    @abstractmethod
    async def get_by_status(self, status: OrderStatus) -> List[ProcurementOrder]:
        """Get orders by status"""
        pass

    @abstractmethod
    async def get_by_po_number(self, po_number: str) -> Optional[ProcurementOrder]:
        """Get order by purchase order number"""
        pass

    @abstractmethod
    async def get_overdue_orders(self) -> List[ProcurementOrder]:
        """Get all overdue orders"""
        pass

    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[ProcurementOrder]:
        """Get orders within date range"""
        pass

    @abstractmethod
    async def get_pending_orders(self) -> List[ProcurementOrder]:
        """Get all pending orders"""
        pass

    @abstractmethod
    async def delete(self, order_id: UUID) -> bool:
        """Delete an order"""
        pass

    @abstractmethod
    async def get_orders_for_delivery_tracking(self) -> List[ProcurementOrder]:
        """Get orders that need delivery tracking (shipped but not delivered)"""
        pass


class UnitOfWork(ABC):
    """Unit of Work interface for transaction management"""

    @abstractmethod
    async def __aenter__(self):
        """Enter async context manager"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager"""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction"""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction"""
        pass

    @property
    @abstractmethod
    def materials(self) -> MaterialRepository:
        """Get materials repository"""
        pass

    @property
    @abstractmethod
    def suppliers(self) -> SupplierRepository:
        """Get suppliers repository"""
        pass

    @property
    @abstractmethod
    def material_suppliers(self) -> MaterialSupplierRepository:
        """Get material-supplier relationships repository"""
        pass

    @property
    @abstractmethod
    def forecasts(self) -> ForecastRepository:
        """Get forecasts repository"""
        pass

    @property
    @abstractmethod
    def boms(self) -> BillOfMaterialRepository:
        """Get BOM repository"""
        pass

    @property
    @abstractmethod
    def inventory(self) -> InventoryRepository:
        """Get inventory repository"""
        pass

    @property
    @abstractmethod
    def recommendations(self) -> ProcurementRecommendationRepository:
        """Get procurement recommendations repository"""
        pass

    @property
    @abstractmethod
    def orders(self) -> ProcurementOrderRepository:
        """Get procurement orders repository"""
        pass