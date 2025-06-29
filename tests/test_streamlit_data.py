"""
Test script to verify data loading and planning engine functionality
"""

import pandas as pd
from data.sample_data_generator import SampleDataGenerator
from engine.planner import RawMaterialPlanner
from models.forecast import FinishedGoodsForecast
from models.bom import BillOfMaterials
from models.inventory import Inventory
from models.supplier import Supplier
from config.settings import PlanningConfig
from datetime import datetime, timedelta

def test_data_loading():
    """Test that sample data can be loaded correctly"""
    print("🧪 Testing Data Loading...")
    
    # Generate sample data
    data = SampleDataGenerator.generate_all_sample_data()
    
    print(f"✓ Generated {len(data['forecasts'])} forecasts")
    print(f"✓ Generated {len(data['boms'])} BOM records")
    print(f"✓ Generated {len(data['inventory'])} inventory records")
    print(f"✓ Generated {len(data['suppliers'])} supplier records")
    
    # Check data structure
    print("\n📊 Data Structure Check:")
    print(f"Forecast columns: {list(data['forecasts'].columns)}")
    print(f"BOM columns: {list(data['boms'].columns)}")
    print(f"Inventory columns: {list(data['inventory'].columns)}")
    print(f"Supplier columns: {list(data['suppliers'].columns)}")
    
    return data

def test_planning_engine():
    """Test that the planning engine can process data"""
    print("\n🧪 Testing Planning Engine...")
    
    # Generate sample data
    data = SampleDataGenerator.generate_all_sample_data()
    
    # Convert to model objects
    forecasts = []
    for _, row in data['forecasts'].iterrows():
        forecasts.append(FinishedGoodsForecast(
            sku_id=row['sku_id'],
            forecast_qty=row['forecast_qty'],
            forecast_date=pd.to_datetime(row['forecast_date']),
            source=row['source'],
            confidence=row.get('confidence', 0.8)
        ))
    
    boms = []
    for _, row in data['boms'].iterrows():
        boms.append(BillOfMaterials(
            sku_id=row['sku_id'],
            material_id=row['material_id'],
            qty_per_unit=row['qty_per_unit'],
            unit=row['unit']
        ))
    
    inventory = []
    for _, row in data['inventory'].iterrows():
        inventory.append(Inventory(
            material_id=row['material_id'],
            on_hand_qty=row['on_hand_qty'],
            unit=row['unit'],
            open_po_qty=row.get('open_po_qty', 0),
            po_expected_date=pd.to_datetime(row['po_expected_date']) if pd.notna(row.get('po_expected_date')) else None
        ))
    
    suppliers = []
    for _, row in data['suppliers'].iterrows():
        suppliers.append(Supplier(
            material_id=row['material_id'],
            supplier_id=row['supplier_id'],
            cost_per_unit=row['cost_per_unit'],
            lead_time_days=row['lead_time_days'],
            moq=row.get('moq', 0),
            reliability_score=row.get('reliability_score', 0.9),
            contract_qty_limit=row.get('contract_qty_limit', None),
            ordering_cost=row.get('ordering_cost', 100),
            holding_cost_rate=row.get('holding_cost_rate', 0.2)
        ))
    
    print(f"✓ Converted {len(forecasts)} forecasts")
    print(f"✓ Converted {len(boms)} BOMs")
    print(f"✓ Converted {len(inventory)} inventory items")
    print(f"✓ Converted {len(suppliers)} suppliers")
    
    # Initialize planner with config
    config = PlanningConfig()
    planner = RawMaterialPlanner(config)
    print("✓ Planning engine initialized")
    
    # Run planning
    try:
        recommendations = planner.plan(
            forecasts=forecasts,
            boms=boms,
            inventory=inventory,
            suppliers=suppliers
        )
        print(f"✓ Planning completed successfully!")
        print(f"✓ Generated {len(recommendations)} recommendations")
        
        # Show sample recommendation
        if recommendations:
            rec = recommendations[0]
            print(f"\n📋 Sample Recommendation:")
            print(f"  Material: {rec.material_id}")
            print(f"  Quantity: {rec.order_quantity}")
            print(f"  Supplier: {rec.supplier_id}")
            print(f"  Total Cost: ${rec.total_cost:,.2f}")
            
    except Exception as e:
        print(f"❌ Planning failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧶 Beverly Knits - Data Loading and Planning Engine Test\n")
    
    # Test data loading
    data = test_data_loading()
    
    # Test planning engine
    test_planning_engine()
    
    print("\n✅ Testing completed!")