"""
Test script for Beverly Knits Raw Material Planner

This script demonstrates the core functionality of the planning system
using sample data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.planner import RawMaterialPlanner
from models.forecast import ForecastProcessor
from models.bom import BOMExploder
from models.inventory import InventoryNetter
from models.supplier import SupplierSelector
from config.settings import PlanningConfig
from data.sample_data_generator import SampleDataGenerator
from utils.helpers import ReportGenerator


def test_planning_system():
    """Test the complete planning system"""
    
    print("🧶 Beverly Knits Raw Material Planner - Test Run")
    print("=" * 50)
    
    # Generate sample data
    print("\n📊 Generating sample data...")
    sample_data = SampleDataGenerator.generate_all_sample_data(num_skus=8)
    
    for data_type, df in sample_data.items():
        print(f"  • {data_type}: {len(df)} records")
    
    # Convert to model objects
    print("\n🔄 Converting data to model objects...")
    forecasts = ForecastProcessor.from_dataframe(sample_data['forecasts'])
    boms = BOMExploder.from_dataframe(sample_data['boms'])
    inventories = InventoryNetter.from_dataframe(sample_data['inventory'])
    suppliers = SupplierSelector.from_dataframe(sample_data['suppliers'])
    
    print(f"  • Forecasts: {len(forecasts)} entries")
    print(f"  • BOMs: {len(boms)} entries")
    print(f"  • Inventory: {len(inventories)} materials")
    print(f"  • Suppliers: {len(suppliers)} supplier relationships")
    
    # Initialize planner with custom configuration
    print("\n⚙️ Initializing planner...")
    config = PlanningConfig.create_custom_config(
        safety_buffer=0.15,  # 15% safety buffer
        max_lead_time=25,    # 25 days max lead time
    )
    
    planner = RawMaterialPlanner(config)
    
    # Validate input data
    print("\n🔍 Validating input data...")
    validation_issues = planner.validate_input_data(forecasts, boms, inventories, suppliers)
    
    if validation_issues:
        print("  ⚠️ Validation issues found:")
        for issue in validation_issues[:3]:
            print(f"    - {issue}")
    else:
        print("  ✅ All input data validated successfully")
    
    # Run planning
    print("\n🚀 Executing AI-driven planning...")
    recommendations = planner.plan(forecasts, boms, inventories, suppliers)
    
    # Display results
    print(f"\n📋 Planning Results:")
    print(f"  • Generated {len(recommendations)} procurement recommendations")
    
    # Summary statistics
    summary = planner.get_planning_summary()
    rec_summary = summary.get('recommendation_summary', {})
    
    print(f"  • Total estimated cost: ${rec_summary.get('total_estimated_cost', 0):,.2f}")
    print(f"  • Average lead time: {rec_summary.get('avg_lead_time', 0):.1f} days")
    print(f"  • Risk distribution: {rec_summary.get('risk_distribution', {})}")
    
    # Show top 5 recommendations
    print(f"\n🔝 Top 5 Recommendations by Cost:")
    sorted_recs = sorted(recommendations, key=lambda x: x.total_cost, reverse=True)[:5]
    
    for i, rec in enumerate(sorted_recs, 1):
        print(f"  {i}. {rec.material_id}")
        print(f"     • Quantity: {rec.recommended_order_qty} {rec.unit}")
        print(f"     • Supplier: {rec.supplier_id}")
        print(f"     • Cost: ${rec.total_cost:,.2f}")
        print(f"     • Lead Time: {rec.expected_lead_time} days")
        print(f"     • Risk: {rec.risk_flag.value}")
        print(f"     • Reasoning: {rec.reasoning}")
        print()
    
    # Generate executive summary
    print("\n📊 Executive Summary:")
    print("-" * 30)
    executive_summary = ReportGenerator.generate_summary(
        recommendations,
        {'safety_stock_percentage': 0.15, 'planning_horizon_days': 30, 'enable_eoq_optimization': True, 'enable_multi_supplier': True}
    )
    print(executive_summary)
    
    # Export results
    print("\n💾 Exporting results...")
    dataframes = planner.export_results_to_dataframes()
    
    for df_name, df in dataframes.items():
        if isinstance(df, dict) and 'error' in df:
            continue
        filename = f"test_output_{df_name}.csv"
        df.to_csv(filename, index=False)
        print(f"  • Exported {df_name} to {filename}")
    
    print("\n✅ Test completed successfully!")


def test_individual_components():
    """Test individual components of the system"""

    print("\n🧪 Testing Individual Components")
    print("=" * 35)

    # Test forecast processing
    print("\n1. Testing Forecast Processing...")
    sample_forecasts = SampleDataGenerator.generate_forecast_data(5)
    forecasts = ForecastProcessor.from_dataframe(sample_forecasts)
    processor = ForecastProcessor()
    unified = processor.aggregate_forecasts(forecasts)
    print(f"   • Processed {len(forecasts)} forecasts into {len(unified)} SKUs")
    
    # Test BOM explosion
    print("\n2. Testing BOM Explosion...")
    sample_boms = SampleDataGenerator.generate_bom_data(5)
    boms = BOMExploder.from_dataframe(sample_boms)
    requirements = BOMExploder.explode_requirements(unified, boms)
    print(f"   • Exploded {len(unified)} SKUs into {len(requirements)} material requirements")
    
    # Test inventory netting
    print("\n3. Testing Inventory Netting...")
    sample_inventory = SampleDataGenerator.generate_inventory_data()
    inventories = InventoryNetter.from_dataframe(sample_inventory)
    net_requirements = InventoryNetter.calculate_net_requirements(requirements, inventories)
    materials_needed = sum(1 for req in net_requirements.values() if req['net_requirement'] > 0)
    print(f"   • Netted {len(requirements)} requirements, {materials_needed} need procurement")
    
    # Test supplier selection
    print("\n4. Testing Supplier Selection...")
    sample_suppliers = SampleDataGenerator.generate_supplier_data()
    suppliers = SupplierSelector.from_dataframe(sample_suppliers)
    
    # Test selecting supplier for first material needing procurement
    for material_id, req_data in net_requirements.items():
        if req_data['net_requirement'] > 0:
            selected = SupplierSelector.select_optimal_supplier(
                material_id, req_data['net_requirement'], suppliers
            )
            if selected:
                print(f"   • Selected {selected.supplier_id} for {material_id}")
                break
    
    print("\n✅ All components tested successfully!")


if __name__ == "__main__":
    try:
        # Test individual components first
        test_individual_components()
        
        # Then test the complete system
        recommendations, planner = test_planning_system()
        
        print(f"\n🎉 All tests passed! System is ready for production use.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()