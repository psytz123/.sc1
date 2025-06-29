"""
Integration tests for sales planning workflow
"""

import os
import tempfile
import shutil
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from engine.sales_planning_integration import SalesPlanningIntegration
from models.bom import BillOfMaterials, BOMExploder
from models.inventory import Inventory, InventoryNetter
from models.sales_forecast_generator import SalesForecastGenerator
from models.forecast import FinishedGoodsForecast


class TestSalesIntegrationEndToEnd(unittest.TestCase):
    """End-to-end integration tests for sales planning workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = SalesPlanningIntegration()
        self.integration.data_dir = self.temp_dir
        self._create_test_data()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_data(self):
        """Create test data files"""
        # Sales data
        sales_data = pd.DataFrame({
            'Invoice Date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
            'Style': ['STYLE001'] * 50 + ['STYLE002'] * 50,
            'Yds_ordered': np.random.uniform(100, 500, 100),
            'Customer': ['Customer1'] * 100,
            'Unit Price': [10.0] * 100
        })
        sales_data.to_csv(os.path.join(self.temp_dir, 'Sales Activity Report.csv'), index=False)
        
        # BOM data
        bom_data = pd.DataFrame({
            'sku_id': ['STYLE001', 'STYLE001', 'STYLE002'],
            'material_id': ['YARN001', 'YARN002', 'YARN001'],
            'qty_per_unit': [0.7, 0.3, 1.0],
            'unit': ['yards', 'yards', 'yards']
        })
        bom_data.to_csv(os.path.join(self.temp_dir, 'integrated_boms_v3_corrected.csv'), index=False)
        
        # Inventory data
        inventory_data = pd.DataFrame({
            'material_id': ['YARN001', 'YARN002'],
            'on_hand_qty': [5000.0, 3000.0],
            'open_po_qty': [1000.0, 0.0],
            'unit': ['yards', 'yards']
        })
        inventory_data.to_csv(os.path.join(self.temp_dir, 'integrated_inventory_v2.csv'), index=False)
    
    def test_load_boms(self):
        """Test loading BOMs"""
        boms = self.integration._load_boms()
        self.assertEqual(len(boms), 3)
        for bom in boms:
            self.assertIsInstance(bom, BillOfMaterials)
            self.assertGreater(bom.qty_per_unit, 0)
    
    def test_load_inventory(self):
        """Test loading inventory"""
        inventories = self.integration._load_inventory()
        self.assertEqual(len(inventories), 2)
        for inv in inventories:
            self.assertIsInstance(inv, Inventory)
            self.assertGreaterEqual(inv.on_hand_qty, 0)

    def test_sales_forecast_generation(self):
        """Test generating forecasts from sales data"""
        sales_df = pd.read_csv(os.path.join(self.temp_dir, 'Sales Activity Report.csv'))
        # Convert Invoice Date to datetime
        sales_df['Invoice Date'] = pd.to_datetime(sales_df['Invoice Date'])

        # Create a custom generator that works with our test data dates
        # We'll need to modify the sales data to be more recent or create a custom test
        # For now, let's update the dates to be more recent
        latest_date = sales_df['Invoice Date'].max()
        days_diff = (datetime.now() - latest_date).days
        sales_df['Invoice Date'] = sales_df['Invoice Date'] + timedelta(days=days_diff - 10)  # Make it 10 days ago

        generator = SalesForecastGenerator(
            sales_df,
            planning_horizon_days=30,
            min_history_days=1,
            lookback_days=100
        )
        forecasts = generator.generate_forecasts()

        self.assertGreater(len(forecasts), 0)
        for forecast in forecasts:
            self.assertIsInstance(forecast, FinishedGoodsForecast)
            self.assertGreater(forecast.forecast_qty, 0)
    
    def test_bom_explosion(self):
        """Test BOM explosion from forecasts to materials"""
        # Create sample forecasts
        sku_forecasts = {
            'STYLE001': 1000.0,
            'STYLE002': 500.0
        }
        
        boms = self.integration._load_boms()
        material_reqs = BOMExploder.explode_requirements(sku_forecasts, boms)
        
        # Check YARN001 requirement (0.7 * 1000 + 1.0 * 500 = 1200)
        self.assertIn('YARN001', material_reqs)
        self.assertAlmostEqual(material_reqs['YARN001']['total_qty'], 1200.0, places=1)
        
        # Check YARN002 requirement (0.3 * 1000 = 300)
        self.assertIn('YARN002', material_reqs)
        self.assertAlmostEqual(material_reqs['YARN002']['total_qty'], 300.0, places=1)
    
    def test_inventory_netting(self):
        """Test inventory netting calculations"""
        material_reqs = {
            'YARN001': {'total_qty': 10000.0, 'unit': 'yards', 'sources': []},
            'YARN002': {'total_qty': 2000.0, 'unit': 'yards', 'sources': []}
        }
        
        inventories = self.integration._load_inventory()
        net_reqs = InventoryNetter.calculate_net_requirements(material_reqs, inventories)
        
        # YARN001: 10000 - 5000 - 1000 = 4000
        self.assertAlmostEqual(net_reqs['YARN001']['net_requirement'], 4000.0, places=1)
        
        # YARN002: 2000 - 3000 - 0 = 0 (no shortage)
        self.assertAlmostEqual(net_reqs['YARN002']['net_requirement'], 0.0, places=1)

    def test_data_validation(self):
        """Test data validation"""
        validation_results = self.integration.validate_integration()

        self.assertIn('sales_data_load', validation_results)
        self.assertIn('bom_data_load', validation_results)
        self.assertIn('forecast_generation', validation_results)
        self.assertIn('overall', validation_results)

        # Sales and BOM data should load successfully
        self.assertTrue(validation_results['sales_data_load'])
        self.assertTrue(validation_results['bom_data_load'])
    
    def test_error_handling_missing_file(self):
        """Test error handling when files are missing"""
        # Remove BOM file
        os.remove(os.path.join(self.temp_dir, 'integrated_boms_v3_corrected.csv'))
        
        # Should return empty list and log warning
        boms = self.integration._load_boms()
        self.assertEqual(len(boms), 0)
    
    def test_error_handling_invalid_data(self):
        """Test error handling with invalid data"""
        # Create invalid inventory data (negative stock)
        invalid_inventory = pd.DataFrame({
            'material_id': ['YARN001'],
            'on_hand_qty': [-100.0],  # Invalid negative value
            'unit': ['yards']
        })
        invalid_inventory.to_csv(os.path.join(self.temp_dir, 'integrated_inventory_v2.csv'), index=False)
        
        # Should raise error
        with self.assertRaises(ValueError):
            self.integration._load_inventory()


if __name__ == '__main__':
    unittest.main()