# Beverly Knits Refactored Architecture Usage Guide

## Overview
This guide demonstrates how to use the newly refactored Beverly Knits architecture, showing practical examples of working with the clean architecture components.

## Architecture Overview

```
User Interface → Use Cases → Domain Services → Repositories → Database
     ↓              ↓            ↓               ↓
Presentation → Application → Domain Layer → Infrastructure
```

## Key Components

### 1. Domain Entities
Rich business objects with validation and business rules.

```python
from decimal import Decimal
from src.core.domain.entities import Material, MaterialId, MaterialType, Money, Quantity

# Create a material with proper validation
material = Material(
    id=MaterialId("YARN-001"),
    name="Premium Cotton Yarn",
    type=MaterialType.YARN,
    description="High-quality cotton yarn for premium garments",
    is_critical=True
)

# Update specifications
material.update_specifications({
    "weight": "200g",
    "color": "natural",
    "fiber_content": "100% cotton"
})
```

### 2. Value Objects
Type-safe representations of values with validation.

```python
from src.core.domain.entities import Money, Quantity

# Create money with validation
price = Money(Decimal("15.50"), "USD")

# Create quantity with validation
quantity = Quantity(Decimal("100"), "yards")

# Value objects are immutable and comparable
total_cost = price * quantity.amount  # Money(1550.00, "USD")
```

### 3. Repository Pattern
Clean data access through interfaces.

```python
from src.core.interfaces.repositories import MaterialRepository, UnitOfWork

class MaterialService:
    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work
    
    async def add_material(self, material: Material) -> Material:
        async with self.unit_of_work:
            saved_material = await self.unit_of_work.materials.save(material)
            await self.unit_of_work.commit()
            return saved_material
    
    async def get_critical_materials(self) -> List[Material]:
        async with self.unit_of_work:
            return await self.unit_of_work.materials.get_critical_materials()
```

### 4. Service Layer
Business logic implementation through service interfaces.

```python
from src.core.interfaces.services import ForecastingService, BOMExplosionService
from src.core.domain.entities import Forecast, BillOfMaterial, Quantity

class PlanningService:
    def __init__(
        self,
        forecasting_service: ForecastingService,
        bom_explosion_service: BOMExplosionService
    ):
        self.forecasting_service = forecasting_service
        self.bom_explosion_service = bom_explosion_service
    
    async def calculate_material_requirements(
        self, 
        forecasts: List[Forecast],
        boms: List[BillOfMaterial]
    ) -> Dict[MaterialId, Quantity]:
        # Unify forecasts from multiple sources
        unified_forecasts = await self.forecasting_service.unify_forecasts(
            forecasts, 
            source_weights={
                ForecastSource.SALES_ORDER: 1.0,
                ForecastSource.PROJECTION: 0.7
            }
        )
        
        # Explode to material requirements
        requirements = await self.bom_explosion_service.explode_forecasts_to_materials(
            unified_forecasts, 
            boms
        )
        
        return requirements
```

### 5. Use Cases
Complete business scenarios with orchestration.

```python
from src.core.use_cases.procurement_planning import ProcurementPlanningUseCase
from src.core.domain.entities import ProcurementRecommendation

class PlanningController:
    def __init__(self, planning_use_case: ProcurementPlanningUseCase):
        self.planning_use_case = planning_use_case
    
    async def execute_planning(self, config: Dict[str, Any]) -> List[ProcurementRecommendation]:
        try:
            # Execute complete planning cycle
            recommendations = await self.planning_use_case.execute_planning_cycle(config)
            
            # Return recommendations
            return recommendations
            
        except PlanningError as e:
            # Handle planning-specific errors
            logging.error(f"Planning failed: {e.message}")
            raise
        except ValidationError as e:
            # Handle validation errors
            logging.error(f"Validation failed: {e.field_errors}")
            raise
```

## Dependency Injection Example

```python
from src.core.interfaces.repositories import UnitOfWork
from src.core.interfaces.services import (
    ForecastingService, BOMExplosionService, InventoryService,
    ProcurementOptimizationService, RiskAssessmentService
)
from src.core.use_cases.procurement_planning import ProcurementPlanningUseCase

class ApplicationContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        # Infrastructure layer (would be implemented in Phase 3)
        self.unit_of_work = self._create_unit_of_work()
        
        # Services (would be implemented in Phase 3)
        self.forecasting_service = self._create_forecasting_service()
        self.bom_explosion_service = self._create_bom_explosion_service()
        self.inventory_service = self._create_inventory_service()
        self.procurement_optimization_service = self._create_procurement_optimization_service()
        self.risk_assessment_service = self._create_risk_assessment_service()
        
        # Use cases
        self.procurement_planning_use_case = ProcurementPlanningUseCase(
            unit_of_work=self.unit_of_work,
            forecasting_service=self.forecasting_service,
            bom_explosion_service=self.bom_explosion_service,
            inventory_service=self.inventory_service,
            procurement_optimization_service=self.procurement_optimization_service,
            risk_assessment_service=self.risk_assessment_service
        )
    
    def _create_unit_of_work(self) -> UnitOfWork:
        # Implementation would be in infrastructure layer
        pass
    
    def _create_forecasting_service(self) -> ForecastingService:
        # Implementation would be in infrastructure layer
        pass
    
    # ... other service factory methods
```

## Error Handling Example

