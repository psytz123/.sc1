"""
Test script to verify sales forecast integration with the planning engine
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
import json
import pandas as pd

from scripts.analyze_sales_inventory import SalesInventoryAnalyzer
from engine.planner import RawMaterialPlanner
from config.settings import PlanningConfig
from models.bom import BillOfMaterials
from models.inventory import Inventory
from models.supplier import Supplier
from utils.logger import get_logger

logger = get_logger(__name__)

def test_sales_forecast_generation():
    """Test the sales forecast generation"""
    logger.info("="*60)
    logger.info("TESTING SALES FORECAST GENERATION")
    logger.info("="*60)
    
    # Initialize analyzer
    analyzer = SalesInventoryAnalyzer()
    
    # Load data
    analyzer.load_data()
    
    # Generate forecasts only
    forecasts = analyzer.generate_forecasts(
        lookback_days=90,
        planning_horizon_days=90,
        aggregation_period='weekly',
        safety_stock_method='statistical'
    )
    
    logger.info(f"\nGenerated {len(forecasts)} forecasts")

    # Show sample forecasts
    if forecasts:
        logger.info("\nSample forecasts (first 5):")
        for i, forecast in enumerate(forecasts[:5]):
            logger.info(f"  {i+1}. Style: {forecast.sku_id}, Qty: {forecast.forecast_qty:,.0f}, "
                       f"Confidence: {forecast.confidence:.2f}")
    
    # Save forecasts
    analyzer.save_results()
    
    return forecasts

def test_planner_integration():
    """Test the integration with the main planner"""
    logger.info("\n"+"="*60)
    logger.info("TESTING PLANNER INTEGRATION")
    logger.info("="*60)
    
    # Create config with sales forecasting enabled
    config = PlanningConfig()
    config.enable_sales_forecasting = True
    config.sales_lookback_days = 90
    config.planning_horizon_days = 90
    config.aggregation_period = 'weekly'
    config.safety_stock_method = 'statistical'
    
    # Initialize planner
    planner = RawMaterialPlanner(config)
    
    # Test forecast loading
    logger.info("\nTesting forecast loading from sales data...")
    sales_forecasts = planner._generate_sales_forecasts()

    # Check if forecasts were loaded
    if sales_forecasts:
        logger.info(f"[OK] Loaded {len(sales_forecasts)} forecasts from sales data")

        # Show sample forecasts
        logger.info("\nSample forecasts (first 5):")
        for i, forecast in enumerate(sales_forecasts[:5]):
            logger.info(f"  {i+1}. Style: {forecast.sku_id}, Qty: {forecast.forecast_qty:,.0f}, "
                       f"Source: {forecast.source}")

    # Create minimal test data for full planning run
    logger.info("\nTesting full planning run with sales forecasts...")
    
    # Create dummy BOM and supplier data
    test_boms = []
    test_inventory = []
    test_suppliers = []
    
    # Add a simple test BOM
    if sales_forecasts:
        # Create a simple BOM for the first forecasted style
        test_style = sales_forecasts[0].sku_id
        test_bom = BillOfMaterials(
            sku_id=test_style,
            material_id="TEST_MATERIAL",
            qty_per_unit=1.0,
            unit="yards"
        )
        test_boms.append(test_bom)
        
        # Add a test supplier
        test_supplier = Supplier(
            supplier_id="SUP_001",
            material_id="YARN_001",
            cost_per_unit=5.0,
            lead_time_days=14,
            moq=100,
            reliability_score=0.9
        )
        test_suppliers.append(test_supplier)
    
    # Run planning with sales forecasts
    try:
        recommendations = planner.plan(
            forecasts=sales_forecasts,  # Using sales-based forecasts
            boms=test_boms,
            inventory=test_inventory,
            suppliers=test_suppliers
        )
        
        logger.info(f"[OK] Planning completed with {len(recommendations)} recommendations")
        
        if recommendations:
            logger.info("\nSample recommendations:")
            for i, rec in enumerate(recommendations[:3]):
                logger.info(f"  {i+1}. Material: {rec.material_id}, Qty: {rec.order_qty:,.0f}, "
                           f"Cost: ${rec.total_cost:,.2f}")
    
    except Exception as e:
        logger.error(f"[ERROR] Planning failed: {e}")
        return False
    
    return True

def verify_integration_files():
    """Verify that all integration files are created correctly"""
    logger.info("\n"+"="*60)
    logger.info("VERIFYING INTEGRATION FILES")
    logger.info("="*60)
    
    files_to_check = [
        ('output/generated_forecasts.csv', 'Forecast data'),
        ('output/sales_inventory_analysis.json', 'Analysis results'),
        ('output/sales_forecast_integration.json', 'Integration metadata')
    ]
    
    all_good = True
    for file_path, description in files_to_check:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            logger.info(f"[OK] {description}: {file_path} ({size:,} bytes)")
            
            # Check content
            if file_path.endswith('.json'):
                with open(path, 'r') as f:
                    data = json.load(f)
                    logger.info(f"   - Keys: {list(data.keys())}")
            elif file_path.endswith('.csv'):
                df = pd.read_csv(path)
                logger.info(f"   - Rows: {len(df)}, Columns: {list(df.columns)}")
        else:
            logger.error(f"[MISSING] Missing: {file_path}")
            all_good = False
    
    return all_good

def main():
    """Run all integration tests"""
    logger.info("SALES FORECAST INTEGRATION TEST")
    logger.info("="*60)
    
    # Test 1: Generate forecasts
    logger.info("\nTest 1: Forecast Generation")
    forecasts = test_sales_forecast_generation()
    
    # Test 2: Verify files
    logger.info("\n📁 Test 2: File Verification")
    files_ok = verify_integration_files()
    
    # Test 3: Planner integration
    logger.info("\nTest 3: Planner Integration")
    planner_ok = test_planner_integration()
    
    # Summary
    logger.info("\n"+"="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Forecast Generation: {'PASSED' if forecasts else 'FAILED'}")
    logger.info(f"File Creation: {'PASSED' if files_ok else 'FAILED'}")
    logger.info(f"Planner Integration: {'PASSED' if planner_ok else 'FAILED'}")
    
    if forecasts and files_ok and planner_ok:
        logger.info("\nAll tests passed! Sales forecast integration is working correctly.")
        logger.info("\nThe planning engine will now automatically use sales-based forecasts when:")
        logger.info("1. enable_sales_forecasting is True in config")
        logger.info("2. Forecast files exist and are less than 24 hours old")
    else:
        logger.info("\nSome tests failed. Please check the logs above.")

if __name__ == "__main__":
    main()