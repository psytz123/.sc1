"""
Procurement Planning Use Cases

This module contains the main use cases for procurement planning,
implementing the core business logic following clean architecture.
"""

from typing import Dict, List, Optional, Any
from datetime import date, datetime
from uuid import UUID, uuid4
import logging

from src.core.domain.entities import (
    MaterialId, Forecast, BillOfMaterial, Inventory, 
    ProcurementRecommendation, RiskLevel, Quantity, Money
)
from src.core.interfaces.repositories import UnitOfWork
from src.core.interfaces.services import (
    ForecastingService, BOMExplosionService, InventoryService,
    ProcurementOptimizationService, RiskAssessmentService,
    CacheService, NotificationService, AuditService
)
from src.shared.exceptions import (
    PlanningError, ValidationError, DataNotFoundError
)

logger = logging.getLogger(__name__)


class ProcurementPlanningUseCase:
    """Main use case for procurement planning"""
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        forecasting_service: ForecastingService,
        bom_explosion_service: BOMExplosionService,
        inventory_service: InventoryService,
        procurement_optimization_service: ProcurementOptimizationService,
        risk_assessment_service: RiskAssessmentService,
        cache_service: Optional[CacheService] = None,
        notification_service: Optional[NotificationService] = None,
        audit_service: Optional[AuditService] = None
    ):
        self.unit_of_work = unit_of_work
        self.forecasting_service = forecasting_service
        self.bom_explosion_service = bom_explosion_service
        self.inventory_service = inventory_service
        self.procurement_optimization_service = procurement_optimization_service
        self.risk_assessment_service = risk_assessment_service
        self.cache_service = cache_service
        self.notification_service = notification_service
        self.audit_service = audit_service
    
    async def execute_planning_cycle(
        self,
        planning_config: Dict[str, Any],
        execution_id: Optional[UUID] = None
    ) -> List[ProcurementRecommendation]:
        """
        Execute complete procurement planning cycle
        
        Args:
            planning_config: Planning configuration parameters
            execution_id: Optional execution ID for tracking
            
        Returns:
            List of procurement recommendations
            
        Raises:
            PlanningError: If planning execution fails
            ValidationError: If input validation fails
        """
        if execution_id is None:
            execution_id = uuid4()
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting procurement planning cycle {execution_id}")
            
            # Step 1: Validate configuration
            await self._validate_planning_config(planning_config)
            
            # Step 2: Load and unify forecasts
            forecasts = await self._load_and_unify_forecasts(planning_config)
            logger.info(f"Loaded {len(forecasts)} forecasts")
            
            # Step 3: Explode BOMs to get material requirements
            material_requirements = await self._explode_boms_to_materials(
                forecasts, planning_config
            )
            logger.info(f"Calculated requirements for {len(material_requirements)} materials")
            
            # Step 4: Calculate net requirements after inventory netting
            net_requirements = await self._calculate_net_requirements(
                material_requirements, planning_config
            )
            logger.info(f"Calculated net requirements for {len(net_requirements)} materials")
            
            # Step 5: Generate procurement recommendations
            recommendations = await self._generate_procurement_recommendations(
                net_requirements, planning_config
            )
            logger.info(f"Generated {len(recommendations)} procurement recommendations")
            
            # Step 6: Assess and update risk levels
            recommendations = await self._assess_and_update_risks(
                recommendations, planning_config
            )
            
            # Step 7: Save recommendations
            async with self.unit_of_work:
                saved_recommendations = await self.unit_of_work.recommendations.save_batch(
                    recommendations
                )
                await self.unit_of_work.commit()
            
            # Step 8: Send notifications for high-risk items
            await self._send_notifications(saved_recommendations)
            
            # Step 9: Log execution for audit
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._log_execution(
                execution_id, planning_config, saved_recommendations, execution_time
            )
            
            logger.info(f"Completed procurement planning cycle {execution_id}")
            return saved_recommendations
            
        except Exception as e:
            logger.error(f"Planning cycle {execution_id} failed: {str(e)}")
            raise PlanningError(f"Planning execution failed: {str(e)}") from e
    
    async def _validate_planning_config(self, config: Dict[str, Any]) -> None:
        """Validate planning configuration"""
        required_fields = [
            'planning_horizon_days', 'safety_stock_percentage',
            'source_weights', 'enable_multi_supplier'
        ]
        
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise ValidationError(f"Missing required config fields: {missing_fields}")
        
        # Validate value ranges
        if not 0 <= config['safety_stock_percentage'] <= 1:
            raise ValidationError("Safety stock percentage must be between 0 and 1")
        
        if config['planning_horizon_days'] <= 0:
            raise ValidationError("Planning horizon days must be positive")
    
    async def _load_and_unify_forecasts(
        self, 
        config: Dict[str, Any]
    ) -> Dict[str, Quantity]:
        """Load and unify forecasts from multiple sources"""
        
        # Check cache first
        cache_key = f"unified_forecasts_{config.get('cache_key', 'default')}"
        if self.cache_service:
            cached_forecasts = await self.cache_service.get(cache_key)
            if cached_forecasts:
                logger.info("Using cached forecasts")
                return cached_forecasts
        
        # Load recent forecasts
        async with self.unit_of_work:
            forecasts = await self.unit_of_work.forecasts.get_recent_forecasts(
                days=config.get('forecast_lookback_days', 30)
            )
        
        if not forecasts:
            raise DataNotFoundError("No forecasts found for planning")
        
        # Unify forecasts using weights
        source_weights = config.get('source_weights', {})
        unified_forecasts = await self.forecasting_service.unify_forecasts(
            forecasts, source_weights
        )
        
        # Cache the result
        if self.cache_service:
            await self.cache_service.set(
                cache_key, unified_forecasts, 
                expiration_seconds=config.get('cache_expiration', 3600)
            )
        
        return unified_forecasts
    
    async def _explode_boms_to_materials(
        self,
        sku_forecasts: Dict[str, Quantity],
        config: Dict[str, Any]
    ) -> Dict[MaterialId, Dict[str, Any]]:
        """Explode SKU forecasts to material requirements"""
        
        # Load effective BOMs
        async with self.unit_of_work:
            boms = await self.unit_of_work.boms.get_effective_boms()
        
        if not boms:
            raise DataNotFoundError("No BOMs found for explosion")
        
        # Perform BOM explosion
        material_requirements = await self.bom_explosion_service.explode_forecasts_to_materials(
            sku_forecasts, boms
        )
        
        # Validate BOM completeness
        sku_ids = list(sku_forecasts.keys())
        completeness_issues = await self.bom_explosion_service.validate_bom_completeness(
            sku_ids, boms
        )
        
        if completeness_issues:
            logger.warning(f"BOM completeness issues found: {completeness_issues}")
        
        return material_requirements
    
    async def _calculate_net_requirements(
        self,
        gross_requirements: Dict[MaterialId, Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[MaterialId, Dict[str, Any]]:
        """Calculate net requirements after inventory netting"""
        
        # Load current inventory levels
        material_ids = list(gross_requirements.keys())
        async with self.unit_of_work:
            inventory_levels = await self.unit_of_work.inventory.get_by_material_ids(
                material_ids
            )
        
        # Convert to format expected by inventory service
        gross_quantities = {
            material_id: Quantity(
                amount=req_data['total_quantity'],
                unit=req_data['unit']
            )
            for material_id, req_data in gross_requirements.items()
        }
        
        # Calculate net requirements
        net_requirements = await self.inventory_service.calculate_net_requirements(
            gross_quantities, inventory_levels
        )
        
        return net_requirements
    
    async def _generate_procurement_recommendations(
        self,
        net_requirements: Dict[MaterialId, Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[ProcurementRecommendation]:
        """Generate procurement recommendations"""
        
        recommendations = []
        
        for material_id, req_data in net_requirements.items():
            net_quantity = req_data.get('net_requirement_quantity')
            if not net_quantity or net_quantity.amount <= 0:
                continue
            
            # Load supplier relationships for this material
            async with self.unit_of_work:
                supplier_relations = await self.unit_of_work.material_suppliers.get_by_material_id(
                    material_id
                )
            
            if not supplier_relations:
                logger.warning(f"No suppliers found for material {material_id.value}")
                continue
            
            # Filter active suppliers
            active_suppliers = [
                rel for rel in supplier_relations 
                if rel.is_active and rel.is_contract_active()
            ]
            
            if not active_suppliers:
                logger.warning(f"No active suppliers found for material {material_id.value}")
                continue
            
            # Generate recommendations based on configuration
            if config.get('enable_multi_supplier', False) and len(active_suppliers) > 1:
                material_recommendations = await self._generate_multi_supplier_recommendations(
                    material_id, net_quantity, active_suppliers, config
                )
            else:
                material_recommendations = await self._generate_single_supplier_recommendations(
                    material_id, net_quantity, active_suppliers, config
                )
            
            recommendations.extend(material_recommendations)
        
        return recommendations
    
    async def _generate_single_supplier_recommendations(
        self,
        material_id: MaterialId,
        required_quantity: Quantity,
        suppliers: List[Any],
        config: Dict[str, Any]
    ) -> List[ProcurementRecommendation]:
        """Generate single supplier recommendation"""
        
        # Optimize supplier selection
        selected_suppliers = await self.procurement_optimization_service.optimize_supplier_selection(
            material_id, required_quantity, suppliers,
            cost_weight=config.get('cost_weight', 0.6),
            reliability_weight=config.get('reliability_weight', 0.4)
        )
        
        if not selected_suppliers:
            return []
        
        # Use the best supplier
        best_supplier = selected_suppliers[0]
        supplier_id, quantity, cost = best_supplier
        
        # Calculate EOQ if enabled
        eoq_quantity = None
        if config.get('enable_eoq_optimization', False):
            # Get annual demand estimate
            annual_demand = required_quantity * 4  # Assuming quarterly planning
            
            # Find the supplier relation for costing data
            supplier_relation = next(
                (rel for rel in suppliers if rel.supplier_id == supplier_id), 
                None
            )
            
            if supplier_relation:
                eoq_quantity = await self.procurement_optimization_service.calculate_economic_order_quantity(
                    material_id, annual_demand, supplier_relation.ordering_cost,
                    supplier_relation.holding_cost_rate, supplier_relation.cost_per_unit
                )
        
        # Create recommendation
        recommendation = ProcurementRecommendation(
            id=uuid4(),
            material_id=material_id,
            supplier_id=supplier_id,
            recommended_quantity=quantity,
            estimated_cost=cost,
            recommended_order_date=date.today(),
            expected_delivery_date=date.today(),  # Will be calculated based on lead time
            risk_level=RiskLevel.LOW,  # Will be assessed later
            urgency_score=0.5,  # Will be calculated later
            reasoning="Optimized single supplier selection",
            eoq_quantity=eoq_quantity
        )
        
        return [recommendation]
    
    async def _generate_multi_supplier_recommendations(
        self,
        material_id: MaterialId,
        required_quantity: Quantity,
        suppliers: List[Any],
        config: Dict[str, Any]
    ) -> List[ProcurementRecommendation]:
        """Generate multi-supplier recommendations"""
        
        # Optimize across multiple suppliers
        selected_suppliers = await self.procurement_optimization_service.optimize_supplier_selection(
            material_id, required_quantity, suppliers,
            cost_weight=config.get('cost_weight', 0.6),
            reliability_weight=config.get('reliability_weight', 0.4)
        )
        
        recommendations = []
        for supplier_id, quantity, cost in selected_suppliers:
            recommendation = ProcurementRecommendation(
                id=uuid4(),
                material_id=material_id,
                supplier_id=supplier_id,
                recommended_quantity=quantity,
                estimated_cost=cost,
                recommended_order_date=date.today(),
                expected_delivery_date=date.today(),
                risk_level=RiskLevel.LOW,
                urgency_score=0.5,
                reasoning=f"Multi-supplier optimization - {quantity.amount} units"
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _assess_and_update_risks(
        self,
        recommendations: List[ProcurementRecommendation],
        config: Dict[str, Any]
    ) -> List[ProcurementRecommendation]:
        """Assess and update risk levels for recommendations"""
        
        updated_recommendations = []
        
        for recommendation in recommendations:
            # Assess supplier risk
            supplier_risk = await self.risk_assessment_service.assess_supplier_risk(
                recommendation.supplier_id,
                recommendation.material_id,
                recommendation.recommended_quantity
            )
            
            # Update risk level and reasoning
            recommendation.update_risk_level(supplier_risk, f"Risk assessment: {supplier_risk.value}")
            
            # Calculate urgency score based on inventory levels and lead times
            urgency_score = await self._calculate_urgency_score(recommendation, config)
            recommendation.urgency_score = urgency_score
            
            updated_recommendations.append(recommendation)
        
        return updated_recommendations
    
    async def _calculate_urgency_score(
        self,
        recommendation: ProcurementRecommendation,
        config: Dict[str, Any]
    ) -> float:
        """Calculate urgency score for recommendation"""
        
        # Get current inventory level
        async with self.unit_of_work:
            inventory = await self.unit_of_work.inventory.get_by_material_id(
                recommendation.material_id
            )
        
        if not inventory:
            return 1.0  # Maximum urgency if no inventory data
        
        # Calculate urgency based on inventory levels
        if inventory.is_below_safety_stock():
            return 1.0  # Maximum urgency
        elif inventory.is_below_reorder_point():
            return 0.8  # High urgency
        else:
            return 0.5  # Normal urgency
    
    async def _send_notifications(
        self,
        recommendations: List[ProcurementRecommendation]
    ) -> None:
        """Send notifications for high-risk recommendations"""
        
        if not self.notification_service:
            return
        
        high_risk_recommendations = [
            rec for rec in recommendations 
            if rec.risk_level == RiskLevel.HIGH
        ]
        
        for recommendation in high_risk_recommendations:
            try:
                await self.notification_service.send_procurement_alert(recommendation)
            except Exception as e:
                logger.error(f"Failed to send notification for {recommendation.id}: {str(e)}")
    
    async def _log_execution(
        self,
        execution_id: UUID,
        config: Dict[str, Any],
        recommendations: List[ProcurementRecommendation],
        execution_time: float
    ) -> None:
        """Log execution for audit trail"""
        
        if not self.audit_service:
            return
        
        try:
            await self.audit_service.log_planning_execution(
                execution_id, config, recommendations, execution_time
            )
        except Exception as e:
            logger.error(f"Failed to log execution {execution_id}: {str(e)}")


class ForecastManagementUseCase:
    """Use case for managing forecasts"""
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        forecasting_service: ForecastingService,
        cache_service: Optional[CacheService] = None
    ):
        self.unit_of_work = unit_of_work
        self.forecasting_service = forecasting_service
        self.cache_service = cache_service
    
    async def import_forecasts(
        self,
        forecasts: List[Forecast],
        replace_existing: bool = False
    ) -> List[Forecast]:
        """Import forecasts from external source"""
        
        async with self.unit_of_work:
            if replace_existing:
                # Delete existing forecasts for the same SKUs
                sku_ids = list(set(f.sku_id for f in forecasts))
                for sku_id in sku_ids:
                    await self.unit_of_work.forecasts.delete_by_sku_id(sku_id)
            
            # Save new forecasts
            saved_forecasts = await self.unit_of_work.forecasts.save_batch(forecasts)
            await self.unit_of_work.commit()
        
        # Clear cache
        if self.cache_service:
            await self.cache_service.clear_pattern("unified_forecasts_*")
        
        return saved_forecasts
    
    async def generate_forecasts_from_sales_history(
        self,
        sku_ids: List[str],
        config: Dict[str, Any]
    ) -> List[Forecast]:
        """Generate forecasts from sales history"""
        
        forecasts = []
        
        for sku_id in sku_ids:
            sku_forecasts = await self.forecasting_service.generate_forecast_from_sales_history(
                sku_id,
                lookback_days=config.get('lookback_days', 90),
                forecast_horizon_days=config.get('forecast_horizon_days', 90)
            )
            forecasts.extend(sku_forecasts)
        
        # Save forecasts
        if forecasts:
            async with self.unit_of_work:
                saved_forecasts = await self.unit_of_work.forecasts.save_batch(forecasts)
                await self.unit_of_work.commit()
                return saved_forecasts
        
        return []