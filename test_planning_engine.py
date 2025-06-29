"""
Test script to verify the planning engine functionality
"""

import pandas as pd
from datetime import datetime, timedelta
from engine.planner import RawMaterialPlanner
from data.sample_data_generator import SampleDataGenerator
from config.settings import PlanningConfig
from models.forecast import FinishedGoodsForecast
from models.bom import BillOfMaterials
from models.inventory import Inventory
from models.supplier import Supplier

def test_planning_engine():
    """Test the planning engine with sample data"""
    
    print("🧪 Testing Beverly Knits Planning Engine\n")
    
    # 1. Generate sample data
    print("1️⃣ Generating sample data...")
    data = SampleDataGenerator.generate_all_sample_data(num_skus=10)
    print(f"   ✓ Generated {len(data['forecasts'])} forecasts")
    print(f"   ✓ Generated {len(data['boms'])} BOM records")
    print(f"   ✓ Generated {len(data['inventory'])} inventory records")
    print(f"   ✓ Generated {len(data['suppliers'])} supplier records\n")
    
    # 2. Convert DataFrames to model objects
    print("2️⃣ Converting data to model objects...")
    
    # Convert forecasts
    forecasts = []
    for _, row in data['forecasts'].iterrows():
        forecast = FinishedGoodsForecast(
            sku_id=row['sku_id'],
            forecast_qty=row['forecast_qty'],
            forecast_date=row['forecast_date'],
            source=row['source']
        )
        forecasts.append(forecast)
    
    # Convert BOMs
    boms = []
    for _, row in data['boms'].iterrows():
        bom = BillOfMaterials(
            sku_id=row['sku_id'],
            material_id=row['material_id'],
            qty_per_unit=row['qty_per_unit'],
            unit=row['unit']
        )
        boms.append(bom)
    
    # Convert inventory
    inventory_list = []
    for _, row in data['inventory'].iterrows():
        inv = Inventory(
            material_id=row['material_id'],
            on_hand_qty=row['on_hand_qty'],
            unit=row['unit'],
            open_po_qty=row.get('open_po_qty', 0.0),
            po_expected_date=row.get('po_expected_date', None)
        )
        inventory_list.append(inv)
    
    # Convert suppliers
    suppliers = []
    for _, row in data['suppliers'].iterrows():
        supplier = Supplier(
            material_id=row['material_id'],
            supplier_id=row['supplier_id'],
            cost_per_unit=row['cost_per_unit'],
            lead_time_days=row['lead_time_days'],
            moq=row['moq'],
            contract_qty_limit=row.get('contract_qty_limit', None),
            reliability_score=row['reliability_score'],
            ordering_cost=row.get('ordering_cost', 100.0),
            holding_cost_rate=row.get('holding_cost_rate', 0.2)
        )
        suppliers.append(supplier)
    
    print("   ✓ Data conversion completed\n")
    
    # 3. Initialize planning engine with config
    print("3️⃣ Initializing planning engine...")
    config = PlanningConfig()
    planner = RawMaterialPlanner(config)
    print("   ✓ Planning engine initialized\n")
    
    # 4. Run planning process
    print("4️⃣ Running planning process...")
    try:
        recommendations = planner.plan(
            forecasts=forecasts,
            boms=boms,
            inventory=inventory_list,
            suppliers=suppliers
        )
        print(f"   ✓ Generated {len(recommendations)} recommendations\n")
        
        # 5. Display sample recommendations
        if recommendations:
            print("5️⃣ Sample Recommendations:")
            print("-" * 80)
            
            for i, rec in enumerate(recommendations[:3]):  # Show first 3 recommendations
                print(f"\nRecommendation #{i+1}:")
                print(f"  Material: {rec.material_id}")
                print(f"  Quantity: {rec.quantity:,.2f} {rec.unit}")
                print(f"  Supplier: {rec.supplier_id}")
                print(f"  Lead Time: {rec.lead_time} days")
                print(f"  Total Cost: ${rec.total_cost:,.2f}")
                print(f"  Order Date: {rec.order_date}")
                print(f"  Delivery Date: {rec.delivery_date}")
                print(f"  Reasoning: {rec.reasoning}")
            
            print("\n" + "-" * 80)
            print(f"\n✅ Planning engine test completed successfully!")
            print(f"   Total recommendations: {len(recommendations)}")
            print(f"   Total cost: ${sum(r.total_cost for r in recommendations):,.2f}")
        else:
            print("\n⚠️  No recommendations generated - this might be normal if inventory is sufficient")
            print("✅ Planning engine test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during planning: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_planning_engine()