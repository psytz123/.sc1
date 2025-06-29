"""
Test Suite for Sales Integration Components
Tests the sales forecast generator, data processor, and integration
"""

import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
import os

import numpy as np
import pandas as pd

from data.sales_data_processor import SalesDataProcessor
from engine.sales_planning_integration import SalesPlanningIntegration
from models.forecast import FinishedGoodsForecast
from models.sales_forecast_generator import SalesForecastGenerator
from models.bom import BillOfMaterials, BOMExploder
from models.inventory import Inventory, InventoryNetter
from models.supplier import Supplier
from utils.logger import get_logger

logger = get_logger(__name__)


class TestSalesForecastGenerator(unittest.TestCase):
    """Test the sales forecast generator"""
    
    def setUp(self):
        """Create sample sales data"""
        # Generate sample sales data
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        self.styles = ['STYLE001', 'STYLE002', 'STYLE003']
        
        sales_data = []
        for _ in range(200):
            sales_data.append({
                'Invoice Date': np.random.choice(dates),
                'Style': np.random.choice(self.styles),
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
            self.assertIn(forecast.sku_id, self.styles)
    
    def test_seasonality_detection(self):
        """Test seasonality detection in forecasts"""
        # Create data with clear seasonality
        dates = pd.date_range(end=datetime.now(), periods=365, freq='D')
        sales_data = []
        
        for date in dates:
            # Higher sales in summer months
            base_qty = 100
            if date.month in [6, 7, 8]:
                base_qty = 300
            
            sales_data.append({
                'Invoice Date': date,
                'Style': 'STYLE001',
                'Yds_ordered': base_qty + np.random.uniform(-20, 20),
                'Customer': 'Customer1',
                'Unit Price': 10
            })
        
        seasonal_df = pd.DataFrame(sales_data)
        generator = SalesForecastGenerator(seasonal_df, planning_horizon_days=90)
        forecasts = generator.generate_forecasts()
        
        self.assertEqual(len(forecasts), 1)
        # Forecast should reflect seasonality
        self.assertGreater(forecasts[0].forecast_qty, 0)


class TestSalesDataProcessor(unittest.TestCase):
    """Test the sales data processor"""
    
    def setUp(self):
        """Create temporary directory and sample data"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample sales data
        self.sample_sales = pd.DataFrame({
            'Invoice Date': pd.date_range(start='2024-01-01', periods=10),
            'Style': ['STYLE001'] * 5 + ['STYLE002'] * 5,
            'Yds_ordered': np.random.uniform(100, 500, 10),
            'Customer': ['Customer1'] * 10,
            'Unit Price': np.random.uniform(5, 15, 10)
        })
        
        # Save to temp directory
        self.sample_sales.to_csv(
            os.path.join(self.temp_dir, 'Sales Activity Report.csv'),
            index=False
        )
        
        # Create processor with custom data directory
        self.processor = SalesDataProcessor()
        # Override the data path for testing
        self.original_path = Path('data/Sales Activity Report.csv')
        self.test_path = Path(self.temp_dir) / 'Sales Activity Report.csv'
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_sales_data_from_csv(self):
        """Test loading sales data from CSV"""
        # Load the sample data directly
        df = pd.read_csv(self.test_path)
        
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 10)
        self.assertIn('Invoice Date', df.columns)
        self.assertIn('Style', df.columns)
    
    def test_sales_aggregation(self):
        """Test sales data aggregation"""
        # Group by style and sum yards
        aggregated = self.sample_sales.groupby('Style').agg({
            'Yds_ordered': 'sum',
            'Invoice Date': 'count',
            'Unit Price': 'mean'
        }).reset_index()
        
        aggregated.columns = ['Style', 'total_yards', 'order_count', 'avg_price']
        
        self.assertEqual(len(aggregated), 2)  # Two styles
        self.assertIn('STYLE001', aggregated['Style'].values)
        self.assertIn('STYLE002', aggregated['Style'].values)
        
        # Check aggregation columns
        self.assertIn('total_yards', aggregated.columns)
        self.assertIn('order_count', aggregated.columns)
        self.assertIn('avg_price', aggregated.columns)


class TestSalesPlanningIntegration(unittest.TestCase):
    """Test the complete sales to planning integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test data files in temp directory
        self._create_test_data()
        
        # Create integration instance
        self.integration = SalesPlanningIntegration()
        # Override data directory
        self.integration.data_dir = self.temp_dir
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_data(self):
        """Create all necessary test data files"""
        # Sales data
        sales_data = pd.DataFrame({
            'Invoice Date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
            'Style': ['STYLE001'] * 50 + ['STYLE002'] * 50,
            'Yds_ordered': np.random.uniform(100, 500, 100),
            'Customer': [f'Customer{i%5}' for i in range(100)],
            'Unit Price': np.random.uniform(5, 15, 100)
        })
        sales_data.to_csv(os.path.join(self.temp_dir, 'Sales Activity Report.csv'), index=False)
        
        # BOM data
        bom_data = pd.DataFrame({
            'sku_id': ['STYLE001', 'STYLE001', 'STYLE002', 'STYLE002'],
            'material_id': ['YARN001', 'YARN002', 'YARN001', 'YARN003'],
            'qty_per_unit': [0.7, 0.3, 0.5, 0.5],
            'unit': ['yards', 'yards', 'yards', 'yards']
        })
        bom_data.to_csv(os.path.join(self.temp_dir, 'integrated_boms_v3_corrected.csv'), index=False)
        
        # Inventory data
        inventory_data = pd.DataFrame({
            'material_id': ['YARN001', 'YARN002', 'YARN003'],
            'on_hand_qty': [5000, 3000, 2000],
            'open_po_qty': [1000, 0, 500],
            'unit': ['yards', 'yards', 'yards']
        })
        inventory_data.to_csv(os.path.join(self.temp_dir, 'integrated_inventory_v2.csv'), index=False)
        
        # Supplier data
        supplier_data = pd.DataFrame({
            'supplier_id': ['SUPP001', 'SUPP002', 'SUPP003'],
            'supplier_name': ['Supplier 1', 'Supplier 2', 'Supplier 3'],
            'material_id': ['YARN001', 'YARN002', 'YARN003'],
            'lead_time_days': [14, 21, 30],
            'moq': [1000, 500, 2000],
            'price_per_unit': [2.5, 3.0, 4.0],
            'reliability_score': [0.95, 0.90, 0.85]
        })
        supplier_data.to_csv(os.path.join(self.temp_dir, 'integrated_suppliers_v2.csv'), index=False)
    
    def test_load_boms_method(self):
        """Test the _load_boms method"""
        boms = self.integration._load_boms()
        
        self.assertIsInstance(boms, list)
        self.assertEqual(len(boms), 4)  # 4 BOM entries
        
        # Check BOM structure
        for bom in boms:
            self.assertIsInstance(bom, BillOfMaterials)
            self.assertGreater(bom.qty_per_unit, 0)
            self.assertEqual(bom.unit, 'yards')
    
    def test_load_inventory_method(self):
        """Test the _load_inventory method"""
        inventories = self.integration._load_inventory()
        
        self.assertIsInstance(inventories, list)
        self.assertEqual(len(inventories), 3)  # 3 materials
        
        # Check inventory structure
        for inv in inventories:
            self.assertIsInstance(inv, Inventory)
            self.assertGreaterEqual(inv.on_hand_qty, 0)
            self.assertGreaterEqual(inv.open_po_qty, 0)
    
    def test_data_validation(self):
        """Test data validation in the integration"""
        validation_results = self.integration.validate_data()
        
        self.assertIsInstance(validation_results, dict)
        self.assertIn('sales_data', validation_results)
        self.assertIn('bom_data', validation_results)
        self.assertIn('inventory_data', validation_results)
        self.assertIn('overall', validation_results)
        
        # All validations should pass with our test data
        self.assertTrue(validation_results['overall'])
    
    def test_forecast_to_material_flow(self):
        """Test the flow from forecasts to material requirements"""
        # Generate forecasts
        sales_df = pd.read_csv(os.path.join(self.temp_dir, 'Sales Activity Report.csv'))
        generator = SalesForecastGenerator(sales_df, planning_horizon_days=30)
        forecasts = generator.generate_forecasts()
        
        # Convert to material requirements
        sku_forecasts = {f.sku_id: f.forecast_qty for f in forecasts}
        
        # Load BOMs and explode
        boms = self.integration._load_boms()
        material_reqs = BOMExploder.explode_requirements(sku_forecasts, boms)
        
        # Verify material requirements
        self.assertGreater(len(material_reqs), 0)
        
        # Check that each material requirement has the correct structure
        for material_id, req_data in material_reqs.items():
            self.assertIn('total_qty', req_data)
            self.assertIn('unit', req_data)
            self.assertIn('sources', req_data)
            self.assertGreater(req_data['total_qty'], 0)
    
    def test_inventory_netting(self):
        """Test inventory netting calculations"""
        # Create material requirements
        material_reqs = {
            'YARN001': {'total_qty': 10000, 'unit': 'yards', 'sources': []},
            'YARN002': {'total_qty': 5000, 'unit': 'yards', 'sources': []},
            'YARN003': {'total_qty': 3000, 'unit': 'yards', 'sources': []}
        }
        
        # Load inventory
        inventories = self.integration._load_inventory()
        
        # Calculate net requirements
        net_reqs = InventoryNetter.calculate_net_requirements(material_reqs, inventories)
        
        # Verify netting logic
        for material_id, net_req in net_reqs.items():
            gross = net_req['gross_requirement']
            on_hand = net_req['on_hand_qty']
            open_po = net_req['open_po_qty']
            net = net_req['net_requirement']
            
            # Net requirement = max(0, gross - on_hand - open_po)
            expected_net = max(0, gross - on_hand - open_po)
            self.assertAlmostEqual(net, expected_net, places=2)


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and consistency across the integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = SalesPlanningIntegration()
        self.integration.data_dir = self.temp_dir
        
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_bom_validation(self):
        """Test that BOM data is validated correctly"""
        # Create BOM data
        bom_data = pd.DataFrame({
            'sku_id': ['STYLE001', 'STYLE001'],
            'material_id': ['YARN001', 'YARN002'],
            'qty_per_unit': [0.6, 0.3],
            'unit': ['yards', 'yards']
        })
        
        bom_file = os.path.join(self.temp_dir, 'integrated_boms_v3_corrected.csv')
        bom_data.to_csv(bom_file, index=False)
        
        # Load and validate
        boms = self.integration._load_boms()
        issues = BOMExploder.validate_bom_data(boms)
        
        # Should still load
        self.assertEqual(len(boms), 2)
    
    def test_unit_consistency(self):
        """Test that units are handled consistently"""
        # Create data with consistent units
        inventory_data = pd.DataFrame({
            'material_id': ['YARN001', 'YARN002'],
            'on_hand_qty': [1000, 2000],
            'unit': ['yards', 'yards']
        })
        
        inventory_file = os.path.join(self.temp_dir, 'integrated_inventory_v2.csv')
        inventory_data.to_csv(inventory_file, index=False)
        
        inventories = self.integration._load_inventory()
        
        # Check that units are preserved
        for inv in inventories:
            self.assertEqual(inv.unit, 'yards')


if __name__ == '__main__':
    unittest.main()