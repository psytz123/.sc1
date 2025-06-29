"""
Test script for enhanced sales forecast generator with seasonality detection
"""

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from models.sales_forecast_generator import SalesForecastGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_sales_data():
    """Create sample sales data with seasonal patterns"""
    # Generate 2 years of sales data
    start_date = datetime.now() - timedelta(days=730)
    end_date = datetime.now()
    
    # Create styles with different seasonal patterns
    styles = {
        'SUMMER-001': {'base': 1000, 'summer_peak': True},
        'WINTER-001': {'base': 800, 'winter_peak': True},
        'STABLE-001': {'base': 500, 'no_season': True},
        'GROWING-001': {'base': 300, 'growth': 0.02}  # 2% monthly growth
    }
    
    sales_data = []
    current_date = start_date
    
    while current_date <= end_date:
        for style, params in styles.items():
            # Base demand
            base_demand = params['base']
            
            # Apply seasonality
            month = current_date.month
            seasonal_factor = 1.0
            
            if params.get('summer_peak'):
                # Peak in summer (June-August)
                if month in [6, 7, 8]:
                    seasonal_factor = 1.5
                elif month in [12, 1, 2]:
                    seasonal_factor = 0.7
                    
            elif params.get('winter_peak'):
                # Peak in winter (December-February)
                if month in [12, 1, 2]:
                    seasonal_factor = 1.6
                elif month in [6, 7, 8]:
                    seasonal_factor = 0.6
                    
            # Apply growth
            if 'growth' in params:
                months_elapsed = (current_date - start_date).days / 30
                growth_factor = (1 + params['growth']) ** months_elapsed
                base_demand *= growth_factor
            
            # Add random variation
            daily_demand = base_demand / 30 * seasonal_factor
            actual_demand = max(0, np.random.normal(daily_demand, daily_demand * 0.2))
            
            if actual_demand > 0:
                sales_data.append({
                    'Invoice Date': current_date,
                    'Style': style,
                    'Yds_ordered': int(actual_demand),
                    'Line Price': actual_demand * np.random.uniform(10, 20)
                })
        
        current_date += timedelta(days=np.random.randint(1, 4))  # Random 1-3 days between orders
    
    return pd.DataFrame(sales_data)

def test_seasonality_detection():
    """Test the seasonality detection functionality"""
    print("=== Testing Sales Forecast Generator with Seasonality Detection ===\n")
    
    # Create sample data
    sales_df = create_sample_sales_data()
    print(f"Generated {len(sales_df)} sales records")
    print(f"Date range: {sales_df['Invoice Date'].min()} to {sales_df['Invoice Date'].max()}")
    print(f"Styles: {sales_df['Style'].unique()}\n")
    
    # Initialize forecast generator
    generator = SalesForecastGenerator(
        sales_df=sales_df,
        planning_horizon_days=90,
        lookback_days=365,
        min_history_days=30,
        aggregation_period='weekly',
        safety_stock_method='statistical',
        service_level=0.95
    )
    
    # Test seasonality detection for each style
    print("=== Seasonality Pattern Detection ===")
    for style in sales_df['Style'].unique():
        print(f"\nStyle: {style}")
        seasonality_factors = generator.detect_seasonality_patterns(style)
        
        if seasonality_factors:
            print("Monthly seasonality factors:")
            for month in range(1, 13):
                factor = seasonality_factors.get(month, 1.0)
                month_name = datetime(2024, month, 1).strftime('%B')
                bar = '█' * int(factor * 20)
                print(f"  {month_name:10}: {factor:.3f} {bar}")
    
    # Test weekly average demand calculation
    print("\n=== Weekly Average Demand Analysis ===")
    for style in sales_df['Style'].unique():
        weekly_stats = generator.calculate_weekly_average_demand(style, apply_seasonality=True)
        print(f"\nStyle: {style}")
        print(f"  Weekly average: {weekly_stats['weekly_avg']:.1f} yards")
        print(f"  Weekly min/max: {weekly_stats['weekly_min']:.1f} - {weekly_stats['weekly_max']:.1f} yards")
        print(f"  Seasonally adjusted: {weekly_stats['seasonally_adjusted']:.1f} yards")
        print(f"  Coefficient of variation: {weekly_stats['cv']:.3f}")
        print(f"  Confidence: {weekly_stats['confidence']:.2%}")
    
    # Generate forecasts with automatic seasonality
    print("\n=== Generating Forecasts with Auto-Seasonality ===")
    forecasts = generator.generate_forecasts_with_auto_seasonality(
        include_safety_stock=True,
        growth_factor=1.0,
        auto_detect_seasonality=True
    )
    
    print(f"\nGenerated {len(forecasts)} forecasts:")
    for forecast in forecasts:
        print(f"  {forecast.sku_id}: {forecast.forecast_qty:,} yards")
        print(f"    Confidence: {forecast.confidence:.2%}")
        print(f"    Notes: {forecast.notes}")
    
    # Compare with non-seasonal forecasts
    print("\n=== Comparison: With vs Without Seasonality ===")
    forecasts_no_season = generator.generate_forecasts(
        include_safety_stock=True,
        growth_factor=1.0,
        seasonality_factors=None
    )
    
    comparison_data = []
    for f_season in forecasts:
        f_no_season = next((f for f in forecasts_no_season if f.sku_id == f_season.sku_id), None)
        if f_no_season:
            diff = f_season.forecast_qty - f_no_season.forecast_qty
            pct_diff = (diff / f_no_season.forecast_qty * 100) if f_no_season.forecast_qty > 0 else 0
            comparison_data.append({
                'Style': f_season.sku_id,
                'With Seasonality': f_season.forecast_qty,
                'Without Seasonality': f_no_season.forecast_qty,
                'Difference': diff,
                'Pct Difference': f"{pct_diff:.1f}%"
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n", comparison_df.to_string(index=False))
    
    # Create forecast summary
    print("\n=== Forecast Summary ===")
    summary_df = generator.create_forecast_summary(forecasts)
    print(summary_df.to_string(index=False))

if __name__ == "__main__":
    test_seasonality_detection()