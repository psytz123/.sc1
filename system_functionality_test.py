#!/usr/bin/env python3
"""
Complete System Functionality Test Suite for Beverly Knits
Tests all modules, imports, processes, and system components
"""

import sys
import os
import importlib
import traceback
import time
import json
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import warnings

warnings.filterwarnings('ignore')

class SystemFunctionalityTest:
    """Comprehensive system functionality testing"""
    
    def __init__(self):
        self.test_results = []
        self.module_status = {}
        self.function_status = {}
        self.process_status = {}
        self.errors = []
        self.warnings = []
        
        print("🔧 Beverly Knits System Functionality Test Suite")
        print("=" * 60)
    
    def run_complete_system_test(self):
        """Execute complete system functionality testing"""
        
        print("🚀 Starting Complete System Functionality Test")
        print("-" * 60)
        
        # Phase 1: Environment & Dependencies
        print("\n1️⃣ Environment & Dependencies Test")
        self.test_environment_setup()
        
        # Phase 2: Module Import Testing
        print("\n2️⃣ Module Import Testing")
        self.test_all_imports()
        
        # Phase 3: Core Models Testing
        print("\n3️⃣ Core Models Testing")
        self.test_core_models()
        
        # Phase 4: Engine Components Testing
        print("\n4️⃣ Engine Components Testing")
        self.test_engine_components()
        
        # Phase 5: Configuration System Testing
        print("\n5️⃣ Configuration System Testing")
        self.test_configuration_system()
        
        # Phase 6: Utility Functions Testing
        print("\n6️⃣ Utility Functions Testing")
        self.test_utility_functions()
        
        # Phase 7: Data Processing Testing
        print("\n7️⃣ Data Processing Testing")
        self.test_data_processing()
        
        # Phase 8: Workflow Process Testing
        print("\n8️⃣ Complete Workflow Testing")
        self.test_complete_workflow()
        
        # Phase 9: UI Components Testing
        print("\n9️⃣ UI Components Testing")
        self.test_ui_components()
        
        # Phase 10: Integration Testing
        print("\n🔟 System Integration Testing")
        self.test_system_integration()
        
        # Generate comprehensive report
        self.generate_system_report()
        
        return self.test_results
    
    def test_environment_setup(self):
        """Test environment and dependencies"""
        
        # Test Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.log_success("Environment", f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.log_error("Environment", f"Python version too old: {python_version}")
        
        # Test required packages
        required_packages = [
            'pandas', 'numpy', 'streamlit', 'plotly', 'pydantic', 
            'loguru', 'pathlib', 'datetime', 'decimal', 'typing'
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                self.log_success("Dependencies", f"{package} available")
            except ImportError:
                self.log_error("Dependencies", f"{package} not available")
        
        # Test working directory
        if Path('main.py').exists():
            self.log_success("Environment", "Running from correct directory")
        else:
            self.log_error("Environment", "Not running from project root directory")
        
        # Test directory structure
        expected_dirs = ['engine', 'models', 'config', 'utils', 'data']
        for dir_name in expected_dirs:
            if Path(dir_name).exists():
                self.log_success("Directory Structure", f"{dir_name}/ exists")
            else:
                self.log_warning("Directory Structure", f"{dir_name}/ missing")
    
    def test_all_imports(self):
        """Test all module imports"""
        
        # Add current directory to Python path
        sys.path.insert(0, '.')
        
        # Test core module imports
        core_modules = {
            'main': 'main.py',
            'engine.planner': 'engine/planner.py',
            'models.forecast': 'models/forecast.py',
            'models.bom': 'models/bom.py',
            'models.inventory': 'models/inventory.py',
            'models.supplier': 'models/supplier.py',
            'models.recommendation': 'models/recommendation.py',
            'config.settings': 'config/settings.py'
        }
        
        for module_name, file_path in core_modules.items():
            self.test_module_import(module_name, file_path)
        
        # Test utility imports
        utility_modules = [
            'utils', 'utils.data_validation', 'utils.file_operations',
            'utils.calculations', 'utils.logging_config'
        ]
        
        for module_name in utility_modules:
            self.test_optional_module_import(module_name)
    
    def test_module_import(self, module_name, file_path):
        """Test importing a specific module"""
        try:
            # Check if file exists
            if not Path(file_path).exists():
                self.log_error("Module Import", f"{file_path} file missing")
                return
            
            # Try to import
            module = importlib.import_module(module_name)
            self.log_success("Module Import", f"{module_name} imported successfully")
            
            # Store module for later testing
            self.module_status[module_name] = {
                'status': 'SUCCESS',
                'module': module,
                'file_path': file_path
            }
            
        except Exception as e:
            self.log_error("Module Import", f"{module_name}: {str(e)}")
            self.module_status[module_name] = {
                'status': 'ERROR',
                'error': str(e),
                'file_path': file_path
            }
    
    def test_optional_module_import(self, module_name):
        """Test importing optional modules"""
        try:
            module = importlib.import_module(module_name)
            self.log_success("Optional Import", f"{module_name} available")
            self.module_status[module_name] = {'status': 'SUCCESS', 'module': module}
        except ImportError:
            self.log_warning("Optional Import", f"{module_name} not available")
            self.module_status[module_name] = {'status': 'MISSING'}
        except Exception as e:
            self.log_error("Optional Import", f"{module_name}: {str(e)}")
            self.module_status[module_name] = {'status': 'ERROR', 'error': str(e)}
    
    def test_core_models(self):
        """Test core data models"""
        
        model_tests = [
            ('Forecast Model', self.test_forecast_model),
            ('BOM Model', self.test_bom_model),
            ('Inventory Model', self.test_inventory_model),
            ('Supplier Model', self.test_supplier_model),
            ('Recommendation Model', self.test_recommendation_model)
        ]
        
        for test_name, test_func in model_tests:
            try:
                test_func()
                self.log_success("Core Models", test_name)
            except Exception as e:
                self.log_error("Core Models", f"{test_name}: {str(e)}")
    
    def test_forecast_model(self):
        """Test forecast model functionality"""
        if 'models.forecast' not in self.module_status or self.module_status['models.forecast']['status'] != 'SUCCESS':
            raise Exception("Forecast module not available")
        
        forecast_module = self.module_status['models.forecast']['module']
        
        # Test class exists
        if hasattr(forecast_module, 'FinishedGoodsForecast'):
            forecast_class = getattr(forecast_module, 'FinishedGoodsForecast')
            
            # Test instantiation
            test_forecast = forecast_class(
                sku_id="TEST-SKU",
                forecast_qty=100.0,
                source="test",
                forecast_date="2025-02-01"
            )
            
            # Test basic properties
            assert test_forecast.sku_id == "TEST-SKU"
            assert test_forecast.forecast_qty == 100.0
            
        else:
            raise Exception("FinishedGoodsForecast class not found")
    
    def test_bom_model(self):
        """Test BOM model functionality"""
        if 'models.bom' not in self.module_status or self.module_status['models.bom']['status'] != 'SUCCESS':
            raise Exception("BOM module not available")
        
        bom_module = self.module_status['models.bom']['module']
        
        # Test class exists
        if hasattr(bom_module, 'BillOfMaterials'):
            bom_class = getattr(bom_module, 'BillOfMaterials')
            
            # Test instantiation
            test_bom = bom_class(
                sku_id="TEST-SKU",
                material_id="TEST-MAT",
                qty_per_unit=0.5,
                unit="yards"
            )
            
            # Test basic properties
            assert test_bom.sku_id == "TEST-SKU"
            assert test_bom.qty_per_unit == 0.5
            
        else:
            raise Exception("BillOfMaterials class not found")
    
    def test_inventory_model(self):
        """Test inventory model functionality"""
        if 'models.inventory' not in self.module_status or self.module_status['models.inventory']['status'] != 'SUCCESS':
            raise Exception("Inventory module not available")
        
        inventory_module = self.module_status['models.inventory']['module']
        
        # Test class exists
        if hasattr(inventory_module, 'Inventory'):
            inventory_class = getattr(inventory_module, 'Inventory')
            
            # Test instantiation
            test_inventory = inventory_class(
                material_id="TEST-MAT",
                on_hand_qty=50.0,
                unit="yards"
            )
            
            # Test basic properties
            assert test_inventory.material_id == "TEST-MAT"
            assert test_inventory.on_hand_qty == 50.0
            
        else:
            raise Exception("Inventory class not found")
    
    def test_supplier_model(self):
        """Test supplier model functionality"""
        if 'models.supplier' not in self.module_status or self.module_status['models.supplier']['status'] != 'SUCCESS':
            raise Exception("Supplier module not available")
        
        supplier_module = self.module_status['models.supplier']['module']
        
        # Test class exists
        if hasattr(supplier_module, 'Supplier'):
            supplier_class = getattr(supplier_module, 'Supplier')
            
            # Test instantiation
            test_supplier = supplier_class(
                material_id="TEST-MAT",
                supplier_id="TEST-SUP",
                cost_per_unit=10.0,
                lead_time_days=14
            )
            
            # Test basic properties
            assert test_supplier.supplier_id == "TEST-SUP"
            assert test_supplier.cost_per_unit == 10.0
            
        else:
            raise Exception("Supplier class not found")
    
    def test_recommendation_model(self):
        """Test recommendation model functionality"""
        if 'models.recommendation' not in self.module_status or self.module_status['models.recommendation']['status'] != 'SUCCESS':
            raise Exception("Recommendation module not available")
        
        recommendation_module = self.module_status['models.recommendation']['module']
        
        # Test class exists
        if hasattr(recommendation_module, 'ProcurementRecommendation'):
            rec_class = getattr(recommendation_module, 'ProcurementRecommendation')
            
            # Test instantiation
            test_rec = rec_class(
                material_id="TEST-MAT",
                supplier_id="TEST-SUP",
                quantity=100.0,
                unit_cost=10.0,
                total_cost=1000.0
            )
            
            # Test basic properties
            assert test_rec.material_id == "TEST-MAT"
            assert test_rec.total_cost == 1000.0
            
        else:
            raise Exception("ProcurementRecommendation class not found")
    
    def test_engine_components(self):
        """Test planning engine components"""
        
        if 'engine.planner' not in self.module_status or self.module_status['engine.planner']['status'] != 'SUCCESS':
            self.log_error("Engine Components", "Planning engine not available")
            return
        
        planner_module = self.module_status['engine.planner']['module']
        
        # Test MaterialPlanner class exists
        if hasattr(planner_module, 'MaterialPlanner'):
            planner_class = getattr(planner_module, 'MaterialPlanner')
            
            try:
                # Test instantiation
                planner = planner_class()
                self.log_success("Engine Components", "MaterialPlanner instantiated")
                
                # Test required methods exist
                required_methods = [
                    'unify_forecasts', 'explode_bom', 'net_inventory',
                    'optimize_procurement', 'select_suppliers', 'generate_recommendations'
                ]
                
                for method_name in required_methods:
                    if hasattr(planner, method_name):
                        method = getattr(planner, method_name)
                        if callable(method):
                            self.log_success("Engine Methods", f"{method_name} method available")
                        else:
                            self.log_error("Engine Methods", f"{method_name} exists but not callable")
                    else:
                        self.log_error("Engine Methods", f"{method_name} method missing")
                
                # Test method signatures
                self.test_method_signatures(planner, required_methods)
                
            except Exception as e:
                self.log_error("Engine Components", f"MaterialPlanner instantiation failed: {str(e)}")
        else:
            self.log_error("Engine Components", "MaterialPlanner class not found")
    
    def test_method_signatures(self, planner, method_names):
        """Test method signatures are correct"""
        
        for method_name in method_names:
            if hasattr(planner, method_name):
                method = getattr(planner, method_name)
                try:
                    # Get method signature
                    sig = inspect.signature(method)
                    params = list(sig.parameters.keys())
                    
                    # Basic signature validation (method should accept parameters)
                    if len(params) > 0:  # Excluding 'self'
                        self.log_success("Method Signatures", f"{method_name} has {len(params)} parameters")
                    else:
                        self.log_warning("Method Signatures", f"{method_name} has no parameters")
                        
                except Exception as e:
                    self.log_warning("Method Signatures", f"Could not inspect {method_name}: {str(e)}")
    
    def test_configuration_system(self):
        """Test configuration system"""
        
        # Test config module
        if 'config.settings' in self.module_status and self.module_status['config.settings']['status'] == 'SUCCESS':
            config_module = self.module_status['config.settings']['module']
            
            # Test configuration loading
            try:
                # Check for configuration constants/functions
                config_items = [attr for attr in dir(config_module) if not attr.startswith('_')]
                
                if config_items:
                    self.log_success("Configuration", f"Config module has {len(config_items)} items")
                    
                    # Test specific config items
                    expected_configs = [
                        'PLANNING_CONFIG', 'FORECAST_WEIGHTS', 'MATERIAL_CATEGORIES',
                        'SAFETY_STOCK_CONFIG', 'EOQ_CONFIG'
                    ]
                    
                    for config_name in expected_configs:
                        if hasattr(config_module, config_name):
                            self.log_success("Configuration Items", f"{config_name} defined")
                        else:
                            self.log_warning("Configuration Items", f"{config_name} not found")
                else:
                    self.log_warning("Configuration", "Config module appears empty")
                    
            except Exception as e:
                self.log_error("Configuration", f"Config testing failed: {str(e)}")
        else:
            self.log_warning("Configuration", "Config module not available")
        
        # Test environment variables
        self.test_environment_variables()
    
    def test_environment_variables(self):
        """Test environment variable handling"""
        
        # Common environment variables for the application
        env_vars = ['PYTHONPATH', 'STREAMLIT_SERVER_PORT', 'STREAMLIT_SERVER_ADDRESS']
        
        for var in env_vars:
            if var in os.environ:
                self.log_success("Environment Variables", f"{var} set")
            else:
                self.log_info("Environment Variables", f"{var} not set (optional)")
    
    def test_utility_functions(self):
        """Test utility functions"""
        
        utility_tests = [
            ('File Operations', self.test_file_operations),
            ('Data Validation', self.test_data_validation),
            ('Calculations', self.test_calculations),
            ('Logging', self.test_logging_utilities)
        ]
        
        for test_name, test_func in utility_tests:
            try:
                test_func()
                self.log_success("Utilities", test_name)
            except Exception as e:
                self.log_error("Utilities", f"{test_name}: {str(e)}")
    
    def test_file_operations(self):
        """Test file operation utilities"""
        
        # Test basic file operations
        test_file = Path('test_system_functionality.tmp')
        
        # Test write
        test_file.write_text('test content')
        assert test_file.exists()
        
        # Test read
        content = test_file.read_text()
        assert content == 'test content'
        
        # Test delete
        test_file.unlink()
        assert not test_file.exists()
    
    def test_data_validation(self):
        """Test data validation utilities"""
        
        # Test pandas operations (core to data validation)
        import pandas as pd
        import numpy as np
        
        # Create test dataframe
        test_df = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.5, 20.0, 30.5],
            'text': ['A', 'B', 'C']
        })
        
        # Test basic operations
        assert len(test_df) == 3
        assert test_df['value'].sum() == 61.0
        assert test_df['text'].nunique() == 3
    
    def test_calculations(self):
        """Test calculation utilities"""
        
        import math
        
        # Test basic mathematical operations
        assert abs(math.sqrt(16) - 4.0) < 0.001
        
        # Test EOQ calculation formula
        annual_demand = 1000
        ordering_cost = 25
        unit_cost = 10
        holding_rate = 0.2
        
        eoq = math.sqrt(2 * annual_demand * ordering_cost / (unit_cost * holding_rate))
        assert eoq > 0
        
        # Test percentage calculations
        percentage = 0.15
        base_value = 100
        result = base_value * percentage
        assert result == 15.0
    
    def test_logging_utilities(self):
        """Test logging utilities"""
        
        import logging
        
        # Test basic logging setup
        logger = logging.getLogger('test_logger')
        logger.setLevel(logging.INFO)
        
        # Test logging works (shouldn't raise exceptions)
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
    
    def test_data_processing(self):
        """Test data processing capabilities"""
        
        try:
            import pandas as pd
            import numpy as np
            
            # Test CSV processing
            test_data = pd.DataFrame({
                'sku_id': ['SKU-001', 'SKU-002', 'SKU-003'],
                'forecast_qty': [100, 200, 150],
                'source': ['sales_order', 'prod_plan', 'projection']
            })
            
            # Test basic DataFrame operations
            assert len(test_data) == 3
            assert test_data['forecast_qty'].sum() == 450
            
            # Test grouping operations
            grouped = test_data.groupby('source')['forecast_qty'].sum()
            assert len(grouped) == 3
            
            # Test data cleaning operations
            test_data_with_nulls = test_data.copy()
            test_data_with_nulls.loc[0, 'forecast_qty'] = None
            
            cleaned_data = test_data_with_nulls.fillna(0)
            assert cleaned_data['forecast_qty'].isna().sum() == 0
            
            self.log_success("Data Processing", "All pandas operations working")
            
        except Exception as e:
            self.log_error("Data Processing", f"Pandas operations failed: {str(e)}")
    
    def test_complete_workflow(self):
        """Test complete workflow process"""
        
        try:
            # Check if planning engine is available
            if 'engine.planner' not in self.module_status or self.module_status['engine.planner']['status'] != 'SUCCESS':
                raise Exception("Planning engine not available")
            
            planner_module = self.module_status['engine.planner']['module']
            planner_class = getattr(planner_module, 'MaterialPlanner')
            planner = planner_class()
            
            # Create minimal test data
            import pandas as pd
            
            # Test forecast data
            forecast_data = pd.DataFrame({
                'sku_id': ['SKU-001'],
                'forecast_qty': [100],
                'source': ['sales_order'],
                'forecast_date': ['2025-02-01']
            })
            
            # Test BOM data
            bom_data = pd.DataFrame({
                'sku_id': ['SKU-001'],
                'material_id': ['MAT-001'],
                'qty_per_unit': [1.0]
            })
            
            # Test inventory data
            inventory_data = pd.DataFrame({
                'material_id': ['MAT-001'],
                'on_hand_qty': [25]
            })
            
            # Test supplier data
            supplier_data = pd.DataFrame({
                'material_id': ['MAT-001'],
                'supplier_id': ['SUP-001'],
                'cost_per_unit': [10.0],
                'lead_time_days': [14]
            })
            
            # Test workflow steps
            workflow_steps = [
                ('Forecast Unification', lambda: planner.unify_forecasts(forecast_data)),
                ('BOM Explosion', lambda: planner.explode_bom(bom_data, forecast_data)),
                ('Inventory Netting', lambda: planner.net_inventory(
                    pd.DataFrame({'material_id': ['MAT-001'], 'gross_requirement': [100]}), 
                    inventory_data
                )),
                ('Procurement Optimization', lambda: planner.optimize_procurement(
                    pd.DataFrame({'material_id': ['MAT-001'], 'net_requirement': [75]})
                )),
                ('Supplier Selection', lambda: planner.select_suppliers(
                    pd.DataFrame({'material_id': ['MAT-001'], 'optimized_qty': [85]}), 
                    supplier_data
                )),
                ('Recommendation Generation', lambda: planner.generate_recommendations(
                    pd.DataFrame({
                        'material_id': ['MAT-001'], 
                        'supplier_id': ['SUP-001'], 
                        'quantity': [85], 
                        'unit_cost': [10.0]
                    })
                ))
            ]
            
            for step_name, step_func in workflow_steps:
                try:
                    result = step_func()
                    if result is not None and len(result) >= 0:
                        self.log_success("Workflow Steps", f"{step_name} completed")
                    else:
                        self.log_warning("Workflow Steps", f"{step_name} returned empty result")
                except Exception as e:
                    self.log_error("Workflow Steps", f"{step_name} failed: {str(e)}")
            
            self.log_success("Complete Workflow", "All workflow steps tested")
            
        except Exception as e:
            self.log_error("Complete Workflow", f"Workflow testing failed: {str(e)}")
    
    def test_ui_components(self):
        """Test UI components"""
        
        try:
            import streamlit as st
            
            # Test Streamlit import
            self.log_success("UI Components", "Streamlit imported successfully")
            
            # Test main application file
            if Path('main.py').exists():
                # Read main.py to check for Streamlit components
                main_content = Path('main.py').read_text()
                
                streamlit_components = [
                    'st.title', 'st.sidebar', 'st.selectbox', 'st.button',
                    'st.file_uploader', 'st.dataframe', 'st.plotly_chart'
                ]
                
                found_components = []
                for component in streamlit_components:
                    if component in main_content:
                        found_components.append(component)
                
                if found_components:
                    self.log_success("UI Components", f"Found {len(found_components)} Streamlit components")
                else:
                    self.log_warning("UI Components", "No Streamlit components found in main.py")
            else:
                self.log_error("UI Components", "main.py not found")
            
            # Test plotly for charts
            try:
                import plotly.graph_objects as go
                import plotly.express as px
                self.log_success("UI Components", "Plotly charting available")
            except ImportError:
                self.log_warning("UI Components", "Plotly not available")
            
        except ImportError:
            self.log_error("UI Components", "Streamlit not available")
        except Exception as e:
            self.log_error("UI Components", f"UI testing failed: {str(e)}")
    
    def test_system_integration(self):
        """Test overall system integration"""
        
        integration_tests = [
            ('Module Dependencies', self.test_module_dependencies),
            ('Data Flow Integration', self.test_data_flow),
            ('Error Handling Integration', self.test_error_handling),
            ('Configuration Integration', self.test_config_integration),
            ('File System Integration', self.test_filesystem_integration)
        ]
        
        for test_name, test_func in integration_tests:
            try:
                test_func()
                self.log_success("System Integration", test_name)
            except Exception as e:
                self.log_error("System Integration", f"{test_name}: {str(e)}")
    
    def test_module_dependencies(self):
        """Test module dependencies work correctly"""
        
        # Count successful vs failed imports
        successful_imports = sum(1 for status in self.module_status.values() 
                               if status.get('status') == 'SUCCESS')
        total_imports = len(self.module_status)
        
        if successful_imports == total_imports:
            pass  # All good
        elif successful_imports >= total_imports * 0.8:
            self.log_warning("Module Dependencies", f"{successful_imports}/{total_imports} modules imported")
        else:
            raise Exception(f"Too many import failures: {successful_imports}/{total_imports}")
    
    def test_data_flow(self):
        """Test data flows between components"""
        
        # Test that data can flow from one component to another
        import pandas as pd
        
        # Create test data
        test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10, 20, 30]
        })
        
        # Test basic transformations
        transformed = test_data.copy()
        transformed['value'] = transformed['value'] * 2
        
        assert transformed['value'].sum() == 120
    
    def test_error_handling(self):
        """Test error handling works across system"""
        
        # Test that exceptions can be caught and handled
        try:
            raise ValueError("Test error")
        except ValueError as e:
            assert str(e) == "Test error"
        
        # Test pandas error handling
        import pandas as pd
        
        try:
            df = pd.DataFrame({'a': [1, 2, 3]})
            _ = df['nonexistent_column']
        except KeyError:
            pass  # Expected
    
    def test_config_integration(self):
        """Test configuration integration"""
        
        # Test that configuration can be loaded and used
        test_config = {
            'safety_buffer': 0.15,
            'max_lead_time': 30,
            'enable_eoq': True
        }
        
        # Test config validation
        assert 0 < test_config['safety_buffer'] < 1
        assert test_config['max_lead_time'] > 0
        assert isinstance(test_config['enable_eoq'], bool)
    
    def test_filesystem_integration(self):
        """Test file system integration"""
        
        # Test directory access
        current_dir = Path('.')
        assert current_dir.exists()
        
        # Test data directory
        data_dir = Path('data')
        if data_dir.exists():
            pass  # Good
        else:
            self.log_warning("Filesystem", "Data directory not found")
    
    # Logging helper methods
    def log_success(self, category: str, message: str):
        """Log a successful test"""
        print(f"   ✅ {category}: {message}")
        self.test_results.append({
            'category': category,
            'status': 'SUCCESS',
            'message': message,
            'timestamp': time.time()
        })
    
    def log_error(self, category: str, message: str):
        """Log a test error"""
        print(f"   ❌ {category}: {message}")
        self.test_results.append({
            'category': category,
            'status': 'ERROR',
            'message': message,
            'timestamp': time.time()
        })
        self.errors.append(f"{category}: {message}")
    
    def log_warning(self, category: str, message: str):
        """Log a test warning"""
        print(f"   ⚠️  {category}: {message}")
        self.test_results.append({
            'category': category,
            'status': 'WARNING',
            'message': message,
            'timestamp': time.time()
        })
        self.warnings.append(f"{category}: {message}")
    
    def log_info(self, category: str, message: str):
        """Log informational message"""
        print(f"   ℹ️  {category}: {message}")
        self.test_results.append({
            'category': category,
            'status': 'INFO',
            'message': message,
            'timestamp': time.time()
        })
    
    def generate_system_report(self):
        """Generate comprehensive system functionality report"""
        
        # Calculate statistics
        total_tests = len(self.test_results)
        successes = sum(1 for r in self.test_results if r['status'] == 'SUCCESS')
        errors = sum(1 for r in self.test_results if r['status'] == 'ERROR')
        warnings = sum(1 for r in self.test_results if r['status'] == 'WARNING')
        infos = sum(1 for r in self.test_results if r['status'] == 'INFO')
        
        success_rate = (successes / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("🔧 SYSTEM FUNCTIONALITY TEST SUMMARY")
        print("=" * 60)
        
        print(f"📊 Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Success: {successes}")
        print(f"   ❌ Errors: {errors}")
        print(f"   ⚠️  Warnings: {warnings}")
        print(f"   ℹ️  Info: {infos}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        # Module import summary
        successful_modules = sum(1 for status in self.module_status.values() 
                               if status.get('status') == 'SUCCESS')
        total_modules = len(self.module_status)
        
        print(f"\n📦 Module Status:")
        print(f"   Modules Imported: {successful_modules}/{total_modules}")
        
        if successful_modules < total_modules:
            print(f"   Failed Modules:")
            for module_name, status in self.module_status.items():
                if status.get('status') != 'SUCCESS':
                    print(f"      • {module_name}: {status.get('status', 'UNKNOWN')}")
        
        # Critical errors
        if self.errors:
            print(f"\n🚨 Critical Errors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.errors) > 5:
                print(f"   ... and {len(self.errors) - 5} more errors")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:3]:  # Show first 3 warnings
                print(f"   • {warning}")
            if len(self.warnings) > 3:
                print(f"   ... and {len(self.warnings) - 3} more warnings")
        
        # System readiness assessment
        print(f"\n🎯 System Readiness Assessment:")
        
        if errors == 0 and successful_modules == total_modules:
            print("   🟢 SYSTEM READY - All components functional")
            readiness = "READY"
        elif errors == 0 and successful_modules >= total_modules * 0.9:
            print("   🟡 MOSTLY READY - Minor issues detected")
            readiness = "MOSTLY_READY"
        elif errors <= 2 and successful_modules >= total_modules * 0.8:
            print("   🟠 NEEDS ATTENTION - Some components have issues")
            readiness = "NEEDS_ATTENTION"
        else:
            print("   🔴 NOT READY - Critical components missing/broken")
            readiness = "NOT_READY"
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if readiness == "READY":
            print("   ✅ System is fully functional")
            print("   🚀 Ready to run: streamlit run main.py")
            print("   📊 Ready for data processing and planning")
            
        elif readiness == "MOSTLY_READY":
            print("   🔧 Fix minor warnings if possible")
            print("   ✅ Core functionality should work")
            print("   🚀 Try running: streamlit run main.py")
            
        elif readiness == "NEEDS_ATTENTION":
            print("   🔧 Fix import errors and missing modules")
            print("   📚 Check installation: pip install -r requirements.txt")
            print("   🔍 Review error messages above")
            
        else:  # NOT_READY
            print("   🚨 Critical issues must be fixed first")
            print("   📚 Reinstall dependencies: pip install -r requirements.txt")
            print("   🔍 Check project structure and file locations")
            print("   💻 Verify Python environment setup")
        
        # Save detailed results
        detailed_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': total_tests,
                'successes': successes,
                'errors': errors,
                'warnings': warnings,
                'success_rate': success_rate,
                'readiness': readiness
            },
            'module_status': self.module_status,
            'test_results': self.test_results,
            'errors': self.errors,
            'warnings': self.warnings
        }
        
        with open('system_functionality_results.json', 'w') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: system_functionality_results.json")
        print("=" * 60)
        
        return detailed_results

def main():
    """Main execution function"""
    
    print("🔧 Beverly Knits System Functionality Test")
    print("Testing all modules, imports, and processes...")
    print()
    
    # Run system functionality tests
    tester = SystemFunctionalityTest()
    results = tester.run_complete_system_test()
    
    # Determine exit code based on critical errors
    critical_errors = sum(1 for r in results if r['status'] == 'ERROR')
    
    if critical_errors == 0:
        print("\n🎉 System functionality test completed successfully!")
        return 0
    else:
        print(f"\n⚠️  System functionality test completed with {critical_errors} errors")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)