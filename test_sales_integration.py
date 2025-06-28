"""
Test Suite for Sales Integration Components
Tests the sales forecast generator, data processor, and integration
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from models.sales_forecast_generator import SalesForecastGenerator
from data.sales_data_processor import SalesDataProcessor
from engine.sales_planning_integration import SalesPlanningIntegration
from models.forecast import FinishedGoodsForecast

class TestSalesForecastGenerator(unittest.TestCase):
    """Test the sales forecast generator"""
    
    def setUp(self):
        """Create sample sales data"""
        # Generate sample sales data
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        styles = ['STYLE001', 'STYLE002', 'STYLE003']
        
        sales_data = []
        for _ in range(200):
            sales_data.append({
                'Invoice Date': np.random.choice(dates),
                'Style': np.random.choice(styles),
                'Yds_ordered': np.random.uniform(50, 500),
                'Customer': f'Customer{np.random.randint(1, 10)}',
                'Unit Price': np.random.uniform(5, 20)
            })
        
        self.sales_df = pd.DataFrame(sales_data)
        
    def test_forecast_generation(self):
        """Test basic forecast generation"""
        generator = SalesForecastGenerator(self.sales_df, planning_horizon_days=30)
        forecasts = generator.generate_forecasts()
        
        self.assertGreater(len(forecasts), 0)
        self.assertLessEqual(len(forecasts), 3)  # Max 3 styles
        
        # Check forecast structure
        for forecast in forecasts:
            self.assertIsInstance(forecast, FinishedGoodsForecast)
            self.assertGreater(forecast.forecast_qty, 0)
            self.assertEqual(forecast.unit, 'yards')
            self.assertEqual(forecast.source, 'sales_history')
            
    def test_weekly_demand_calculation(self):
        """Test weekly demand calculation"""
        generator = SalesForecastGenerator(self.sales_df)
        
        # Test for a specific style
        style = 'STYLE001'
        demand_stats = generator.calculate_average_weekly_demand(style)
        
        self.assertIn('avg_weekly_demand', demand_stats)
        self.assertIn('std_dev', demand_stats)
        self.assertIn('num_weeks', demand_stats)
        self.assertGreaterEqual(demand_stats['avg_weekly_demand'], 0)
        
    def test_safety_stock_calculation(self):
        """Test safety stock calculation"""
        generator = SalesForecastGenerator(self.sales_df)
        
        # Test with known values
        safety_stock = generator.calculate_safety_stock(
            avg_demand=100,
            std_dev=20,
            service_level=0.95
        )
        
        self.assertGreater(safety_stock, 0)
        # For 95% service level with 2 week lead time, should be ~46.7
        self.assertAlmostEqual(safety_stock, 46.7, delta=1)
        
    def test_seasonality_application(self):
        """Test seasonal adjustment"""
        generator = SalesForecastGenerator(self.sales_df)
        
        base_demand = 1000
        # Test winter month (lower demand)
        winter_demand = generator.apply_seasonality_factor(base_demand, 1)
        self.assertLess(winter_demand, base_demand)
        
        # Test fall month (higher demand)
        fall_demand = generator.apply_seasonality_factor(base_demand, 10)
        self.assertGreater(fall_demand, base_demand)


class TestSalesDataProcessor(unittest.TestCase):
    """Test the sales data processor"""
    
    def setUp(self):
        """Create temporary directory with test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / 'data'
        self.data_dir.mkdir()
        
        # Create sample sales data file
        sales_data = pd.DataFrame({
            'Invoice Date': pd.date_range(end=datetime.now(), periods=50),
            'Style': ['STYLE001'] * 25 + ['STYLE002'] * 25,
            'Yds_ordered': np.random.uniform(100, 500, 50),
            'Customer': [f'Customer{i%5}' for i in range(50)],
            'Unit Price': ['$10.50'] * 50,
            'Line Price': ['$525.00'] * 50
        })
        sales_data.to_csv(self.data_dir / 'Sales Activity Report.csv', index=False)
        
        # Create sample inventory data
        inventory_data = pd.DataFrame({
            'Style': ['STYLE001', 'STYLE002'],
            'yds': ['1,500', '2,000'],
            'lbs': ['500', '750']
        })
        inventory_data.to_csv(self.data_dir / 'Inventory.csv', index=False)
        
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir)
        
    def test_load_sales_data(self):
        """Test loading and validation of sales data"""
        processor = SalesDataProcessor(str(self.data_dir))
        sales_df = processor.load_and_validate_sales_data()
        
        self.assertEqual(len(sales_df), 50)
        self.assertIn('Invoice Date', sales_df.columns)
        self.assertEqual(sales_df['Invoice Date'].dtype, 'datetime64[ns]')
        self.assertTrue(all(sales_df['Yds_ordered'] > 0))
        
    def test_load_inventory_data(self):
        """Test loading inventory data"""
        processor = SalesDataProcessor(str(self.data_dir))
        inventory_df = processor.load_inventory_data()
        
        self.assertEqual(len(inventory_df), 2)
        self.assertEqual(inventory_df['yds'].iloc[0], 1500)  # Should be numeric
        
    def test_merge_sales_inventory(self):
        """Test merging sales with inventory"""
        processor = SalesDataProcessor(str(self.data_dir))
        processor.load_and_validate_sales_data()
        processor.load_inventory_data()
        
        merged_df = processor.merge_sales_with_inventory()
        
        self.assertIn('Current_Inventory', merged_df.columns)
        self.assertIn('Days_of_Inventory', merged_df.columns)
        self.assertIn('Low_Inventory_Flag', merged_df.columns)
        
    def test_generate_planning_inputs(self):
        """Test planning input generation"""
        processor = SalesDataProcessor(str(self.data_dir))
        planning_inputs = processor.generate_planning_inputs()
        
        self.assertIn('forecasts', planning_inputs)
        self.assertIn('forecast_summary', planning_inputs)
        self.assertIn('inventory_analysis', planning_inputs)
        self.assertGreater(len(planning_inputs['forecasts']), 0)


