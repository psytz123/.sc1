#!/usr/bin/env python3
"""
Setup Testing Environment for Beverly Knits
Creates all necessary test files and provides instructions
"""

import sys
from pathlib import Path

def create_quick_health_check():
    """Create the quick health check script"""
    
    content = '''#!/usr/bin/env python3
"""Quick System Health Check - Validates core functionality"""

import sys
import importlib
from pathlib import Path

def main():
    print("🏥 Beverly Knits - Quick Health Check")
    print("=" * 40)
    
    issues = []
    
    # 1. Environment
    print("\\n🌍 Environment...")
    if Path('main.py').exists():
        print("   ✅ Project directory OK")
    else:
        print("   ❌ Wrong directory")
        issues.append("Not in project root")
    
    # 2. Dependencies
    print("\\n📦 Dependencies...")
    deps = ['pandas', 'numpy', 'streamlit', 'plotly']
    for dep in deps:
        try:
            importlib.import_module(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            issues.append(f"Missing {dep}")
    
    # 3. Modules
    print("\\n🔌 Modules...")
    sys.path.insert(0, '.')
    modules = ['engine.planner', 'models.forecast', 'models.bom']
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"   ✅ {mod}")
        except Exception as e:
            print(f"   ❌ {mod}")
            issues.append(f"Module {mod}: {str(e)[:30]}")
    
    # 4. Basic Test
    print("\\n⚡ Basic Test...")
    try:
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        assert len(df) == 3
        print("   ✅ Pandas works")
    except Exception as e:
        print("   ❌ Pandas test failed")
        issues.append("Basic functionality broken")
    
    # Summary
    print("\\n" + "=" * 40)
    if not issues:
        print("🎉 SYSTEM HEALTHY - Ready to use!")
        print("▶️  Next: streamlit run main.py")
        return 0
    else:
        print(f"⚠️  {len(issues)} ISSUES FOUND:")
        for issue in issues:
            print(f"   • {issue}")
        print("🔧 Fix these issues first")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    Path('quick_system_health_check.py').write_text(content)

def create_data_test():
    """Create the quick data test script"""
    
    content = '''#!/usr/bin/env python3
"""Quick Real Data Test - Validates your CSV files"""

import sys
import pandas as pd
from pathlib import Path

def main():
    print("📊 Beverly Knits - Quick Data Test")
    print("=" * 40)
    
    data_dir = Path('data')
    if not data_dir.exists():
        print("❌ No data directory found")
        return 1
    
    files = {
        'Yarn_ID.csv': 'Yarn Master',
        'Style_BOM.csv': 'Bill of Materials', 
        'inventory_updated.csv': 'Inventory',
        'Supplier_ID.csv': 'Suppliers'
    }
    
    issues = []
    loaded = 0
    
    print("\\n📁 Loading data files...")
    for filename, description in files.items():
        file_path = data_dir / filename
        try:
            if file_path.exists():
                df = pd.read_csv(file_path)
                print(f"   ✅ {description}: {len(df):,} rows")
                loaded += 1
                
                # Quick quality check
                if filename == 'Yarn_ID.csv' and 'Cost_Pound' in df.columns:
                    cost_issues = df['Cost_Pound'].astype(str).str.contains('\\$0|^0').sum()
                    if cost_issues > 0:
                        issues.append(f"{cost_issues} yarns with $0 cost")
                
                if filename == 'Style_BOM.csv' and 'qty_per_unit' in df.columns:
                    bom_issues = ((df['qty_per_unit'] <= 0) | (df['qty_per_unit'] > 1)).sum()
                    if bom_issues > 0:
                        issues.append(f"{bom_issues} invalid BOM percentages")
                        
            else:
                print(f"   ❌ {description}: Not found")
        except Exception as e:
            print(f"   💥 {description}: Error - {str(e)[:30]}")
            issues.append(f"{description} load error")
    
    print("\\n" + "=" * 40)
    print(f"📊 SUMMARY: {loaded}/{len(files)} files loaded")
    
    if issues:
        print(f"⚠️  {len(issues)} data issues found:")
        for issue in issues:
            print(f"   • {issue}")
    
    if loaded >= 2:
        print("✅ SUFFICIENT DATA - Basic testing possible")
        if not issues:
            print("🚀 Ready for: streamlit run main.py")
        else:
            print("🔧 Consider running data_integration_v2.py")
        return 0
    else:
        print("❌ INSUFFICIENT DATA - Need more CSV files")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    Path('execute_real_data_tests.py').write_text(content)

