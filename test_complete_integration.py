#!/usr/bin/env python3
"""
Test script for the complete Beverly Knits integration system
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.master_integration import IntegrationOrchestrator

def test_complete_integration():
    """Test the complete integration system"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'output/integration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Beverly Knits Complete Integration Test")
    
    try:
        # Create orchestrator
        orchestrator = IntegrationOrchestrator()
        
        # Test initialization
        logger.info("\n=== Testing Integration Initialization ===")
        init_success = orchestrator.initialize_integrations()
        logger.info(f"Initialization result: {'SUCCESS' if init_success else 'FAILED'}")
        
        # Test validation
        logger.info("\n=== Testing Integration Validation ===")
        validation_results = orchestrator.validate_all_integrations()
        logger.info("Validation results:")
        for integration, valid in validation_results.items():
            logger.info(f"  - {integration}: {'VALID' if valid else 'INVALID'}")
        
        # Test complete integration with sample data
        logger.info("\n=== Running Complete Integration ===")
        
        # Sample manual forecasts
        manual_forecasts = [
            {
                'sku': 'BK-CREW-001',
                'quantity': 5000,
                'month': '2024-01',
                'confidence': 0.85,
                'source': 'sales_team'
            },
            {
                'sku': 'BK-VNECK-002',
                'quantity': 3000,
                'month': '2024-01',
                'confidence': 0.90,
                'source': 'sales_team'
            }
        ]
        
        # Sample customer orders
        customer_orders = [
            {
                'customer': 'Retail Chain A',
                'sku': 'BK-CREW-001',
                'quantity': 2000,
                'delivery_date': '2024-01-15',
                'status': 'confirmed'
            },
            {
                'customer': 'Online Store B',
                'sku': 'BK-VNECK-002',
                'quantity': 1500,
                'delivery_date': '2024-01-20',
                'status': 'confirmed'
            }
        ]
        
        # Run complete integration
        results = orchestrator.run_complete_integration(
            manual_forecasts=manual_forecasts,
            customer_orders=customer_orders
        )
        
        # Display results
        logger.info("\n=== Integration Results ===")
        logger.info(f"Status: {results.get('status', 'unknown').upper()}")
        
        if results.get('status') == 'success':
            # Display key metrics
            if 'reports' in results and 'master_summary' in results['reports']:
                summary = results['reports']['master_summary']
                logger.info(f"System Health Score: {summary.get('system_health_score', 0):.1f}/100")
                logger.info(f"System Health Status: {summary.get('system_health_status', 'unknown')}")
                
                if 'key_metrics' in summary:
                    logger.info("\nKey Metrics:")
                    for metric, value in summary['key_metrics'].items():
                        logger.info(f"  - {metric}: {value}")
            
            # Display integration status
            logger.info("\nIntegration Status:")
            for integration, status in results.get('integration_status', {}).items():
                logger.info(f"  - {integration}: {status.get('status', 'unknown')}")
                if status.get('errors'):
                    logger.info(f"    Errors: {len(status['errors'])}")
                    for error in status['errors'][:3]:  # Show first 3 errors
                        logger.info(f"      • {error}")
                if status.get('warnings'):
                    logger.info(f"    Warnings: {len(status['warnings'])}")
                    for warning in status['warnings'][:3]:  # Show first 3 warnings
                        logger.info(f"      • {warning}")
            
            # Display planning results summary
            if 'planning_results' in results:
                planning = results['planning_results']
                if 'integration_metadata' in planning:
                    meta = planning['integration_metadata']
                    logger.info("\nPlanning Results:")
                    logger.info(f"  - Forecasts generated: {meta.get('combined_forecasts_count', 0)}")
                    logger.info(f"  - Recommendations: {meta.get('recommendations_count', 0)}")
                    logger.info(f"  - Total recommended quantity: {meta.get('total_recommended_qty', 0):,.2f}")
            
            # Display supplier results summary
            if 'supplier_results' in results:
                supplier = results['supplier_results']
                if 'supplier_count' in supplier:
                    logger.info("\nSupplier Results:")
                    logger.info(f"  - Total suppliers: {supplier['supplier_count']}")
                    if 'tier_distribution' in supplier:
                        logger.info("  - Tier distribution:")
                        for tier, count in supplier['tier_distribution'].items():
                            logger.info(f"    • Tier {tier}: {count}")
            
            # Display inventory results summary
            if 'inventory_results' in results:
                inventory = results['inventory_results']
                if 'total_items' in inventory:
                    logger.info("\nInventory Results:")
                    logger.info(f"  - Total items: {inventory['total_items']}")
                    logger.info(f"  - Critical items: {inventory.get('critical_items', 0)}")
            
            # Display optimization results
            if 'optimization_results' in results:
                optimization = results['optimization_results']
                if 'total_materials' in optimization:
                    logger.info("\nOptimization Results:")
                    logger.info(f"  - Materials optimized: {optimization['total_materials']}")
                    logger.info(f"  - Suppliers selected: {optimization['total_suppliers']}")
                    logger.info(f"  - Urgent reorders: {optimization.get('urgent_reorders', 0)}")
            
            logger.info("\n✅ Integration test completed successfully!")
            
        else:
            logger.error(f"\n❌ Integration failed: {results.get('error', 'Unknown error')}")
            
            # Show detailed errors
            if 'integration_status' in results:
                logger.error("\nDetailed Errors:")
                for integration, status in results['integration_status'].items():
                    if status.get('errors'):
                        logger.error(f"\n{integration.upper()} errors:")
                        for error in status['errors']:
                            logger.error(f"  - {error}")
        
        return results
        
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        return {'status': 'failed', 'error': str(e)}

