#!/usr/bin/env python3
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
        
        print("\n⚙️  Testing planning engine...")
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
        
        print("\n🔄 Testing workflow steps...")
        
        # Step 1
        result1 = planner.unify_forecasts(forecast)
        print(f"   ✅ Step 1: Forecasts unified ({len(result1)} records)")
        
        # Step 2  
        result2 = planner.explode_bom(bom, result1)
        print(f"   ✅ Step 2: BOM exploded ({len(result2)} requirements)")
        
        print("\n🎉 WORKFLOW FUNCTIONAL")
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