def create_workflow_test():
    """Create a simple workflow test"""
    
    content = '''#!/usr/bin/env python3
"""Simple Workflow Test - Tests planning process"""

import sys
import pandas as pd
from pathlib import Path

def main():
    print("🔄 Beverly Knits - Workflow Test")
    print("=" * 40)
    
    try:
        sys.path.insert(0, '.')
        from engine.planner import MaterialPlanner
        
        print("\\n⚙️  Testing planning engine...")
        planner = MaterialPlanner()
        print("   ✅ Planner instantiated")
        
        # Create test data
        forecast = pd.DataFrame({
            'sku_id': ['TEST-001'],
            'forecast_qty': [100],
            'source': ['test'],
            'forecast_date': ['2025-02-01']
        })
        
        bom = pd.DataFrame({
            'sku_id': ['TEST-001'],
            'material_id': ['MAT-001'],
            'qty_per_unit': [1.0]
        })
        
        print("\\n🔄 Testing workflow steps...")
        
        # Step 1
        result1 = planner.unify_forecasts(forecast)
        print(f"   ✅ Step 1: Forecasts unified ({len(result1)} records)")
        
        # Step 2  
        result2 = planner.explode_bom(bom, result1)
        print(f"   ✅ Step 2: BOM exploded ({len(result2)} requirements)")
        
        print("\\n🎉 WORKFLOW FUNCTIONAL")
        print("🚀 Core planning process works!")
        return 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Check module structure")
        return 1
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        print("🔧 Check planning engine implementation")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    Path('workflow_integration_test.py').write_text(content)

def setup_tests():
    """Set up the testing environment"""
    
    print("🔧 Setting Up Beverly Knits Testing Environment")
    print("=" * 50)
    
    # Check environment
    if not Path('main.py').exists():
        print("❌ Error: Please run this from the Beverly Knits project directory")
        print("   (The directory that contains main.py)")
        return False
    
    print("✅ Found main.py - in correct directory")
    
    # Create test files
    print("\\n📝 Creating test files...")
    
    try:
        create_quick_health_check()
        print("   ✅ Created: quick_system_health_check.py")
        
        create_data_test()
        print("   ✅ Created: execute_real_data_tests.py")
        
        create_workflow_test()
        print("   ✅ Created: workflow_integration_test.py")
        
    except Exception as e:
        print(f"   ❌ Error creating files: {e}")
        return False
    
    print("\\n🎉 Testing environment set up successfully!")
    return True

def show_instructions():
    """Show usage instructions"""
    
    print("\\n" + "=" * 50)
    print("🚀 HOW TO TEST YOUR SYSTEM")
    print("=" * 50)
    
    print("\\n1️⃣  QUICK SYSTEM CHECK (30 seconds)")
    print("   Run: python quick_system_health_check.py")
    print("   ✓ Tests if all modules and dependencies work")
    print("   ✓ Perfect first test to run")
    
    print("\\n2️⃣  DATA VALIDATION (1 minute)")
    print("   Run: python execute_real_data_tests.py")
    print("   ✓ Tests your actual CSV files")
    print("   ✓ Finds data quality issues")
    
    print("\\n3️⃣  WORKFLOW TEST (2 minutes)")
    print("   Run: python workflow_integration_test.py")
    print("   ✓ Tests the planning process works")
    print("   ✓ Validates core business logic")
    
    print("\\n🎯 RECOMMENDED ORDER:")
    print("   1. Run system check first")
    print("   2. If that passes, run data validation")
    print("   3. If both pass, run workflow test")
    print("   4. If all pass: streamlit run main.py")
    
    print("\\n🔧 IF TESTS FAIL:")
    print("   • System check fails → Fix dependencies/modules")
    print("   • Data test fails → Fix CSV files or run data_integration_v2.py")
    print("   • Workflow fails → Check planning engine code")
    
    print("\\n📊 WHAT EACH TEST TELLS YOU:")
    print("   ✅ System Check: 'Is my code environment working?'")
    print("   ✅ Data Test: 'Is my data ready to use?'")
    print("   ✅ Workflow Test: 'Does the planning process work?'")

def main():
    """Main setup function"""
    
    if not setup_tests():
        return 1
    
    show_instructions()
    
    print("\\n" + "=" * 50)
    print("💡 READY TO START TESTING!")
    print("=" * 50)
    print("\\nRun this command to start:")
    print("📋 python quick_system_health_check.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())