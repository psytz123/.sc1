"""
Command-line interface for running the raw material planner
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from engine.planner import RawMaterialPlanner
from config.settings import PlanningConfig
from models.forecast import ForecastProcessor
from models.bom import BillOfMaterials
from models.inventory import Inventory
from models.supplier import Supplier
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__, level="DEBUG")

def main():
    """Run the planning engine from command line"""
    logger.info("="*60)
    logger.info("BEVERLY KNITS RAW MATERIAL PLANNER")
    logger.info("="*60)
    
    # Load configuration
    config = PlanningConfig()
    logger.info(f"\nConfiguration loaded:")
    logger.info(f"  - Sales forecasting enabled: {config.enable_sales_forecasting}")
    logger.info(f"  - Planning horizon: {config.planning_horizon_days} days")
    logger.info(f"  - Safety stock method: {config.safety_stock_method}")
    
    # Initialize components
    logger.info("\nInitializing components...")
    forecast_processor = ForecastProcessor()

    # Load data
    logger.info("\nLoading data...")

    # Load forecasts
    forecast_df = pd.read_csv('data/real_data_sample_forecasts.csv')
    # Rename column to match expected format
    forecast_df['forecast_qty'] = forecast_df['quantity']
    # Map source values to valid ones
    forecast_df['source'] = forecast_df['source'].replace('Historical', 'sales_history')
    forecasts = ForecastProcessor.from_dataframe(forecast_df)

    # Load BOM
    bom_df = pd.read_csv('data/integrated_boms_v3_corrected.csv')
    bom_entries = []
    for _, row in bom_df.iterrows():
        bom = BillOfMaterials(
            sku_id=str(row['sku_id']),  # Convert to string
            material_id=str(row['material_id']),  # Convert to string
            qty_per_unit=row['quantity_per_unit'],
            unit=row.get('unit', 'kg')  # Default to kg if not specified
        )
        bom_entries.append(bom)

    # Load inventory
    inventory_df = pd.read_csv('data/integrated_inventory_v2.csv')
    inventory = []
    for _, row in inventory_df.iterrows():
        inv = Inventory(
            material_id=str(row['material_id']),  # Convert to string
            on_hand_qty=row['current_stock'],  # Use current_stock as on_hand_qty
            unit='kg',  # Default unit
            open_po_qty=row.get('incoming_stock', 0.0)  # Use incoming_stock as open PO
        )
        inventory.append(inv)

    # Load suppliers
    logger.info("Loading suppliers...")
    supplier_df = pd.read_csv('data/integrated_suppliers_v3_complete.csv')
    supplier_df = pd.read_csv('data/integrated_suppliers_v2.csv')
    suppliers = []
    for _, row in supplier_df.iterrows():
        supplier = Supplier(
            supplier_id=str(row['supplier_id']),  # Convert to string
            material_id=str(row['material_id']),  # Convert to string
            cost_per_unit=row['cost_per_unit'],  # Use correct parameter name
            lead_time_days=row['lead_time_days'],
            moq=row.get('moq', 0),
            reliability_score=row.get('reliability_score', 0.95)
        )
        suppliers.append(supplier)

    logger.info(f"  - Loaded {len(forecasts)} forecasts")
    logger.info(f"  - Loaded {len(bom_entries)} BOM entries")
    logger.info(f"  - Loaded {len(inventory)} inventory items")
    logger.info(f"  - Loaded {len(suppliers)} suppliers")

    # Initialize planner
    planner = RawMaterialPlanner(config)

    # Run planning
    logger.info("\n" + "="*60)
    logger.info("RUNNING PLANNING ENGINE")
    logger.info("="*60)

    recommendations = planner.plan(
        forecasts=forecasts,
        boms=bom_entries,
        inventory=inventory,
        suppliers=suppliers
    )

    # Display results
    logger.info("\n" + "="*60)
    logger.info("PLANNING RESULTS")
    logger.info("="*60)

    if recommendations:
        logger.info(f"\nGenerated {len(recommendations)} procurement recommendations:")

        total_cost = 0
        for i, rec in enumerate(recommendations[:10]):  # Show first 10
            logger.info(f"\n{i+1}. {rec.material_id}")
            logger.info(f"   Quantity: {rec.quantity:,.0f} {rec.unit}")
            logger.info(f"   Supplier: {rec.supplier_id}")
            logger.info(f"   Unit Price: ${rec.unit_price:.2f}")
            logger.info(f"   Total Cost: ${rec.total_cost:,.2f}")
            logger.info(f"   Lead Time: {rec.lead_time_days} days")
            logger.info(f"   Order Date: {rec.order_date}")
            logger.info(f"   Delivery Date: {rec.expected_delivery}")
            total_cost += rec.total_cost
        
        if len(recommendations) > 10:
            logger.info(f"\n... and {len(recommendations) - 10} more recommendations")
        
        logger.info(f"\nTotal procurement cost: ${sum(r.total_cost for r in recommendations):,.2f}")
    else:
        logger.info("\nNo procurement recommendations generated.")
        logger.info("This could mean:")
        logger.info("  - Current inventory is sufficient")
        logger.info("  - No forecasts require procurement")
        logger.info("  - Missing BOM or supplier data")

    # Save results
    if recommendations:
        logger.info("\nSaving results...")
        output_file = f"output/procurement_plan_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        pd.DataFrame([r.__dict__ for r in recommendations]).to_csv(output_file, index=False)
        logger.info(f"Results saved to: {output_file}")

    logger.info("\nPlanning complete!")
    logger.info("="*60)

if __name__ == "__main__":
    main()