```python
from src.shared.exceptions import (
    ValidationError, DataNotFoundError, PlanningError, 
    BOMError, InventoryError, SupplierError
)

async def safe_planning_execution(config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Execute planning
        recommendations = await planning_use_case.execute_planning_cycle(config)
        
        return {
            'status': 'success',
            'recommendations': recommendations,
            'count': len(recommendations)
        }
        
    except ValidationError as e:
        return {
            'status': 'validation_error',
            'message': e.message,
            'field_errors': e.field_errors,
            'error_code': e.error_code
        }
    
    except DataNotFoundError as e:
        return {
            'status': 'data_not_found',
            'message': e.message,
            'resource_type': e.resource_type,
            'resource_id': e.resource_id
        }
    
    except PlanningError as e:
        return {
            'status': 'planning_error',
            'message': e.message,
            'execution_id': e.execution_id
        }
    
    except Exception as e:
        # Log unexpected errors
        logging.error(f"Unexpected error: {str(e)}")
        return {
            'status': 'internal_error',
            'message': 'An unexpected error occurred'
        }
```

## Testing Example

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.core.use_cases.procurement_planning import ProcurementPlanningUseCase
from src.core.interfaces.repositories import UnitOfWork
from src.core.interfaces.services import ForecastingService
from src.shared.exceptions import ValidationError

class TestProcurementPlanningUseCase:
    @pytest.fixture
    def mock_unit_of_work(self):
        return Mock(spec=UnitOfWork)
    
    @pytest.fixture
    def mock_forecasting_service(self):
        return Mock(spec=ForecastingService)
    
    @pytest.fixture
    def planning_use_case(self, mock_unit_of_work, mock_forecasting_service):
        return ProcurementPlanningUseCase(
            unit_of_work=mock_unit_of_work,
            forecasting_service=mock_forecasting_service,
            bom_explosion_service=Mock(),
            inventory_service=Mock(),
            procurement_optimization_service=Mock(),
            risk_assessment_service=Mock()
        )
    
    async def test_invalid_config_raises_validation_error(self, planning_use_case):
        invalid_config = {}  # Missing required fields
        
        with pytest.raises(ValidationError) as exc_info:
            await planning_use_case.execute_planning_cycle(invalid_config)
        
        assert "Missing required config fields" in str(exc_info.value)
    
    async def test_successful_planning_execution(self, planning_use_case, mock_unit_of_work):
        # Arrange
        config = {
            'planning_horizon_days': 90,
            'safety_stock_percentage': 0.1,
            'source_weights': {'sales_order': 1.0},
            'enable_multi_supplier': True
        }
        
        # Mock the repository responses
        mock_unit_of_work.forecasts.get_recent_forecasts.return_value = []
        mock_unit_of_work.boms.get_effective_boms.return_value = []
        
        # Act & Assert
        # Would need to mock all the service calls for full test
        # This shows the testing pattern
```

## Configuration Example

```python
from src.shared.types import PlanningConfig

# Example configuration for planning
planning_config: PlanningConfig = {
    # Basic settings
    'planning_horizon_days': 90,
    'safety_stock_percentage': 0.15,
    'forecast_lookback_days': 30,
    
    # Forecast source weights
    'source_weights': {
        'sales_order': 1.0,
        'prod_plan': 0.9,
        'projection': 0.7,
        'sales_history': 0.8
    },
    
    # Supplier optimization
    'enable_multi_supplier': True,
    'cost_weight': 0.6,
    'reliability_weight': 0.4,
    'max_suppliers_per_material': 3,
    
    # Advanced features
    'enable_eoq_optimization': True,
    'enable_risk_assessment': True,
    'enable_notifications': True,
    'enable_audit_logging': True,
    
    # Caching
    'cache_expiration': 3600,
    'cache_key': 'production_planning'
}
```

## Integration Points

### Database Integration (Phase 3)
```python
# Infrastructure layer implementation
from src.infrastructure.database.repositories import SqlMaterialRepository
from src.infrastructure.database.unit_of_work import SqlUnitOfWork

# Concrete implementations
unit_of_work = SqlUnitOfWork(connection_string)
material_repo = SqlMaterialRepository(connection_string)
```

### Caching Integration (Phase 3)
```python
# Infrastructure layer implementation
from src.infrastructure.cache.redis_cache import RedisCacheService

cache_service = RedisCacheService(redis_connection)
```

### Notification Integration (Phase 3)
```python
# Infrastructure layer implementation
from src.infrastructure.external.email_service import EmailNotificationService

notification_service = EmailNotificationService(smtp_config)
```

## Migration Path

### From Old Code
```python
# OLD: Monolithic approach
def run_planning(data, config):
    # Large function with mixed concerns
    forecasts = process_forecasts(data)
    requirements = explode_boms(forecasts)
    recommendations = generate_recommendations(requirements)
    return recommendations
```

### To New Architecture
```python
# NEW: Clean architecture approach
async def run_planning(config: PlanningConfig) -> List[ProcurementRecommendation]:
    # Dependency injection
    container = ApplicationContainer()
    
    # Use case execution
    recommendations = await container.procurement_planning_use_case.execute_planning_cycle(config)
    
    return recommendations
```

## Best Practices

1. **Always use type hints** for better IDE support and runtime checking
2. **Handle exceptions at appropriate levels** - use case level for business errors
3. **Keep domain logic in domain entities** - rich domain model
4. **Use dependency injection** for loose coupling and testability
5. **Validate inputs early** - fail fast with clear error messages
6. **Log important business events** - audit trail for compliance
7. **Cache expensive operations** - use cache service for performance
8. **Test through interfaces** - mock dependencies for unit testing

## Conclusion

The refactored architecture provides:
- **Clean separation of concerns** with proper layer boundaries
- **Type safety** with comprehensive type system
- **Testability** through dependency injection and interfaces
- **Maintainability** with single responsibility principle
- **Scalability** with async patterns and caching
- **Reliability** with proper error handling and validation

This foundation supports future enhancements while maintaining code quality and architectural integrity.