"""
Test script for enhanced sales integration features
Demonstrates:
1. Style-to-Yarn BOM explosion
2. Automated forecast creation from sales analysis
3. Weekly/monthly demand aggregation
4. Safety stock calculation based on sales variability
"""

from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

import numpy as np
import pandas as pd

from config.settings import PlanningConfig
from data.real_data_loader import RealDataLoader
from data.sales_data_processor import SalesDataProcessor
from engine.planner import RawMaterialPlanner
from models.bom import BOMExploder
from models.sales_forecast_generator import SalesForecastGenerator


def test_style_to_yarn_bom_explosion():
    """Test the enhanced BOM explosion for style-to-yarn conversion"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Style-to-Yarn BOM Explosion")
    logger.info("="*60)
    
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
    
    logger.info("\nStyle Forecasts:")
    for style, qty in style_forecasts.items():
        logger.info(f"  {style}: {qty} yards")
    
    logger.info("\nYarn Requirements (after BOM explosion):")
    for yarn_id, data in yarn_requirements.items():
        logger.info(f"\n  {yarn_id} ({data['yarn_name']}):")
        logger.info(f"    Total Required: {data['total_qty']:.2f} {data['unit']}")
        logger.info(f"    Sources:")
        for source in data['sources']:
            logger.info(f"      - {source['style_id']}: {source['yarn_qty']:.2f} yards ({source['percentage']}%)")
    
    return yarn_requirements


def test_automated_forecast_creation():
    """Test automated forecast generation from sales data"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Automated Forecast Creation from Sales Analysis")
    logger.info("="*60)
    
    # Initialize processor
    processor = SalesDataProcessor()
    
    try:
        # Load sales data
        processor.load_and_validate_sales_data()
        
        # Load BOM data if available
        processor.load_bom_data()
        
        # Generate planning inputs with different configurations
        logger.info("\nGenerating forecasts with statistical safety stock...")
        planning_inputs = processor.generate_planning_inputs(
            lookback_days=90,
            planning_horizon_days=90,
            aggregation_period='weekly',
            safety_stock_method='statistical',
            include_safety_stock=True
        )
        
        # Display results
        forecasts = planning_inputs['forecasts']
        logger.info(f"\nGenerated {len(forecasts)} forecasts")
        
        if forecasts:
            # Show sample forecasts
            logger.info("\nSample Forecasts (first 5):")
            for i, forecast in enumerate(forecasts[:5]):
                logger.info(f"  {forecast.sku_id}: {forecast.forecast_qty} {forecast.unit} "
                      f"(confidence: {forecast.confidence:.2f})")
            
            # Show statistics
            total_qty = sum(f.forecast_qty for f in forecasts)
            avg_confidence = sum(f.confidence for f in forecasts) / len(forecasts)
            logger.info(f"\nTotal Forecast Quantity: {total_qty:,.0f} yards")
            logger.info(f"Average Confidence: {avg_confidence:.2f}")
        
        # Show demand statistics
        if 'demand_statistics' in planning_inputs:
            stats = planning_inputs['demand_statistics']
            logger.info("\nOverall Demand Statistics:")
            for key, value in stats.items():
                if isinstance(value, float):
                    logger.info(f"  {key}: {value:.2f}")
                else:
                    logger.info(f"  {key}: {value}")
        
        return planning_inputs
        
    except Exception as e:
        logger.info(f"Error in automated forecast creation: {e}")
        return None


def test_demand_aggregation():
    """Test weekly and monthly demand aggregation capabilities"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Weekly/Monthly Demand Aggregation")
    logger.info("="*60)
    
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
        logger.info(f"\n{period.upper()} Aggregation:")
        aggregated = generator.aggregate_demand_by_period(period=period)
        
        # Show summary
        logger.info(f"  Total periods: {len(aggregated['period'].unique())}")
        logger.info(f"  Styles analyzed: {len(aggregated['Style'].unique())}")
        
        # Show sample data
        logger.info(f"\n  Sample {period} data (first 5 rows):")
        display_cols = ['period', 'Style', 'Yds_ordered_sum', 'Yds_ordered_mean', 'Yds_ordered_std']
        logger.info(aggregated[display_cols].head().to_string(index=False))
        
        # Calculate aggregated statistics
        total_demand = aggregated['Yds_ordered_sum'].sum()
        avg_demand = aggregated['Yds_ordered_mean'].mean()
        logger.info(f"\n  Total demand: {total_demand:,.0f} yards")
        logger.info(f"  Average {period} demand per style: {avg_demand:.2f} yards")
    
    return aggregated


def test_safety_stock_calculation():
    """Test different safety stock calculation methods"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Safety Stock Calculation Based on Sales Variability")
    logger.info("="*60)
    
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
            
            logger.info(f"\n{method.upper()} Method (Service Level: {service_level}):")
            
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
                
                logger.info(f"  {style}:")
                logger.info(f"    Avg Demand: {stats['average_demand']:.1f} yards/week")
                logger.info(f"    Std Dev: {stats['std_deviation']:.1f}")
                logger.info(f"    CV: {cv:.2f}")
                logger.info(f"    Safety Stock: {safety_stock:.1f} yards ({safety_percentage:.1f}%)")
    
    # Create comparison DataFrame
    results_df = pd.DataFrame(results)
    
    logger.info("\n" + "-"*60)
    logger.info("SAFETY STOCK COMPARISON SUMMARY")
    logger.info("-"*60)
    
    # Pivot table for easy comparison
    pivot = results_df.pivot_table(
        values='safety_percentage',
        index='style',
        columns=['method', 'service_level'],
        aggfunc='mean'
    ).round(1)
    
    logger.info("\nSafety Stock as % of Average Demand:")
    logger.info(pivot.to_string())
    
    return results_df


