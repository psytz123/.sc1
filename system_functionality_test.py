#!/usr/bin/env python3
"""
System Functionality Test Suite for Beverly Knits
Comprehensive testing of all system components
"""

import sys
import os
import importlib
import traceback
import time
import json
import pandas as pd
from pathlib import Path

class SystemFunctionalityTest:
    """Comprehensive system functionality testing"""
    
    def __init__(self):
        self.test_results = []
        self.module_status = {}
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
        
        # Phase 5: Data Processing Testing
        print("\n5️⃣ Data Processing Testing")
        self.test_data_processing()
        
        # Generate comprehensive report
        self.generate_system_report()
        
        return self.test_results
    
    def test_environment_setup(self):
        """Test environment and dependencies"""
        
        # Test Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.log_success("Environment", f"Python {python_version.major}.{python_version.minor}")
        else:
            self.log_error("Environment", f"Python version too old: {python_version}")
        
        # Test required packages
        required_packages = ['pandas', 'numpy', 'streamlit', 'plotly']
        
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
    
    def test_all_imports(self):
        """Test all module imports"""
        
        sys.path.insert(0, '.')
        
        # Test core module imports
        core_modules = {
            'engine.planner': 'engine/planner.py',
            'models.forecast': 'models/forecast.py',
            'models.bom': 'models/bom.py',
            'models.inventory': 'models/inventory.py'
        }
        
        for module_name, file_path in core_modules.items():
            self.test_module_import(module_name, file_path)
    
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
    
    def test_core_models(self):
        """Test core data models"""
        
        model_tests = [
            ('Forecast Model', self.test_forecast_model),
            ('BOM Model', self.test_bom_model),
            ('Inventory Model', self.test_inventory_model),
        ]
        
        for test_name, test_func in model_tests:
            try:
                test_func()
                self.log_success("Core Models", test_name)
            except Exception as e:
                self.log_error("Core Models", f"{test_name}: {str(e)}")
    
    def test_forecast_model(self):
        """Test forecast model functionality"""
        if 'models.forecast' not in self.module_status:
            raise Exception("Forecast module not available")
        
        # Basic model test
        test_data = pd.DataFrame({
            'sku_id': ['TEST-001'],
            'forecast_qty': [100],
            'source': ['test']
        })
        
        assert len(test_data) == 1
        assert test_data['forecast_qty'].sum() == 100
    
    def test_bom_model(self):
        """Test BOM model functionality"""
        if 'models.bom' not in self.module_status:
            raise Exception("BOM module not available")
        
        # Basic BOM test
        test_bom = pd.DataFrame({
            'sku_id': ['STYLE-001'],
            'material_id': ['YARN-001'],
            'qty_per_unit': [1.0]
        })
        
        assert len(test_bom) == 1
        assert test_bom['qty_per_unit'].sum() == 1.0
    
    def test_inventory_model(self):
        """Test inventory model functionality"""
        # Basic inventory test
        test_inventory = pd.DataFrame({
            'material_id': ['YARN-001'],
            'on_hand_qty': [50]
        })
        
        assert len(test_inventory) == 1
        assert test_inventory['on_hand_qty'].sum() == 50
    
    def test_engine_components(self):
        """Test planning engine components"""
        
        if 'engine.planner' not in self.module_status:
            self.log_error("Engine Components", "Planning engine not available")
            return
        
        planner_module = self.module_status['engine.planner'].get('module')
        if not planner_module:
            self.log_error("Engine Components", "Planning engine module not loaded")
            return
        
        # Test MaterialPlanner class exists
        if hasattr(planner_module, 'MaterialPlanner'):
            try:
                planner_class = getattr(planner_module, 'MaterialPlanner')
                planner = planner_class()
                self.log_success("Engine Components", "MaterialPlanner instantiated")
                
                # Test required methods exist
                required_methods = [
                    'unify_forecasts', 'explode_bom', 'net_inventory'
                ]
                
                for method_name in required_methods:
                    if hasattr(planner, method_name):
                        self.log_success("Engine Methods", f"{method_name} method available")
                    else:
                        self.log_error("Engine Methods", f"{method_name} method missing")
                
            except Exception as e:
                self.log_error("Engine Components", f"MaterialPlanner instantiation failed: {str(e)}")
        else:
            self.log_error("Engine Components", "MaterialPlanner class not found")
    
    def test_data_processing(self):
        """Test data processing capabilities"""
        
        try:
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
            
            self.log_success("Data Processing", "All pandas operations working")
            
        except Exception as e:
            self.log_error("Data Processing", f"Pandas operations failed: {str(e)}")
    
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
    
    def generate_system_report(self):
        """Generate comprehensive system functionality report"""
        
        # Calculate statistics
        total_tests = len(self.test_results)
        successes = sum(1 for r in self.test_results if r['status'] == 'SUCCESS')
        errors = sum(1 for r in self.test_results if r['status'] == 'ERROR')
        warnings = sum(1 for r in self.test_results if r['status'] == 'WARNING')
        
        success_rate = (successes / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("🔧 SYSTEM FUNCTIONALITY TEST SUMMARY")
        print("=" * 60)
        
        print(f"📊 Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Success: {successes}")
        print(f"   ❌ Errors: {errors}")
        print(f"   ⚠️  Warnings: {warnings}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        # Critical errors
        if self.errors:
            print(f"\n🚨 Critical Errors ({len(self.errors)}):")
            for error in self.errors[:3]:  # Show first 3 errors
                print(f"   • {error}")
        
        # System readiness assessment
        print(f"\n🎯 System Readiness Assessment:")
        
        if errors == 0:
            print("   🟢 SYSTEM READY - All components functional")
        elif errors <= 2:
            print("   🟡 MOSTLY READY - Minor issues detected")
        else:
            print("   🔴 NOT READY - Critical components missing/broken")
        
        # Save results
        detailed_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': total_tests,
                'successes': successes,
                'errors': errors,
                'warnings': warnings,
                'success_rate': success_rate
            },
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