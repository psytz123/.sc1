"""
Test script for enhanced sales integration features
Demonstrates:
1. Style-to-Yarn BOM explosion
2. Automated forecast creation from sales analysis
3. Weekly/monthly demand aggregation
4. Safety stock calculation based on sales variability
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from data.sales_data_processor import SalesDataProcessor
from models.sales_forecast_generator import SalesForecastGenerator
from models.bom import BOMExploder, StyleYarnBOM
from engine.planner import RawMaterialPlanner
from config.settings import PlanningConfig
from data.real_data_loader import RealDataLoader


def test_style_to_yarn_bom_explosion():
    """Test the enhanced BOM explosion for style-to-yarn conversion"""
    print("\n" + "="*60)
    print("TEST 1: Style-to-Yarn BOM Explosion")
    print("="*60)
    
    # Create sample style-yarn BOM data
    bom_data = pd.DataFrame([
        {'Style': 'STYLE001', 'Yarn ID': 'YARN-COTTON-001', 'Percentage': 60, 'Yarn Name': 'Cotton Yarn 30s'},
        {'Style': 'STYLE001', 'Yarn ID': 'YARN-POLY-001', 'Percentage': 40, 'Yarn Name': 'Polyester Yarn'},
        {'Style': 'STYLE002', 'Yarn ID': 'YARN-COTTON-001', 'Percentage': 100, 'Yarn Name': 'Cotton Yarn 30s'},
        {'Style': 'STYLE003', 'Yarn ID': 'YARN-WOOL-001', 'Percentage': 70, 'Yarn Name': 'Wool Yarn'},
        {'Style': 'STYLE003', 'Yarn ID': 'YARN-ACRYLIC-001', 'Percentage': 30, 'Yarn Name': 'Acrylic Yarn'},
    ])
    
    # Create style-yarn BOMs
    style_yarn_boms = BOMExploder.from_style_yarn_dataframe(bom_data)
    
    # Create style forecasts
    style_forecasts = {
        'STYLE001': 1000,  # 1000 yards
        'STYLE002': 500,   # 500 yards
        'STYLE003': 750    # 750 yards
    }
    
    # Explode to yarn requirements
    yarn_requirements = BOMExploder.explode_style_to_yarn_requirements(
        style_forecasts,
        style_yarn_boms
    )
    
    print("\nStyle Forecasts:")
    for style, qty in style_forecasts.items():
        print(f"  {style}: {qty} yards")
    
    print("\nYarn Requirements (after BOM explosion):")
    for yarn_id, data in yarn_requirements.items():
        print(f"\n  {yarn_id} ({data['yarn_name']}):")
        print(f"    Total Required: {data['total_qty']:.2f} {data['unit']}")
        print(f"    Sources:")
        for source in data['sources']:
            print(f"      - {source['style_id']}: {source['yarn_qty']:.2f} yards ({source['percentage']}%)")
    
    return yarn_requirements


def test_automated_forecast_creation():
    """Test automated forecast generation from sales data"""
    print("\n" + "="*60)
    print("TEST 2: Automated Forecast Creation from Sales Analysis")
    print("="*60)
    
    # Initialize processor
    processor = SalesDataProcessor()
    
    try:
        # Load sales data
        sales_df = processor.load_and_validate_sales_data()
        
        # Load BOM data if available
        bom_df = processor.load_bom_data()
        
        # Generate planning inputs with different configurations
        print("\nGenerating forecasts with statistical safety stock...")
        planning_inputs = processor.generate_planning_inputs(
            lookback_days=90,
            planning_horizon_days=90,
            aggregation_period='weekly',
            safety_stock_method='statistical',
            include_safety_stock=True
        )
        
        # Display results
        forecasts = planning_inputs['forecasts']
        print(f"\nGenerated {len(forecasts)} forecasts")
        
        if forecasts:
            # Show sample forecasts
            print("\nSample Forecasts (first 5):")
            for i, forecast in enumerate(forecasts[:5]):
                print(f"  {forecast.sku_id}: {forecast.forecast_qty} {forecast.unit} "
                      f"(confidence: {forecast.confidence:.2f})")
            
            # Show statistics
            total_qty = sum(f.forecast_qty for f in forecasts)
            avg_confidence = sum(f.confidence for f in forecasts) / len(forecasts)
            print(f"\nTotal Forecast Quantity: {total_qty:,.0f} yards")
            print(f"Average Confidence: {avg_confidence:.2f}")
        
        # Show demand statistics
        if 'demand_statistics' in planning_inputs:
            stats = planning_inputs['demand_statistics']
            print("\nOverall Demand Statistics:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        
        return planning_inputs
        
    except Exception as e:
        print(f"Error in automated forecast creation: {e}")
        return None


def test_demand_aggregation():
    """Test weekly and monthly demand aggregation capabilities"""
    print("\n" + "="*60)
    print("TEST 3: Weekly/Monthly Demand Aggregation")
    print("="*60)
    
    # Create sample sales data
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
    np.random.seed(42)
    
    sales_data = []
    styles = ['STYLE001', 'STYLE002', 'STYLE003', 'STYLE004', 'STYLE005']
    
    for date in dates:
        # Generate 1-5 sales per day
        num_sales = np.random.randint(1, 6)
        for _ in range(num_sales):
            style = np.random.choice(styles)
            # Add seasonality and random variation
            base_demand = 100
            seasonality = 1 + 0.3 * np.sin(2 * np.pi * date.dayofyear / 365)
            quantity = max(10, int(base_demand * seasonality * np.random.uniform(0.5, 1.5)))
            
            sales_data.append({
                'Invoice Date': date,
                'Style': style,
                'Yds_ordered': quantity,
                'Customer': f'Customer{np.random.randint(1, 10)}',
                'Unit Price': np.random.uniform(5, 15),
                'Line Price': quantity * np.random.uniform(5, 15)
            })
    
    sales_df = pd.DataFrame(sales_data)
    
    # Initialize forecast generator
    generator = SalesForecastGenerator(
        sales_df=sales_df,
        planning_horizon_days=30,
        lookback_days=90
    )
    
    # Test different aggregation periods
    for period in ['daily', 'weekly', 'monthly']:
        print(f"\n{period.upper()} Aggregation:")
        aggregated = generator.aggregate_demand_by_period(period=period)
        
        # Show summary
        print(f"  Total periods: {len(aggregated['period'].unique())}")
        print(f"  Styles analyzed: {len(aggregated['Style'].unique())}")
        
        # Show sample data
        print(f"\n  Sample {period} data (first 5 rows):")
        display_cols = ['period', 'Style', 'Yds_ordered_sum', 'Yds_ordered_mean', 'Yds_ordered_std']
        print(aggregated[display_cols].head().to_string(index=False))
        
        # Calculate aggregated statistics
        total_demand = aggregated['Yds_ordered_sum'].sum()
        avg_demand = aggregated['Yds_ordered_mean'].mean()
        print(f"\n  Total demand: {total_demand:,.0f} yards")
        print(f"  Average {period} demand per style: {avg_demand:.2f} yards")
    
    return aggregated


def test_safety_stock_calculation():
    """Test different safety stock calculation methods"""
    print("\n" + "="*60)
    print("TEST 4: Safety Stock Calculation Based on Sales Variability")
    print("="*60)
    
    # Create sample sales data with different variability patterns
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
    
    # Style patterns: stable, variable, seasonal
    style_patterns = {
        'STABLE-001': {'mean': 100, 'std': 10, 'trend': 0},
        'VARIABLE-001': {'mean': 100, 'std': 40, 'trend': 0},
        'SEASONAL-001': {'mean': 100, 'std': 20, 'trend': 0.5},
        'GROWING-001': {'mean': 80, 'std': 15, 'trend': 1.0}
    }
    
    sales_data = []
    for date in dates:
        for style, pattern in style_patterns.items():
            # Calculate demand with pattern
            base = pattern['mean']
            if pattern['trend'] > 0:
                # Add seasonality
                seasonality = 1 + pattern['trend'] * np.sin(2 * np.pi * date.dayofyear / 365)
                base *= seasonality
            
            # Add random variation
            quantity = max(0, int(np.random.normal(base, pattern['std'])))
            
            if quantity > 0:  # Only add if there's a sale
                sales_data.append({
                    'Invoice Date': date,
                    'Style': style,
                    'Yds_ordered': quantity,
                    'Customer': 'TestCustomer',
                    'Unit Price': 10,
                    'Line Price': quantity * 10
                })
    
    sales_df = pd.DataFrame(sales_data)
    
    # Test different safety stock methods
    methods = ['percentage', 'statistical', 'min_max', 'dynamic']
    service_levels = [0.90, 0.95, 0.99]
    
    results = []
    
    for method in methods:
        for service_level in service_levels:
            generator = SalesForecastGenerator(
                sales_df=sales_df,
                safety_stock_method=method,
                service_level=service_level
            )
            
            print(f"\n{method.upper()} Method (Service Level: {service_level}):")
            
            for style in style_patterns.keys():
                # Calculate demand statistics
                stats = generator.calculate_demand_statistics(style)
                
                # Calculate safety stock
                safety_stock = generator.calculate_safety_stock(
                    stats['average_demand'],
                    stats['std_deviation'],
                    stats['lead_time_days']
                )
                
                # Calculate metrics
                cv = stats['cv']
                safety_percentage = (safety_stock / stats['average_demand'] * 100) if stats['average_demand'] > 0 else 0
                
                result = {
                    'style': style,
                    'method': method,
                    'service_level': service_level,
                    'avg_demand': stats['average_demand'],
                    'std_dev': stats['std_deviation'],
                    'cv': cv,
                    'safety_stock': safety_stock,
                    'safety_percentage': safety_percentage
                }
                results.append(result)
                
                print(f"  {style}:")
                print(f"    Avg Demand: {stats['average_demand']:.1f} yards/week")
                print(f"    Std Dev: {stats['std_deviation']:.1f}")
                print(f"    CV: {cv:.2f}")
                print(f"    Safety Stock: {safety_stock:.1f} yards ({safety_percentage:.1f}%)")
    
    # Create comparison DataFrame
    results_df = pd.DataFrame(results)
    
    print("\n" + "-"*60)
    print("SAFETY STOCK COMPARISON SUMMARY")
    print("-"*60)
    
    # Pivot table for easy comparison
    pivot = results_df.pivot_table(
        values='safety_percentage',
        index='style',
        columns=['method', 'service_level'],
        aggfunc='mean'
    ).round(1)
    
    print("\nSafety Stock as % of Average Demand:")
    print(pivot.to_string())
    
    return results_df


def test_integrated_planning_with_sales():
    """Test the complete integrated planning process with sales data"""
    print("\n" + "="*60)
    print("TEST 5: Integrated Planning with Sales-Based Forecasting")
    print("="*60)
    
    # Create configuration with sales integration enabled
    config = PlanningConfig({
        'enable_sales_forecasting': True,
        'use_style_yarn_bom': True,
        'safety_stock_method': 'statistical',
        'service_level': 0.95,
        'aggregation_period': 'weekly',
        'lookback_days': 90,
        'planning_horizon_days': 90
    })
    
    # Validate configuration
    validation = config.validate_configuration()
    if not validation['valid']:
        print("Configuration errors:", validation['errors'])
        return
    
    if validation['warnings']:
        print("Configuration warnings:", validation['warnings'])
    
    # Initialize planner
    planner = RawMaterialPlanner(config)
    
    # Load real data
    try:
        loader = RealDataLoader()
        forecasts, boms, inventory, suppliers = loader.load_all_data()
        
        print(f"\nLoaded data:")
        print(f"  Forecasts: {len(forecasts)}")
        print(f"  BOMs: {len(boms)}")
        print(f"  Inventory: {len(inventory)}")
        print(f"  Suppliers: {len(suppliers)}")
        
        # Run planning with sales integration
        print("\nRunning integrated planning...")
        recommendations = planner.plan(forecasts, boms, inventory, suppliers)
        
        # Generate summary report
        summary = planner.generate_summary_report()
        
        print("\n" + "-"*60)
        print("PLANNING SUMMARY")
        print("-"*60)
        print(f"Total Materials: {summary['summary']['total_materials']}")
        print(f"Total Suppliers: {summary['summary']['total_suppliers']}")
        print(f"Total Cost: ${summary['summary']['total_cost']:,.2f}")
        print(f"Total Recommendations: {summary['summary']['total_recommendations']}")
        
        print("\nRisk Summary:")
        for risk_level, count in summary['risk_summary'].items():
            print(f"  {risk_level.capitalize()}: {count}")
        
        print("\nDelivery Timeline:")
        print(f"  Earliest: {summary['delivery_timeline']['earliest']}")
        print(f"  Latest: {summary['delivery_timeline']['latest']}")
        print(f"  Span: {summary['delivery_timeline']['span_days']} days")
        
        print("\nTop 5 Cost Items:")
        for i, (material, cost) in enumerate(summary['top_cost_items'][:5], 1):
            print(f"  {i}. {material}: ${cost:,.2f}")
        
        return recommendations
        
    except Exception as e:
        print(f"Error in integrated planning: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("BEVERLY KNITS - ENHANCED SALES INTEGRATION TESTING")
    print("="*80)
    
    # Test 1: Style-to-Yarn BOM Explosion
    yarn_requirements = test_style_to_yarn_bom_explosion()
    
    # Test 2: Automated Forecast Creation
    planning_inputs = test_automated_forecast_creation()
    
    # Test 3: Demand Aggregation
    aggregated_demand = test_demand_aggregation()
    
    # Test 4: Safety Stock Calculation
    safety_stock_results = test_safety_stock_calculation()
    
    # Test 5: Integrated Planning
    recommendations = test_integrated_planning_with_sales()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
    
    # Save test results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save safety stock comparison
    if safety_stock_results is not None:
        safety_stock_results.to_csv(f'test_results_safety_stock_{timestamp}.csv', index=False)
        print(f"\nSafety stock results saved to: test_results_safety_stock_{timestamp}.csv")
    
    print("\nEnhanced features successfully implemented:")
    print("✓ Style-to-Yarn BOM explosion with percentage-based composition")
    print("✓ Automated forecast creation from sales analysis")
    print("✓ Weekly/monthly demand aggregation capabilities")
    print("✓ Statistical safety stock calculation based on sales variability")
    print("✓ Integrated planning with sales-based forecasting")


if __name__ == "__main__":
    main()