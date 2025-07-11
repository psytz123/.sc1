"""
Service Interfaces for Beverly Knits Supply Chain Management

These interfaces define the contracts for domain services, external services,
and use case implementations following clean architecture principles.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from src.core.domain.entities import (
    Material, MaterialId, Supplier, SupplierId, MaterialSupplierRelation,
    Forecast, BillOfMaterial, Inventory, ProcurementRecommendation,
    ProcurementOrder, Quantity, Money, RiskLevel, ForecastSource
)


class UnitConversionService(ABC):
    """Service interface for unit conversions"""

    @abstractmethod
    async def convert_quantity(
        self, 
        quantity: Quantity, 
        target_unit: str,
        material_id: Optional[MaterialId] = None
    ) -> Quantity:
        """Convert quantity to target unit"""
        pass

    @abstractmethod
    async def get_supported_conversions(self, from_unit: str) -> List[str]:
        """Get list of supported target units for conversion"""
        pass

    @abstractmethod
    async def is_conversion_supported(self, from_unit: str, to_unit: str) -> bool:
        """Check if conversion is supported"""
        pass


class CacheService(ABC):
    """Service interface for caching operations"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expiration_seconds: int = 3600) -> None:
        """Set value in cache with expiration"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass


class NotificationService(ABC):
    """Service interface for notifications"""

    @abstractmethod
    async def send_email(
        self, 
        to: List[str], 
        subject: str, 
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email notification"""
        pass

    @abstractmethod
    async def send_slack_message(self, channel: str, message: str) -> bool:
        """Send Slack notification"""
        pass

    @abstractmethod
    async def send_procurement_alert(
        self, 
        recommendation: ProcurementRecommendation
    ) -> bool:
        """Send procurement alert notification"""
        pass

    @abstractmethod
    async def send_inventory_low_stock_alert(
        self, 
        inventory: Inventory
    ) -> bool:
        """Send low stock alert"""
        pass


