#!/usr/bin/env python3
"""Quick System Health Check - Validates core functionality"""

import sys
import importlib
from pathlib import Path

def main():
    print("🏥 Beverly Knits - Quick Health Check")
    print("=" * 40)
    
    issues = []
    
    # 1. Environment
    print("\n🌍 Environment...")
    if Path('main.py').exists():
        print("   ✅ Project directory OK")
    else:
        print("   ❌ Wrong directory")
        issues.append("Not in project root")
    
    # 2. Dependencies
    print("\n📦 Dependencies...")
    deps = ['pandas', 'numpy', 'streamlit', 'plotly']
    for dep in deps:
        try:
            importlib.import_module(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            issues.append(f"Missing {dep}")
    
    # 3. Modules
    print("\n🔌 Modules...")
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
    print("\n⚡ Basic Test...")
    try:
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        assert len(df) == 3
        print("   ✅ Pandas works")
    except Exception as e:
        print("   ❌ Pandas test failed")
        issues.append("Basic functionality broken")
    
    # Summary
    print("\n" + "=" * 40)
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