class TestSalesPlanningIntegration(unittest.TestCase):
    """Test the complete integration"""
    
    def setUp(self):
        """Set up test configuration"""
        self.config = {
            'enable_sales_forecasts': True,
            'planning_horizon_days': 30,
            'lookback_days': 60,
            'min_sales_history_days': 14,
            'seasonality_enabled': False,
            'forecast_source_weights': {
                'sales_history': 0.7,
                'manual_forecast': 0.2,
                'customer_orders': 1.0
            }
        }
        
    def test_combine_forecasts(self):
        """Test forecast combination logic"""
        integration = SalesPlanningIntegration(self.config)
        
        # Create sample forecasts
        sales_forecasts = [
            FinishedGoodsForecast(sku_id='SKU001', forecast_qty=100, forecast_date=datetime.now(), source='sales_history', unit='yards', confidence=0.8),
            FinishedGoodsForecast(sku_id='SKU002', forecast_qty=200, forecast_date=datetime.now(), source='sales_history', unit='yards', confidence=0.7)
        ]
        
        manual_forecasts = [
            FinishedGoodsForecast(sku_id='SKU001', forecast_qty=150, forecast_date=datetime.now(), source='manual', unit='yards', confidence=0.9),
            FinishedGoodsForecast(sku_id='SKU003', forecast_qty=300, forecast_date=datetime.now(), source='manual', unit='yards', confidence=0.85)
        ]
        
        customer_orders = [
            FinishedGoodsForecast(sku_id='SKU001', forecast_qty=50, forecast_date=datetime.now(), source='order', unit='yards', confidence=1.0)
        ]
        
        combined = integration.combine_forecasts(sales_forecasts, manual_forecasts, customer_orders)
        
        # Check results
        self.assertEqual(len(combined), 3)  # SKU001, SKU002, SKU003
        
        # Find SKU001 (should have all three sources)
        sku001 = next(f for f in combined if f.sku_id == 'SKU001')
        # Expected: (100 * 0.7) + (150 * 0.2) + (50 * 1.0) = 70 + 30 + 50 = 150
        self.assertAlmostEqual(sku001.forecast_qty, 150, delta=1)
        
    def test_validation(self):
        """Test integration validation"""
        integration = SalesPlanningIntegration(self.config)
        validation_results = integration.validate_integration()
        
        self.assertIn('errors', validation_results)
        self.assertIn('warnings', validation_results)
        self.assertIn('info', validation_results)


if __name__ == '__main__':
    unittest.main()