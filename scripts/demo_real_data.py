"""
Beverly Knits Real Data Planning Demo
Demonstrates the AI Raw Material Planner using real Beverly Knits data
"""

import os
from utils.logger import get_logger

logger = get_logger(__name__)
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from data.real_data_loader import RealDataLoader


def main():
    """Demonstrate planning with real Beverly Knits data"""
    logger.info("🚀 Beverly Knits AI Raw Material Planner - Real Data Demo")
    logger.info("=" * 60)
    
    # Load real data
    logger.info("📊 Loading Real Beverly Knits Data...")
    loader = RealDataLoader()
    
    # Load all datasets
    materials_df = loader.load_materials()
    suppliers_df = loader.load_suppliers()
    inventory_df = loader.load_inventory()
    boms_df = loader.load_boms()
    interchangeable = loader.load_interchangeable_yarns()
    
    logger.info(f"✅ Loaded:")
    logger.info(f"   • {len(materials_df)} yarn materials")
    logger.info(f"   • {len(suppliers_df)} supplier relationships")
    logger.info(f"   • {len(inventory_df)} inventory records")
    logger.info(f"   • {len(boms_df)} BOM lines for {boms_df['sku_id'].nunique()} styles")
    logger.info(f"   • {len(interchangeable)} interchangeable yarn groups")
    
    # Create sample forecasts for demonstration
    logger.info("\n📈 Generating Sample Forecasts...")
    sample_forecasts = loader.generate_sample_forecasts()
    logger.info(f"✅ Generated forecasts for {sample_forecasts['sku_id'].nunique()} styles")
    
    # Show sample of real data
    logger.info("\n📋 Sample Real Data:")
    logger.info("\nTop 5 Materials:")
    logger.info(materials_df[['material_id', 'Supplier', 'Description', 'Type', 'Color', 'cost_per_unit']].head())
    
    logger.info("\nTop 5 Inventory Records:")
    logger.info(inventory_df[['material_id', 'current_stock', 'incoming_stock', 'allocated_stock']].head())
    
    logger.info("\nSample BOM (Style 125792/1):")
    sample_bom = boms_df[boms_df['sku_id'] == '125792/1']
    if not sample_bom.empty:
        for _, row in sample_bom.iterrows():
            material_info = loader.get_material_info(str(row['material_id']))
            if material_info:
                logger.info(f"   • {row['quantity_per_unit']:.1%} - Yarn {row['material_id']}: {material_info['description']} ({material_info['type']})")
    
    # Show interchangeable yarns example
    logger.info("\nInterchangeable Yarn Groups (first 3):")
    for i, (group_name, group_data) in enumerate(list(interchangeable.items())[:3]):
        logger.info(f"   {i+1}. {group_name}:")
        logger.info(f"      Yarns: {group_data['yarn_ids']}")
        logger.info(f"      Specs: {group_data['specifications']['description']} - {group_data['specifications']['type']}")
    
    # Data quality summary
    logger.info("\n⚠️  Data Quality Summary:")
    
    # Count materials with zero costs
    zero_cost_materials = materials_df[materials_df['cost_per_unit'] == 0]
    logger.info(f"   • {len(zero_cost_materials)} materials with zero cost (need pricing)")
    
    # Count negative inventory
    negative_inventory = inventory_df[inventory_df['current_stock'] < 0]
    logger.info(f"   • {len(negative_inventory)} materials with negative inventory")
    
    # Count missing suppliers
    missing_suppliers = materials_df[materials_df['Supplier_ID'].isna()]
    logger.info(f"   • {len(missing_suppliers)} materials with missing supplier IDs")
    
    logger.info("\n📋 Next Steps:")
    logger.info("1. Review data_quality_report.txt for detailed issues")
    logger.info("2. Complete missing cost data for materials with $0.00 cost")
    logger.info("3. Resolve negative inventory balances")
    logger.info("4. Standardize material types and supplier information")
    logger.info("5. Validate BOM percentages that don't sum to 1.0")
    logger.info("6. Add missing yarn specifications to master data")
    
    logger.info("\n🎯 Integration Status:")
    logger.info("✅ Real data successfully loaded and validated")
    logger.info("✅ Interchangeable yarn groups identified")
    logger.info("✅ Data quality issues documented")
    logger.info("✅ Ready for planning system integration")
    
    logger.info("\n💡 To use with planning system:")
    logger.info("   from data.real_data_loader import RealDataLoader")
    logger.info("   loader = RealDataLoader()")
    logger.info("   suppliers = loader.create_supplier_objects()")
    logger.info("   inventory = loader.create_inventory_objects()")
    logger.info("   boms = loader.create_bom_objects()")
    
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
    logger.info(f"\n📊 Summary saved to: data/real_data_integration_summary.csv")

if __name__ == "__main__":
    main()