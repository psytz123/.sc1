#!/usr/bin/env python3
"""
Quick System Health Check for Beverly Knits
Validates core system functionality, imports, and processes
"""

import sys
import importlib
import traceback
import time
from pathlib import Path

def quick_system_health_check():
    """Quick comprehensive system health check"""
    
    print("🏥 Beverly Knits System Health Check")
    print("=" * 50)
    
    health_status = {
        'environment': False,
        'imports': False,
        'models': False,
        'engine': False,
        'workflow': False,
        'ui': False
    }
    
    issues = []
    
    # 1. Environment Check
    print("\n🌍 Environment Check...")
    try:
        # Check Python version
        if sys.version_info >= (3, 8):
            print("   ✅ Python version OK")
        else:
            print(f"   ❌ Python version too old: {sys.version_info}")
            issues.append("Python version < 3.8")
        
        # Check working directory
        if Path('main.py').exists():
            print("   ✅ Running from correct directory")
        else:
            print("   ❌ Not in project root (main.py missing)")
            issues.append("Wrong working directory")
        
        # Check project structure
        required_dirs = ['engine', 'models', 'config', 'data']
        missing_dirs = [d for d in required_dirs if not Path(d).exists()]
        
        if not missing_dirs:
            print("   ✅ Project structure complete")
            health_status['environment'] = True
        else:
            print(f"   ⚠️  Missing directories: {missing_dirs}")
            issues.append(f"Missing directories: {missing_dirs}")
            
    except Exception as e:
        print(f"   ❌ Environment check failed: {e}")
        issues.append(f"Environment error: {e}")
    
    # 2. Core Dependencies Check
    print("\n📦 Dependencies Check...")
    try:
        required_packages = [
            ('pandas', 'Data processing'),
            ('numpy', 'Numerical calculations'),
            ('streamlit', 'Web interface'),
            ('plotly', 'Charts and visualization'),
            ('pathlib', 'File operations'),
            ('datetime', 'Date handling'),
            ('decimal', 'Precise calculations'),
            ('json', 'Data serialization')
        ]
        
        missing_packages = []
        
        for package, description in required_packages:
            try:
                importlib.import_module(package)
                print(f"   ✅ {package} - {description}")
            except ImportError:
                print(f"   ❌ {package} - {description} (MISSING)")
                missing_packages.append(package)
        
        if not missing_packages:
            health_status['imports'] = True
        else:
            issues.append(f"Missing packages: {missing_packages}")
            
    except Exception as e:
        print(f"   ❌ Dependencies check failed: {e}")
        issues.append(f"Dependencies error: {e}")
    
    # 3. Module Import Check
    print("\n🔌 Module Import Check...")
    try:
        sys.path.insert(0, '.')
        
        core_modules = [
            ('engine.planner', 'Planning engine'),
            ('models.forecast', 'Forecast model'),
            ('models.bom', 'BOM model'),
            ('models.inventory', 'Inventory model'),
            ('models.supplier', 'Supplier model'),
            ('models.recommendation', 'Recommendation model'),
            ('config.settings', 'Configuration')
        ]
        
        failed_imports = []
        successful_imports = 0
        
        for module_name, description in core_modules:
            try:
                module = importlib.import_module(module_name)
                print(f"   ✅ {module_name} - {description}")
                successful_imports += 1
            except Exception as e:
                print(f"   ❌ {module_name} - {description} ({str(e)[:50]}...)")
                failed_imports.append(module_name)
        
        if len(failed_imports) == 0:
            print("   🎉 All core modules imported successfully!")
            health_status['models'] = True
        elif successful_imports >= len(core_modules) * 0.7:
            print(f"   ⚠️  Most modules OK ({successful_imports}/{len(core_modules)})")
            issues.append(f"Some module import issues: {failed_imports}")
        else:
            print(f"   ❌ Too many import failures ({successful_imports}/{len(core_modules)})")
            issues.append(f"Critical import failures: {failed_imports}")
            
    except Exception as e:
        print(f"   ❌ Module import check failed: {e}")
        issues.append(f"Import error: {e}")
    
    # 4. Planning Engine Check
    print("\n⚙️  Planning Engine Check...")
    try:
        from engine.planner import RawMaterialPlanner
        from config.settings import PlanningConfig
        
        # Test instantiation
        config = PlanningConfig()
        planner = RawMaterialPlanner(config)
        print("   ✅ RawMaterialPlanner instantiated")
        
        # Test required methods
        required_methods = [
            'plan', 'generate_summary_report', 'export_results_to_dataframes'
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if hasattr(planner, method_name) and callable(getattr(planner, method_name)):
                print(f"   ✅ {method_name} method available")
            else:
                print(f"   ❌ {method_name} method missing")
                missing_methods.append(method_name)
        
        if not missing_methods:
            print("   🎉 All planning methods available!")
            health_status['engine'] = True
        else:
            issues.append(f"Missing planning methods: {missing_methods}")
            
    except Exception as e:
        print(f"   ❌ Planning engine check failed: {e}")
        issues.append(f"Planning engine error: {e}")
    
    # 5. Basic Workflow Test
    print("\n🔄 Basic Workflow Test...")
    try:
        import pandas as pd
        from engine.planner import RawMaterialPlanner
        from config.settings import PlanningConfig
        from models.forecast import FinishedGoodsForecast
        from models.bom import BillOfMaterials
        from models.inventory import Inventory
        from models.supplier import Supplier
        
        config = PlanningConfig()
        planner = RawMaterialPlanner(config)
        
        # Create minimal test data
        forecasts = [
            FinishedGoodsForecast(
                sku_id='TEST-SKU',
                forecast_qty=100,
                source='sales_order',
                forecast_date='2025-02-01'
            )
        ]
        
        boms = [
            BillOfMaterials(
                sku_id='TEST-SKU',
                material_id='TEST-MAT',
                qty_per_unit=1.0,
                unit='yards'
            )
        ]
        
        inventory = [
            Inventory(
                material_id='TEST-MAT',
                on_hand_qty=25,
                unit='yards'
            )
        ]
        
        suppliers = [
            Supplier(
                material_id='TEST-MAT',
                supplier_id='TEST-SUP',
                cost_per_unit=10.0,
                lead_time_days=14,
                moq=50
            )
        ]
        
        # Test basic workflow steps
        workflow_tests = [
            ('Complete Planning Process', lambda: planner.plan(forecasts, boms, inventory, suppliers))
        ]
        
        workflow_failures = []
        
        for step_name, step_func in workflow_tests:
            try:
                result = step_func()
                if result is not None and len(result) > 0:
                    print(f"   ✅ {step_name} works")
                else:
                    print(f"   ⚠️  {step_name} returns empty result")
            except Exception as e:
                print(f"   ❌ {step_name} failed: {str(e)[:50]}...")
                workflow_failures.append(step_name)
        
        if not workflow_failures:
            print("   🎉 Basic workflow functional!")
            health_status['workflow'] = True
        else:
            issues.append(f"Workflow issues: {workflow_failures}")
            
    except Exception as e:
        print(f"   ❌ Workflow test failed: {e}")
        issues.append(f"Workflow error: {e}")
    
    # 6. UI Components Check
    print("\n🖥️  UI Components Check...")
    try:
        import streamlit as st
        print("   ✅ Streamlit imported")
        
        # Check main.py exists and has Streamlit code
        if Path('main.py').exists():
            main_content = Path('main.py').read_text()
            
            ui_components = ['st.', 'streamlit']
            has_ui = any(component in main_content for component in ui_components)
            
            if has_ui:
                print("   ✅ Streamlit UI components found in main.py")
                health_status['ui'] = True
            else:
                print("   ⚠️  No Streamlit components found in main.py")
                issues.append("No UI components in main.py")
        else:
            print("   ❌ main.py not found")
            issues.append("main.py missing")
        
        # Check plotting capabilities
        try:
            import plotly.graph_objects as go
            print("   ✅ Plotly charting available")
        except ImportError:
            print("   ⚠️  Plotly not available")
            issues.append("Plotly missing")
            
    except ImportError:
        print("   ❌ Streamlit not available")
        issues.append("Streamlit missing")
    except Exception as e:
        print(f"   ❌ UI check failed: {e}")
        issues.append(f"UI error: {e}")
    
    # 7. Data Files Check
    print("\n📁 Data Files Check...")
    try:
        data_dir = Path('data')
        
        if data_dir.exists():
            csv_files = list(data_dir.glob('*.csv'))
            print(f"   ✅ Data directory exists with {len(csv_files)} CSV files")
            
            # Check for key data files
            key_files = [
                'Yarn_ID.csv', 'Style_BOM.csv', 'inventory_updated.csv',
                'Supplier_ID.csv', 'eFab_SO_List.csv'
            ]
            
            existing_files = [f for f in key_files if (data_dir / f).exists()]
            missing_files = [f for f in key_files if f not in existing_files]
            
            print(f"   📊 Key files: {len(existing_files)}/{len(key_files)} present")
            
            if missing_files:
                print(f"   ⚠️  Missing files: {missing_files}")
        else:
            print("   ⚠️  Data directory not found")
            
    except Exception as e:
        print(f"   ❌ Data files check failed: {e}")
    
    # Health Summary
    print("\n" + "=" * 50)
    print("🏥 SYSTEM HEALTH SUMMARY")
    print("=" * 50)
    
    # Calculate overall health
    health_components = list(health_status.values())
    healthy_components = sum(health_components)
    total_components = len(health_components)
    health_percentage = (healthy_components / total_components) * 100
    
    print(f"🔍 Components Checked: {total_components}")
    print(f"✅ Healthy Components: {healthy_components}")
    print(f"❌ Issues Found: {len(issues)}")
    print(f"📊 Health Score: {health_percentage:.1f}%")
    
    # Overall status
    if health_percentage >= 90:
        print("\n🟢 SYSTEM STATUS: HEALTHY")
        print("   🚀 Ready to run: streamlit run main.py")
        system_status = "HEALTHY"
    elif health_percentage >= 70:
        print("\n🟡 SYSTEM STATUS: MOSTLY HEALTHY")
        print("   ⚠️  Some minor issues - system should work")
        print("   🚀 Try running: streamlit run main.py")
        system_status = "MOSTLY_HEALTHY"
    elif health_percentage >= 50:
        print("\n🟠 SYSTEM STATUS: NEEDS ATTENTION")
        print("   🔧 Fix issues before running the system")
        system_status = "NEEDS_ATTENTION"
    else:
        print("\n🔴 SYSTEM STATUS: CRITICAL ISSUES")
        print("   🚨 Major problems - system likely won't work")
        system_status = "CRITICAL"
    
    # Issue summary
    if issues:
        print(f"\n🚨 Issues to Address ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    # Component status breakdown
    print(f"\n📊 Component Status:")
    component_names = ['Environment', 'Imports', 'Models', 'Engine', 'Workflow', 'UI']
    for name, status in zip(component_names, health_status.values()):
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {name}")
    
    # Quick fix suggestions
    print(f"\n💡 Quick Fixes:")
    if not health_status['imports']:
        print("   📦 Install missing packages: pip install -r requirements.txt")
    
    if not health_status['models'] or not health_status['engine']:
        print("   🔧 Check file structure and fix import errors")
    
    if not health_status['workflow']:
        print("   🔄 Review planning engine implementation")
    
    if not health_status['ui']:
        print("   🖥️  Check Streamlit installation and main.py")
    
    print(f"\n💾 For detailed diagnostics, run: python system_functionality_test.py")
    
    return system_status, issues

def test_quick_functionality():
    """Quick functionality test - can we run basic operations?"""
    
    print("\n⚡ Quick Functionality Test...")
    
    try:
        # Test pandas operations
        import pandas as pd
        test_df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        assert len(test_df) == 3
        print("   ✅ Pandas operations work")
        
        # Test numpy operations
        import numpy as np
        test_array = np.array([1, 2, 3])
        assert np.sum(test_array) == 6
        print("   ✅ NumPy operations work")
        
        # Test file operations
        test_file = Path('temp_test.txt')
        test_file.write_text('test')
        content = test_file.read_text()
        test_file.unlink()
        assert content == 'test'
        print("   ✅ File operations work")
        
        # Test JSON operations
        import json
        test_data = {'test': 'value'}
        json_str = json.dumps(test_data)
        loaded_data = json.loads(json_str)
        assert loaded_data == test_data
        print("   ✅ JSON operations work")
        
        print("   🎉 All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Functionality test failed: {e}")
        return False

def main():
    """Main execution"""
    
    start_time = time.time()
    
    # Run health check
    system_status, issues = quick_system_health_check()
    
    # Run quick functionality test
    functionality_ok = test_quick_functionality()
    
    execution_time = time.time() - start_time
    
    print(f"\n⏱️  Health check completed in {execution_time:.2f} seconds")
    
    # Final recommendation
    print(f"\n🎯 FINAL RECOMMENDATION:")
    
    if system_status == "HEALTHY" and functionality_ok:
        print("   🎉 System is ready to use!")
        print("   ▶️  Next: streamlit run main.py")
        exit_code = 0
        
    elif system_status in ["HEALTHY", "MOSTLY_HEALTHY"] and functionality_ok:
        print("   ✅ System should work with minor issues")
        print("   ▶️  Try: streamlit run main.py")
        print("   🔧 Fix minor issues when convenient")
        exit_code = 0
        
    elif system_status == "NEEDS_ATTENTION":
        print("   ⚠️  Fix issues before using the system")
        print("   🔧 Address the issues listed above")
        print("   📚 Run: pip install -r requirements.txt")
        exit_code = 1
        
    else:  # CRITICAL
        print("   🚨 System has critical issues")
        print("   🔧 Major fixes needed before system will work")
        print("   📚 Check installation and project setup")
        exit_code = 2
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)