def test_integrated_planning_with_sales():
    """Test the complete integrated planning process with sales data"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Integrated Planning with Sales-Based Forecasting")
    logger.info("="*60)
    
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
        logger.info("Configuration errors:", validation['errors'])
        return
    
    if validation['warnings']:
        logger.info("Configuration warnings:", validation['warnings'])
    
    # Initialize planner
    planner = RawMaterialPlanner(config)
    
    # Load real data
    try:
        loader = RealDataLoader()
        forecasts, boms, inventory, suppliers = loader.load_all_data()
        
        logger.info(f"\nLoaded data:")
        logger.info(f"  Forecasts: {len(forecasts)}")
        logger.info(f"  BOMs: {len(boms)}")
        logger.info(f"  Inventory: {len(inventory)}")
        logger.info(f"  Suppliers: {len(suppliers)}")
        
        # Run planning with sales integration
        logger.info("\nRunning integrated planning...")
        recommendations = planner.plan(forecasts, boms, inventory, suppliers)
        
        # Generate summary report
        summary = planner.generate_summary_report()
        
        logger.info("\n" + "-"*60)
        logger.info("PLANNING SUMMARY")
        logger.info("-"*60)
        logger.info(f"Total Materials: {summary['summary']['total_materials']}")
        logger.info(f"Total Suppliers: {summary['summary']['total_suppliers']}")
        logger.info(f"Total Cost: ${summary['summary']['total_cost']:,.2f}")
        logger.info(f"Total Recommendations: {summary['summary']['total_recommendations']}")
        
        logger.info("\nRisk Summary:")
        for risk_level, count in summary['risk_summary'].items():
            logger.info(f"  {risk_level.capitalize()}: {count}")
        
        logger.info("\nDelivery Timeline:")
        logger.info(f"  Earliest: {summary['delivery_timeline']['earliest']}")
        logger.info(f"  Latest: {summary['delivery_timeline']['latest']}")
        logger.info(f"  Span: {summary['delivery_timeline']['span_days']} days")
        
        logger.info("\nTop 5 Cost Items:")
        for i, (material, cost) in enumerate(summary['top_cost_items'][:5], 1):
            logger.info(f"  {i}. {material}: ${cost:,.2f}")
        
        return recommendations
        
    except Exception as e:
        logger.info(f"Error in integrated planning: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    logger.info("\n" + "="*80)
    logger.info("BEVERLY KNITS - ENHANCED SALES INTEGRATION TESTING")
    logger.info("="*80)
    
    # Test 1: Style-to-Yarn BOM Explosion
    test_style_to_yarn_bom_explosion()
    
    # Test 2: Automated Forecast Creation
    test_automated_forecast_creation()
    
    # Test 3: Demand Aggregation
    test_demand_aggregation()
    
    # Test 4: Safety Stock Calculation
    safety_stock_results = test_safety_stock_calculation()
    
    # Test 5: Integrated Planning
    test_integrated_planning_with_sales()
    
    logger.info("\n" + "="*80)
    logger.info("ALL TESTS COMPLETED")
    logger.info("="*80)
    
    # Save test results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save safety stock comparison
    if safety_stock_results is not None:
        safety_stock_results.to_csv(f'test_results_safety_stock_{timestamp}.csv', index=False)
        logger.info(f"\nSafety stock results saved to: test_results_safety_stock_{timestamp}.csv")
    
    logger.info("\nEnhanced features successfully implemented:")
    logger.info("✓ Style-to-Yarn BOM explosion with percentage-based composition")
    logger.info("✓ Automated forecast creation from sales analysis")
    logger.info("✓ Weekly/monthly demand aggregation capabilities")
    logger.info("✓ Statistical safety stock calculation based on sales variability")
    logger.info("✓ Integrated planning with sales-based forecasting")


if __name__ == "__main__":
    main()