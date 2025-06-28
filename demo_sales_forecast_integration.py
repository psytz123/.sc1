"""
Integration example: Sales Forecast Generator with Planning System
Demonstrates how to use historical sales data to generate forecasts for the planning engine
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from models.sales_forecast_generator import SalesForecastGenerator
from models.forecast import ForecastProcessor
from engine.planner import RawMaterialPlanner
from models.bom import BillOfMaterials
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_real_sales_data():
    """Load real sales data from CSV file"""
    try:
        # Load the actual sales data
        sales_df = pd.read_csv('data/cfab_Sales_Orders_Data.csv')
        
        # Ensure date column is datetime
        if 'Invoice Date' in sales_df.columns:
            sales_df['Invoice Date'] = pd.to_datetime(sales_df['Invoice Date'])
        
        # Filter to recent data (last 2 years)
        cutoff_date = datetime.now() - timedelta(days=730)
        sales_df = sales_df[sales_df['Invoice Date'] >= cutoff_date]
        
        logger.info(f"Loaded {len(sales_df)} sales records from {sales_df['Invoice Date'].min()} to {sales_df['Invoice Date'].max()}")
        return sales_df
        
    except FileNotFoundError:
        logger.warning("Sales data file not found. Using sample data.")
        return create_sample_sales_data()

def create_sample_sales_data():
    """Create sample sales data if real data is not available"""
    # Generate 2 years of sales data
    start_date = datetime.now() - timedelta(days=730)
    end_date = datetime.now()
    
    # Sample styles
    styles = ['STYLE-001', 'STYLE-002', 'STYLE-003', 'STYLE-004', 'STYLE-005']
    
    sales_data = []
    current_date = start_date
    
    while current_date <= end_date:
        for style in styles:
            if np.random.random() > 0.3:  # 70% chance of order on any given day
                quantity = np.random.normal(500, 100)
                if quantity > 0:
                    sales_data.append({
                        'Invoice Date': current_date,
                        'Style': style,
                        'Yds_ordered': int(quantity),
                        'Line Price': quantity * np.random.uniform(10, 20)
                    })
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(sales_data)

def integrate_sales_forecasts_with_planner():
    """Main integration function"""
    print("=== Sales Forecast Integration with Planning System ===\n")
    
    # Step 1: Load sales data
    print("Step 1: Loading sales data...")
    sales_df = load_real_sales_data()
    print(f"  Loaded {len(sales_df)} sales records")
    print(f"  Unique styles: {sales_df['Style'].nunique()}")
    print(f"  Date range: {sales_df['Invoice Date'].min()} to {sales_df['Invoice Date'].max()}\n")
    
    # Step 2: Initialize forecast generator
    print("Step 2: Initializing forecast generator...")
    generator = SalesForecastGenerator(
        sales_df=sales_df,
        planning_horizon_days=90,  # 3-month planning horizon
        lookback_days=365,         # Use 1 year of history
        min_history_days=30,       # Minimum 30 days required
        aggregation_period='weekly',
        safety_stock_method='statistical',
        service_level=0.95
    )
    print("  Generator initialized with weekly aggregation and statistical safety stock\n")
    
    # Step 3: Detect seasonality patterns
    print("Step 3: Detecting seasonality patterns...")
    # Get top 5 styles by volume
    top_styles = sales_df.groupby('Style')['Yds_ordered'].sum().nlargest(5).index.tolist()
    
    for style in top_styles[:3]:  # Show first 3 for brevity
        seasonality = generator.detect_seasonality_patterns(style)
        if seasonality:
            print(f"\n  {style} seasonality factors:")
            for month in [1, 4, 7, 10]:  # Show quarterly
                factor = seasonality.get(month, 1.0)
                month_name = datetime(2024, month, 1).strftime('%B')
                print(f"    {month_name}: {factor:.2f}")
    
    # Step 4: Generate forecasts with auto-seasonality
    print("\n\nStep 4: Generating forecasts with automatic seasonality detection...")
    forecasts = generator.generate_forecasts_with_auto_seasonality(
        include_safety_stock=True,
        growth_factor=1.05,  # 5% growth assumption
        auto_detect_seasonality=True
    )
    
    print(f"  Generated {len(forecasts)} forecasts")
    
    # Show top 5 forecasts
    print("\n  Top 5 forecasts by quantity:")
    sorted_forecasts = sorted(forecasts, key=lambda x: x.forecast_qty, reverse=True)
    for i, forecast in enumerate(sorted_forecasts[:5]):
        print(f"    {i+1}. {forecast.sku_id}: {forecast.forecast_qty:,} yards (confidence: {forecast.confidence:.1%})")
    
    # Step 5: Calculate weekly averages
    print("\n\nStep 5: Weekly demand analysis for top styles...")
    for style in top_styles[:3]:
        weekly_stats = generator.calculate_weekly_average_demand(style, apply_seasonality=True)
        print(f"\n  {style}:")
        print(f"    Weekly average: {weekly_stats['weekly_avg']:.1f} yards")
        print(f"    Seasonally adjusted: {weekly_stats['seasonally_adjusted']:.1f} yards")
        print(f"    Variability (CV): {weekly_stats['cv']:.2f}")
    
    # Step 6: Create forecast summary
    print("\n\nStep 6: Creating forecast summary...")
    summary_df = generator.create_forecast_summary(forecasts)
    
    # Calculate totals by confidence level
    confidence_summary = pd.DataFrame()
    if len(forecasts) > 0:
        forecast_data = pd.DataFrame([{
            'sku_id': f.sku_id,
            'forecast_qty': f.forecast_qty,
            'confidence': f.confidence
        } for f in forecasts])
        
        # Group by confidence bands
        forecast_data['confidence_band'] = pd.cut(
            forecast_data['confidence'], 
            bins=[0, 0.5, 0.7, 0.9, 1.0],
            labels=['Low (<50%)', 'Medium (50-70%)', 'High (70-90%)', 'Very High (>90%)']
        )
        
        confidence_summary = forecast_data.groupby('confidence_band')['forecast_qty'].agg(['count', 'sum'])
        confidence_summary.columns = ['Number of Styles', 'Total Quantity']
        
        print("\n  Forecast summary by confidence level:")
        print(confidence_summary.to_string())
    
    # Step 7: Integration with planning system
    print("\n\nStep 7: Integration with planning system...")
    print("  The generated forecasts can now be used with the RawMaterialPlanner:")
    print("  - Forecasts are in FinishedGoodsForecast format")
    print("  - Source is marked as 'sales_history'")
    print("  - Confidence scores help prioritize planning")
    print("  - Seasonality adjustments improve accuracy")
    
    # Show how to use with planner (conceptual)
    print("\n  Example usage:")
    print("  ```python")
    print("  # Initialize planner with generated forecasts")
    print("  planner = RawMaterialPlanner(")
    print("      forecasts=forecasts,  # From sales forecast generator")
    print("      bom=bom_data,")
    print("      current_inventory=inventory_data,")
    print("      suppliers=supplier_data")
    print("  )")
    print("  ")
    print("  # Run planning process")
    print("  recommendations = planner.plan()")
    print("  ```")
    
    # Save forecasts to CSV for review
    if len(forecasts) > 0:
        output_df = pd.DataFrame([{
            'style_id': f.sku_id,
            'forecast_qty': f.forecast_qty,
            'forecast_date': f.forecast_date,
            'source': f.source,
            'confidence': f.confidence,
            'notes': f.notes
        } for f in forecasts])
        
        output_file = 'sales_based_forecasts.csv'
        output_df.to_csv(output_file, index=False)
        print(f"\n  Forecasts saved to: {output_file}")
    
    return forecasts, generator

if __name__ == "__main__":
    forecasts, generator = integrate_sales_forecasts_with_planner()
    
    print("\n\n=== Summary ===")
    print(f"Successfully generated {len(forecasts)} forecasts from historical sales data")
    print("These forecasts include:")
    print("  ✓ Automatic seasonality detection and adjustment")
    print("  ✓ Statistical safety stock calculation")
    print("  ✓ Confidence scoring based on demand variability")
    print("  ✓ Weekly demand averaging")
    print("  ✓ Compatible format for planning system integration")