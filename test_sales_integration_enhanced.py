"""
Test Sales Integration - Comprehensive test suite for sales-based planning
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path

from models.sales_forecast_generator import SalesForecastGenerator
from data.sales_data_processor import SalesDataProcessor
from engine.sales_planning_integration import SalesPlanningIntegration
from models.forecast import FinishedGoodsForecast

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sales_forecast_generator():
    """Test the enhanced sales forecast generator"""
    print("\n" + "="*60)
    print("Testing Sales Forecast Generator")
    print("="*60)
    
    # Create sample sales data
    dates = pd.date_range(end=datetime.now(), periods=180, freq='D')
    styles = ['STYLE-001', 'STYLE-002', 'STYLE-003']
    
    sales_data = []
    for date in dates:
        for style in styles:
            if np.random.random() > 0.7:  # 30% chance of sale each day
                sales_data.append({
                    'Invoice Date': date,
                    'Style': style,
                    'Yds_ordered': np.random.normal(100, 20) * (1 + 0.1 * np.sin(date.month))  # Seasonal pattern
                })
    
    sales_df = pd.DataFrame(sales_data)
    
    # Create sample BOM data
    bom_data = []
    yarns = ['YARN-A', 'YARN-B', 'YARN-C']
    for style in styles:
        percentages = [50, 30, 20]  # Must sum to 100
        for yarn, pct in zip(yarns, percentages):
            bom_data.append({
                'Style': style,
                'Yarn_ID': yarn,
                'Percentage': pct
            })
    
    bom_df = pd.DataFrame(bom_data)
    
    # Test forecast generation
    generator = SalesForecastGenerator(sales_df, bom_df=bom_df)
    
    # Test weekly demand calculation
    print("\n1. Testing weekly demand calculation:")
    for style in styles:
        demand_stats = generator.calculate_average_weekly_demand(style)
        print(f"   {style}: Avg={demand_stats['avg_weekly_demand']:.1f}, "
              f"StdDev={demand_stats['std_dev']:.1f}, CV={demand_stats['cv']:.2f}")
    
    # Test monthly demand calculation
    print("\n2. Testing monthly demand calculation:")
    for style in styles:
        demand_stats = generator.calculate_monthly_demand(style)
        print(f"   {style}: Avg={demand_stats['avg_monthly_demand']:.1f}, "
              f"Months={demand_stats['num_months']}")
    
    # Test forecast generation
    print("\n3. Testing forecast generation:")
    forecasts = generator.generate_forecasts(apply_seasonality=True, aggregate_by='week')
    print(f"   Generated {len(forecasts)} forecasts")
    for forecast in forecasts[:3]:
        print(f"   {forecast.sku_id}: {forecast.forecast_qty:.1f} {forecast.unit} "
              f"(confidence: {forecast.confidence})")
    
    # Test yarn forecast generation
    print("\n4. Testing yarn forecast generation:")
    yarn_forecasts = generator.generate_yarn_forecasts(forecasts)
    print(f"   Generated forecasts for {len(yarn_forecasts)} yarns")
    for yarn_id, data in yarn_forecasts.items():
        print(f"   {yarn_id}: {data['forecast_qty']:.1f} {data['unit']}")
    
    print("\n✅ Sales Forecast Generator tests completed")
    return True

def test_sales_data_processor():
    """Test the enhanced sales data processor"""
    print("\n" + "="*60)
    print("Testing Sales Data Processor")
    print("="*60)
    
    processor = SalesDataProcessor()
    
    try:
        # Test data loading
        print("\n1. Testing data loading:")
        sales_df = processor.load_and_validate_sales_data()
        print(f"   Loaded {len(sales_df)} sales records")
        
        inventory_df = processor.load_inventory_data()
        print(f"   Loaded {len(inventory_df)} inventory records")
        
        bom_df = processor.load_bom_data()
        print(f"   Loaded {len(bom_df)} BOM records")
        
        # Test sales summary
        print("\n2. Testing sales summary calculation:")
        summary = processor.calculate_sales_summary()
        print(f"   Generated summary for {len(summary)} styles")
        print(f"   Demand patterns: {summary['demand_pattern'].value_counts().to_dict()}")
        
        # Test inventory merge
        print("\n3. Testing sales-inventory merge:")
        merged = processor.merge_sales_with_inventory()
        print(f"   Merged data for {len(merged)} yarns")
        if 'low_stock' in merged.columns:
            low_stock_count = merged['low_stock'].sum()
            print(f"   Low stock items: {low_stock_count}")
        
        # Test validation
        print("\n4. Testing style-yarn mapping validation:")
        validation = processor.validate_style_yarn_mappings()
        print(f"   Missing BOM: {len(validation['missing_bom'])} styles")
        print(f"   Inactive styles: {len(validation['inactive_styles'])}")
        print(f"   Active mapped: {len(validation['active_mapped'])}")
        
        # Test seasonal patterns
        print("\n5. Testing seasonal pattern calculation:")
        seasonal = processor.calculate_seasonal_patterns()
        print(f"   Calculated patterns for {len(seasonal)} styles")
        
        print("\n✅ Sales Data Processor tests completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in Sales Data Processor: {str(e)}")
        return False

def test_sales_planning_integration():
    """Test the complete sales planning integration"""
    print("\n" + "="*60)
    print("Testing Sales Planning Integration")
    print("="*60)
    
    integration = SalesPlanningIntegration()
    
    try:
        # Test validation
        print("\n1. Testing integration validation:")
        validation = integration.validate_integration()
        for check, result in validation.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
        
        # Test sales forecast generation
        print("\n2. Testing sales forecast generation:")
        sales_forecasts = integration.generate_sales_forecasts(aggregate_by='week')
        print(f"   Generated {len(sales_forecasts)} weekly forecasts")
        
        monthly_forecasts = integration.generate_sales_forecasts(aggregate_by='month')
        print(f"   Generated {len(monthly_forecasts)} monthly forecasts")
        
        # Test yarn forecast generation
        print("\n3. Testing yarn forecast generation:")
        yarn_forecasts = integration.generate_yarn_forecasts_from_sales()
        print(f"   Generated forecasts for {len(yarn_forecasts)} yarns")
        
        # Test forecast combination
        print("\n4. Testing forecast combination:")
        # Create some dummy manual forecasts
        manual_forecasts = [
            FinishedGoodsForecast(
                sku_id='STYLE-001',
                forecast_qty=500,
                unit='YDS',
                forecast_date=datetime.now(),
                confidence=0.8,
                source='manual'
            )
        ]
        
        combined = integration.combine_forecasts(
            sales_forecasts[:5],  # Use first 5 sales forecasts
            manual_forecasts,
            []  # No customer orders
        )
        print(f"   Combined into {len(combined)} forecasts")
        
        # Test demand aggregation
        print("\n5. Testing demand aggregation:")
        weekly_demand = integration.generate_demand_aggregation_report('week')
        print(f"   Weekly aggregation: {len(weekly_demand)} periods")
        
        monthly_demand = integration.generate_demand_aggregation_report('month')
        print(f"   Monthly aggregation: {len(monthly_demand)} periods")
        
        # Test safety stock calculation
        print("\n6. Testing safety stock calculation:")
        safety_stock = integration.calculate_safety_stock_requirements()
        print(f"   Calculated safety stock for {len(safety_stock)} yarns")
        if len(safety_stock) > 0:
            avg_weeks = safety_stock['weeks_of_supply'].mean()
            print(f"   Average weeks of supply: {avg_weeks:.1f}")
        
        print("\n✅ Sales Planning Integration tests completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in Sales Planning Integration: {str(e)}")
        logger.error(f"Integration test failed: {str(e)}", exc_info=True)
        return False

def test_end_to_end_workflow():
    """Test the complete end-to-end workflow"""
    print("\n" + "="*60)
    print("Testing End-to-End Workflow")
    print("="*60)
    
    try:
        integration = SalesPlanningIntegration()
        
        # Run integrated planning
        print("\n1. Running integrated planning with sales data...")
        results = integration.run_integrated_planning(aggregate_by='week')
        
        print("\n2. Planning Results:")
        print(f"   Recommendations: {len(results['recommendations'])}")
        print(f"   Forecasts: {len(results['forecasts'])}")
        
        analytics = results['analytics']
        print("\n3. Analytics Summary:")
        print(f"   Sales forecasts: {analytics['forecast_summary']['sales_forecast_count']}")
        print(f"   Combined forecasts: {analytics['forecast_summary']['combined_forecast_count']}")
        print(f"   Total forecast quantity: {analytics['forecast_summary']['total_forecast_quantity']:.0f}")
        print(f"   Average confidence: {analytics['forecast_summary']['avg_confidence']:.2f}")
        
        print("\n4. Inventory Alerts:")
        print(f"   Low stock items: {analytics['inventory_alerts']['low_stock_count']}")
        print(f"   Critical items: {analytics['inventory_alerts']['critical_items']}")
        
        print("\n✅ End-to-End Workflow test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in End-to-End Workflow: {str(e)}")
        logger.error(f"Workflow test failed: {str(e)}", exc_info=True)
        return False

def main():
    """Run all tests"""
    print("\n🧶 Beverly Knits - Sales Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Sales Forecast Generator", test_sales_forecast_generator),
        ("Sales Data Processor", test_sales_data_processor),
        ("Sales Planning Integration", test_sales_planning_integration),
        ("End-to-End Workflow", test_end_to_end_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Sales integration is ready.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")

if __name__ == "__main__":
    main()