def test_individual_integrations():
    """Test individual integration modules"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n=== Testing Individual Integration Modules ===")
    
    # Test supplier integration
    try:
        from integrations.suppliers.supplier_integration import SupplierIntegration
        
        logger.info("\nTesting Supplier Integration...")
        supplier_int = SupplierIntegration()
        supplier_df = supplier_int.load_supplier_data()
        logger.info(f"  ✓ Loaded {len(supplier_df)} suppliers")
        
        validation = supplier_int.validate_supplier_data(supplier_df)
        logger.info(f"  ✓ Validation complete: {len(validation['errors'])} errors, {len(validation['warnings'])} warnings")
        
    except Exception as e:
        logger.error(f"  ✗ Supplier integration test failed: {str(e)}")
    
    # Test inventory integration
    try:
        from integrations.inventory_integration import InventoryIntegration
        
        logger.info("\nTesting Inventory Integration...")
        inventory_int = InventoryIntegration()
        inventory_df = inventory_int.load_inventory_data()
        logger.info(f"  ✓ Loaded {len(inventory_df)} inventory items")
        
        validation = inventory_int.validate_inventory_data(inventory_df)
        logger.info(f"  ✓ Validation complete: {len(validation['errors'])} errors, {len(validation['warnings'])} warnings")
        
    except Exception as e:
        logger.error(f"  ✗ Inventory integration test failed: {str(e)}")
    
    # Test sales integration
    try:
        from engine.sales_planning_integration import SalesPlanningIntegration
        
        logger.info("\nTesting Sales Planning Integration...")
        sales_int = SalesPlanningIntegration()
        validation = sales_int.validate_integration()
        logger.info(f"  ✓ Validation complete: Overall status = {validation.get('overall', False)}")
        
    except Exception as e:
        logger.error(f"  ✗ Sales integration test failed: {str(e)}")

if __name__ == "__main__":
    print("=" * 80)
    print("Beverly Knits Complete Integration Test")
    print("=" * 80)
    
    # Test individual modules first
    test_individual_integrations()
    
    # Then test complete integration
    results = test_complete_integration()
    
    # Exit with appropriate code
    if results.get('status') == 'success':
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)