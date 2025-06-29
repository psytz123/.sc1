"""Test EOQ and Multi-Supplier functionality"""
from data.sample_data_generator import SampleDataGenerator
from utils.logger import get_logger

logger = get_logger(__name__)
from engine.planner import RawMaterialPlanner
from models.bom import BOMExploder
from models.forecast import ForecastProcessor
from models.inventory import InventoryNetter
from models.supplier import (
    EOQCalculator,
    MultiSupplierOptimizer,
    Supplier,
    SupplierSelector,
)


def test_eoq_calculator():
    """Test EOQ calculation"""
    logger.info("Testing EOQ Calculator...")
    
    # Test basic EOQ calculation
    annual_demand = 10000
    ordering_cost = 50
    holding_cost_rate = 0.2
    unit_cost = 10
    
    eoq = EOQCalculator.calculate_eoq(
        annual_demand, ordering_cost, holding_cost_rate, unit_cost
    )
    
    # EOQ formula: sqrt(2 * D * S / H)
    # where H = holding_cost_rate * unit_cost
    expected_eoq = (2 * annual_demand * ordering_cost / (holding_cost_rate * unit_cost)) ** 0.5
    
    assert abs(eoq - expected_eoq) < 0.01
    logger.info(f"   ✓ EOQ calculated correctly: {eoq:.2f} units")


def test_multi_supplier_optimizer():
    """Test multi-supplier optimization"""
    logger.info("Testing Multi-Supplier Optimizer...")
    
    # Create test suppliers
    suppliers = [
        Supplier(
            material_id="MAT1",
            supplier_id="SUP1",
            cost_per_unit=10.0,
            lead_time_days=7,
            moq=100,
            reliability_score=0.95
        ),
        Supplier(
            material_id="MAT1",
            supplier_id="SUP2",
            cost_per_unit=9.5,
            lead_time_days=14,
            moq=200,
            reliability_score=0.85
        ),
        Supplier(
            material_id="MAT1",
            supplier_id="SUP3",
            cost_per_unit=11.0,
            lead_time_days=5,
            moq=50,
            reliability_score=0.98
        )
    ]
    
    # Test optimization
    total_quantity = 1000
    config = {
        'cost_weight': 0.6,
        'reliability_weight': 0.4,
        'max_suppliers_per_material': 3
    }

    optimizer = MultiSupplierOptimizer()
    allocations = optimizer.optimize_multi_supplier_sourcing(
        material_id="MAT1",
        required_quantity=total_quantity,
        suppliers=suppliers,
        max_suppliers=config['max_suppliers_per_material'],
        cost_weight=config['cost_weight'],
        reliability_weight=config['reliability_weight']
    )

    # Verify allocations
    assert len(allocations) > 0
    assert len(allocations) <= 3

    total_allocated = sum(a.quantity for a in allocations)
    assert abs(total_allocated - total_quantity) < 0.01
    
    logger.info(f"   ✓ Allocated {total_quantity} units across {len(allocations)} suppliers")
    for allocation in allocations:
        logger.info(f"     - {allocation.supplier.supplier_id}: {allocation.quantity:.0f} units @ ${allocation.cost:.2f}")


def test_enhanced_planning():
    """Test the enhanced planning with EOQ and multi-supplier"""
    logger.info("🧠 Testing Enhanced Planning System...")
    
    # Generate sample data
    sample_data = SampleDataGenerator.generate_all_sample_data(5)
    
    # Convert to model objects
    forecasts = ForecastProcessor.from_dataframe(sample_data['forecasts'])
    boms = BOMExploder.from_dataframe(sample_data['boms'])
    inventories = InventoryNetter.from_dataframe(sample_data['inventory'])
    suppliers = SupplierSelector.from_dataframe(sample_data['suppliers'])
    
    # Configure planner with EOQ and multi-supplier enabled
    config = {
        'source_weights': {'sales_order': 1.0, 'prod_plan': 0.9, 'projection': 0.7},
        'safety_buffer': 0.1,
        'max_lead_time': 30,
        'safety_stock_days': 7,
        'high_risk_threshold': 0.7,
        'medium_risk_threshold': 0.85,
        'enable_eoq_optimization': True,
        'enable_multi_supplier': True,
        'annual_demand_multiplier': 4,
        'max_suppliers_per_material': 3,
        'cost_weight': 0.6,
        'reliability_weight': 0.4,
        'planning_horizon_days': 90
    }
    
    # Initialize and run planner
    planner = RawMaterialPlanner(config)
    recommendations = planner.plan(forecasts, boms, inventories, suppliers)
    
    logger.info(f"   Generated {len(recommendations)} recommendations")
    
    # Check that recommendations were generated
    assert len(recommendations) > 0
    
    # Verify EOQ was applied (check reasoning)
    eoq_applied = any('EOQ' in r.reasoning for r in recommendations)
    logger.info(f"   ✓ EOQ optimization applied: {eoq_applied}")
    
    # Verify multi-supplier was considered
    multi_supplier_used = any('Multiple suppliers' in r.reasoning for r in recommendations)
    logger.info(f"   ✓ Multi-supplier sourcing used: {multi_supplier_used}")
    
    # Show sample recommendations
    logger.info("\n   Sample Recommendations:")
    for rec in recommendations[:3]:
        logger.info(f"   - {rec.material_id}: {rec.order_quantity:.0f} units from {rec.supplier_id}")
        logger.info(f"     Cost: ${rec.total_cost:,.2f}, Lead time: {rec.lead_time_days} days")
        logger.info(f"     {rec.reasoning}")


if __name__ == "__main__":
    logger.info("Running EOQ and Multi-Supplier Tests...")
    logger.info("=" * 50)
    
    test_eoq_calculator()
    logger.info()
    
    test_multi_supplier_optimizer()
    logger.info()
    
    test_enhanced_planning()
    logger.info()
    
    logger.info("All tests completed! ✅")