class ReportingService(ABC):
    """Service interface for report generation"""

    @abstractmethod
    async def generate_procurement_report(
        self, 
        recommendations: List[ProcurementRecommendation],
        format: str = "pdf"
    ) -> bytes:
        """Generate procurement report"""
        pass

    @abstractmethod
    async def generate_inventory_report(
        self, 
        inventory_items: List[Inventory],
        format: str = "pdf"
    ) -> bytes:
        """Generate inventory report"""
        pass

    @abstractmethod
    async def generate_supplier_performance_report(
        self, 
        suppliers: List[Supplier],
        orders: List[ProcurementOrder],
        format: str = "pdf"
    ) -> bytes:
        """Generate supplier performance report"""
        pass

    @abstractmethod
    async def generate_executive_summary(
        self, 
        recommendations: List[ProcurementRecommendation],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate executive summary text"""
        pass


class ForecastingService(ABC):
    """Service interface for demand forecasting"""

    @abstractmethod
    async def generate_forecast_from_sales_history(
        self, 
        sku_id: str,
        lookback_days: int = 90,
        forecast_horizon_days: int = 90
    ) -> List[Forecast]:
        """Generate forecasts from sales history"""
        pass

    @abstractmethod
    async def unify_forecasts(
        self, 
        forecasts: List[Forecast],
        source_weights: Dict[ForecastSource, float]
    ) -> Dict[str, Quantity]:
        """Unify multiple forecasts with weights"""
        pass

    @abstractmethod
    async def validate_forecast_accuracy(
        self, 
        forecasts: List[Forecast],
        actual_demand: Dict[str, Quantity]
    ) -> Dict[str, float]:
        """Validate forecast accuracy against actual demand"""
        pass

    @abstractmethod
    async def adjust_forecast_for_seasonality(
        self, 
        forecast: Forecast,
        seasonal_factors: Dict[str, float]
    ) -> Forecast:
        """Adjust forecast for seasonal patterns"""
        pass


class BOMExplosionService(ABC):
    """Service interface for BOM explosion operations"""

    @abstractmethod
    async def explode_forecasts_to_materials(
        self, 
        sku_forecasts: Dict[str, Quantity],
        boms: List[BillOfMaterial]
    ) -> Dict[MaterialId, Dict[str, Any]]:
        """Explode SKU forecasts to material requirements"""
        pass

    @abstractmethod
    async def calculate_material_requirements(
        self, 
        production_plan: Dict[str, Quantity],
        boms: List[BillOfMaterial],
        include_safety_stock: bool = True
    ) -> Dict[MaterialId, Quantity]:
        """Calculate material requirements from production plan"""
        pass

    @abstractmethod
    async def validate_bom_completeness(
        self, 
        sku_ids: List[str],
        boms: List[BillOfMaterial]
    ) -> Dict[str, List[str]]:
        """Validate BOM completeness for SKUs"""
        pass


class InventoryService(ABC):
    """Service interface for inventory operations"""

    @abstractmethod
    async def calculate_net_requirements(
        self, 
        gross_requirements: Dict[MaterialId, Quantity],
        inventory_levels: List[Inventory]
    ) -> Dict[MaterialId, Dict[str, Any]]:
        """Calculate net requirements after inventory netting"""
        pass

    @abstractmethod
    async def calculate_safety_stock(
        self, 
        material_id: MaterialId,
        demand_history: List[Quantity],
        lead_time_days: int,
        service_level: float = 0.95
    ) -> Quantity:
        """Calculate safety stock using statistical methods"""
        pass

    @abstractmethod
    async def update_inventory_levels(
        self, 
        material_id: MaterialId,
        quantity_changes: Dict[str, Quantity]
    ) -> Inventory:
        """Update inventory levels"""
        pass

    @abstractmethod
    async def reserve_inventory(
        self, 
        material_id: MaterialId,
        quantity: Quantity,
        reservation_id: str
    ) -> bool:
        """Reserve inventory for production"""
        pass


class ProcurementOptimizationService(ABC):
    """Service interface for procurement optimization"""

    @abstractmethod
    async def calculate_economic_order_quantity(
        self, 
        material_id: MaterialId,
        annual_demand: Quantity,
        ordering_cost: Money,
        holding_cost_rate: float,
        unit_cost: Money
    ) -> Quantity:
        """Calculate Economic Order Quantity"""
        pass

    @abstractmethod
    async def optimize_supplier_selection(
        self, 
        material_id: MaterialId,
        required_quantity: Quantity,
        available_suppliers: List[MaterialSupplierRelation],
        cost_weight: float = 0.6,
        reliability_weight: float = 0.4
    ) -> List[Tuple[SupplierId, Quantity, Money]]:
        """Optimize supplier selection and allocation"""
        pass

    @abstractmethod
    async def calculate_total_cost_of_ownership(
        self, 
        material_id: MaterialId,
        supplier_id: SupplierId,
        quantity: Quantity,
        time_horizon_days: int = 365
    ) -> Money:
        """Calculate total cost of ownership"""
        pass

    @abstractmethod
    async def optimize_order_timing(
        self, 
        material_id: MaterialId,
        demand_forecast: List[Quantity],
        lead_time_days: int,
        inventory_level: Quantity
    ) -> List[Tuple[date, Quantity]]:
        """Optimize order timing and quantities"""
        pass


class RiskAssessmentService(ABC):
    """Service interface for risk assessment"""

    @abstractmethod
    async def assess_supplier_risk(
        self, 
        supplier_id: SupplierId,
        material_id: MaterialId,
        order_quantity: Quantity
    ) -> RiskLevel:
        """Assess risk level for supplier and material combination"""
        pass

    @abstractmethod
    async def assess_inventory_risk(
        self, 
        material_id: MaterialId,
        current_inventory: Inventory,
        demand_forecast: List[Quantity]
    ) -> RiskLevel:
        """Assess inventory risk level"""
        pass

    @abstractmethod
    async def assess_lead_time_risk(
        self, 
        supplier_id: SupplierId,
        material_id: MaterialId,
        historical_lead_times: List[int]
    ) -> RiskLevel:
        """Assess lead time risk"""
        pass

    @abstractmethod
    async def generate_risk_mitigation_recommendations(
        self, 
        risk_level: RiskLevel,
        material_id: MaterialId,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        pass


class PlanningEngine(ABC):
    """Main planning engine interface"""

    @abstractmethod
    async def execute_planning_cycle(
        self, 
        planning_config: Dict[str, Any]
    ) -> List[ProcurementRecommendation]:
        """Execute complete planning cycle"""
        pass

    @abstractmethod
    async def validate_planning_inputs(
        self, 
        forecasts: List[Forecast],
        boms: List[BillOfMaterial],
        inventory: List[Inventory],
        suppliers: List[MaterialSupplierRelation]
    ) -> Dict[str, List[str]]:
        """Validate planning inputs"""
        pass

    @abstractmethod
    async def generate_procurement_recommendations(
        self, 
        net_requirements: Dict[MaterialId, Dict[str, Any]],
        supplier_relations: List[MaterialSupplierRelation],
        planning_config: Dict[str, Any]
    ) -> List[ProcurementRecommendation]:
        """Generate procurement recommendations"""
        pass


class ExternalDataService(ABC):
    """Service interface for external data sources"""

    @abstractmethod
    async def fetch_supplier_catalog(self, supplier_id: SupplierId) -> Dict[str, Any]:
        """Fetch supplier catalog data"""
        pass

    @abstractmethod
    async def fetch_market_prices(self, material_id: MaterialId) -> Dict[str, Money]:
        """Fetch current market prices"""
        pass

    @abstractmethod
    async def fetch_weather_data(self, location: str) -> Dict[str, Any]:
        """Fetch weather data for planning"""
        pass

    @abstractmethod
    async def fetch_economic_indicators(self) -> Dict[str, float]:
        """Fetch economic indicators"""
        pass


class AuditService(ABC):
    """Service interface for audit logging"""

    @abstractmethod
    async def log_planning_execution(
        self, 
        execution_id: UUID,
        input_data: Dict[str, Any],
        output_data: List[ProcurementRecommendation],
        execution_time: float
    ) -> None:
        """Log planning execution"""
        pass

    @abstractmethod
    async def log_supplier_selection(
        self, 
        material_id: MaterialId,
        selected_supplier: SupplierId,
        alternatives: List[SupplierId],
        selection_criteria: Dict[str, Any]
    ) -> None:
        """Log supplier selection decision"""
        pass

    @abstractmethod
    async def log_recommendation_approval(
        self, 
        recommendation_id: UUID,
        approved_by: str,
        approval_timestamp: datetime,
        modifications: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log recommendation approval"""
        pass

    @abstractmethod
    async def get_audit_trail(
        self, 
        entity_type: str,
        entity_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get audit trail for entity"""
        pass


class ConfigurationService(ABC):
    """Service interface for configuration management"""

    @abstractmethod
    async def get_planning_config(self) -> Dict[str, Any]:
        """Get current planning configuration"""
        pass

    @abstractmethod
    async def update_planning_config(self, config: Dict[str, Any]) -> None:
        """Update planning configuration"""
        pass

    @abstractmethod
    async def get_business_rules(self) -> Dict[str, Any]:
        """Get business rules configuration"""
        pass

    @abstractmethod
    async def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration"""
        pass


class IntegrationService(ABC):
    """Service interface for external system integrations"""

    @abstractmethod
    async def sync_with_erp(self) -> Dict[str, Any]:
        """Synchronize data with ERP system"""
        pass

    @abstractmethod
    async def export_to_procurement_system(
        self, 
        recommendations: List[ProcurementRecommendation]
    ) -> bool:
        """Export recommendations to procurement system"""
        pass

    @abstractmethod
    async def import_inventory_updates(self) -> List[Inventory]:
        """Import inventory updates from external systems"""
        pass

    @abstractmethod
    async def sync_supplier_data(self) -> List[Supplier]:
        """Sync supplier data from external systems"""
        pass