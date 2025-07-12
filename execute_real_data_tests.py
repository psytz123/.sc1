#!/usr/bin/env python3
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
    
    print("\n📁 Loading data files...")
    for filename, description in files.items():
        file_path = data_dir / filename
        try:
            if file_path.exists():
                df = pd.read_csv(file_path)
                print(f"   ✅ {description}: {len(df):,} rows")
                loaded += 1
                
                # Quick quality check
                if filename == 'Yarn_ID.csv' and 'Cost_Pound' in df.columns:
                    cost_issues = df['Cost_Pound'].astype(str).str.contains('\$0|^0').sum()
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
    
    print("\n" + "=" * 40)
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
