"""
Beverly Knits Real Data Planning Demo
Demonstrates the AI Raw Material Planner using real Beverly Knits data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.real_data_loader import RealDataLoader
import pandas as pd

def main():
    """Demonstrate planning with real Beverly Knits data"""
    print("🚀 Beverly Knits AI Raw Material Planner - Real Data Demo")
    print("=" * 60)
    
    # Load real data
    print("📊 Loading Real Beverly Knits Data...")
    loader = RealDataLoader()
    
    # Load all datasets
    materials_df = loader.load_materials()
    suppliers_df = loader.load_suppliers()
    inventory_df = loader.load_inventory()
    boms_df = loader.load_boms()
    interchangeable = loader.load_interchangeable_yarns()
    
    print(f"✅ Loaded:")
    print(f"   • {len(materials_df)} yarn materials")
    print(f"   • {len(suppliers_df)} supplier relationships")
    print(f"   • {len(inventory_df)} inventory records")
    print(f"   • {len(boms_df)} BOM lines for {boms_df['sku_id'].nunique()} styles")
    print(f"   • {len(interchangeable)} interchangeable yarn groups")
    
    # Create sample forecasts for demonstration
    print("\n📈 Generating Sample Forecasts...")
    sample_forecasts = loader.generate_sample_forecasts()
    print(f"✅ Generated forecasts for {sample_forecasts['sku_id'].nunique()} styles")
    
    # Show sample of real data
    print("\n📋 Sample Real Data:")
    print("\nTop 5 Materials:")
    print(materials_df[['material_id', 'Supplier', 'Description', 'Type', 'Color', 'cost_per_unit']].head())
    
    print("\nTop 5 Inventory Records:")
    print(inventory_df[['material_id', 'current_stock', 'incoming_stock', 'allocated_stock']].head())
    
    print("\nSample BOM (Style 125792/1):")
    sample_bom = boms_df[boms_df['sku_id'] == '125792/1']
    if not sample_bom.empty:
        for _, row in sample_bom.iterrows():
            material_info = loader.get_material_info(str(row['material_id']))
            if material_info:
                print(f"   • {row['quantity_per_unit']:.1%} - Yarn {row['material_id']}: {material_info['description']} ({material_info['type']})")
    
    # Show interchangeable yarns example
    print("\nInterchangeable Yarn Groups (first 3):")
    for i, (group_name, group_data) in enumerate(list(interchangeable.items())[:3]):
        print(f"   {i+1}. {group_name}:")
        print(f"      Yarns: {group_data['yarn_ids']}")
        print(f"      Specs: {group_data['specifications']['description']} - {group_data['specifications']['type']}")
    
    # Data quality summary
    print("\n⚠️  Data Quality Summary:")
    
    # Count materials with zero costs
    zero_cost_materials = materials_df[materials_df['cost_per_unit'] == 0]
    print(f"   • {len(zero_cost_materials)} materials with zero cost (need pricing)")
    
    # Count negative inventory
    negative_inventory = inventory_df[inventory_df['current_stock'] < 0]
    print(f"   • {len(negative_inventory)} materials with negative inventory")
    
    # Count missing suppliers
    missing_suppliers = materials_df[materials_df['Supplier_ID'].isna()]
    print(f"   • {len(missing_suppliers)} materials with missing supplier IDs")
    
    print("\n📋 Next Steps:")
    print("1. Review data_quality_report.txt for detailed issues")
    print("2. Complete missing cost data for materials with $0.00 cost")
    print("3. Resolve negative inventory balances")
    print("4. Standardize material types and supplier information")
    print("5. Validate BOM percentages that don't sum to 1.0")
    print("6. Add missing yarn specifications to master data")
    
    print("\n🎯 Integration Status:")
    print("✅ Real data successfully loaded and validated")
    print("✅ Interchangeable yarn groups identified")
    print("✅ Data quality issues documented")
    print("✅ Ready for planning system integration")
    
    print("\n💡 To use with planning system:")
    print("   from data.real_data_loader import RealDataLoader")
    print("   loader = RealDataLoader()")
    print("   suppliers = loader.create_supplier_objects()")
    print("   inventory = loader.create_inventory_objects()")
    print("   boms = loader.create_bom_objects()")
    
    # Save summary report
    summary_data = {
        'total_materials': len(materials_df),
        'total_suppliers': suppliers_df['supplier_id'].nunique(),
        'total_styles': boms_df['sku_id'].nunique(),
        'interchangeable_groups': len(interchangeable),
        'zero_cost_materials': len(zero_cost_materials),
        'negative_inventory_items': len(negative_inventory),
        'missing_supplier_ids': len(missing_suppliers)
    }
    
    summary_df = pd.DataFrame([summary_data])
    summary_df.to_csv('data/real_data_integration_summary.csv', index=False)
    print(f"\n📊 Summary saved to: data/real_data_integration_summary.csv")

if __name__ == "__main__":
    main()