#!/usr/bin/env python3
"""
Complete Sales Integration for Beverly Knits Raw Material Planner
This script integrates sales-based forecasting with the existing planning system
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.settings import PlanningConfig
from data.enhanced_real_data_loader import EnhancedRealDataLoader
from engine.sales_planning_integration import SalesPlanningIntegration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sales_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the complete sales integration"""
    logger.info("Starting Beverly Knits Sales Integration...")
    
    try:
        # 1. Fix BOM data issues first
        logger.info("Step 1: Fixing BOM data issues...")
        from fix_bom_integration import create_corrected_bom_file
        bom_report = create_corrected_bom_file()
        logger.info(f"BOM correction complete: {bom_report}")
        
        # 2. Load configuration
        logger.info("Step 2: Loading configuration...")
        config = PlanningConfig.get_default_config()
        config['enable_sales_forecasts'] = True
        
        # 3. Initialize integration
        logger.info("Step 3: Initializing sales planning integration...")
        integration = SalesPlanningIntegration(config)
        
        # 4. Validate integration
        logger.info("Step 4: Validating integration...")
        validation = integration.validate_integration()
        
        if validation['errors']:
            logger.error(f"Validation errors: {validation['errors']}")
            return
        
        for warning in validation['warnings']:
            logger.warning(warning)
        
        # 5. Load existing data using enhanced loader
        logger.info("Step 5: Loading existing planning data...")
        data_loader = EnhancedRealDataLoader()
        
        # Load BOM data (use corrected version)
        bom_df = pd.read_csv('data/corrected_bom.csv')
        
        # Load other data
        inventory_df = data_loader.load_inventory()
        supplier_df = data_loader.load_suppliers()
        
        # 6. Run integrated planning
        logger.info("Step 6: Running integrated planning with sales forecasts...")
        results = integration.run_integrated_planning(
            manual_forecasts=[],  # No manual forecasts for this run
            customer_orders=[],   # Could load from eFab_SO_List.csv
            bom_data=bom_df,
            inventory_data=inventory_df,
            supplier_data=supplier_df
        )
        
        if 'error' in results:
            logger.error(f"Planning failed: {results['error']}")
            return
        
        # 7. Save results
        logger.info("Step 7: Saving results...")
        output_dir = Path('output/sales_integration')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save unified forecasts
        if 'unified_forecasts' in results:
            results['unified_forecasts'].to_csv(
                output_dir / f'unified_forecasts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                index=False
            )
        
        # Save recommendations
        if 'recommendations' in results:
            results['recommendations'].to_csv(
                output_dir / f'recommendations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                index=False
            )
        
        # Save integration metadata
        if 'integration_metadata' in results:
            import json
            with open(output_dir / 'integration_metadata.json', 'w') as f:
                json.dump(results['integration_metadata'], f, indent=2)
        
        logger.info("Sales integration completed successfully!")
        
        # 8. Generate summary report
        logger.info("Step 8: Generating summary report...")
        generate_summary_report(results, output_dir)
        
    except Exception as e:
        logger.error(f"Integration failed: {e}", exc_info=True)
        raise

def generate_summary_report(results: dict, output_dir: Path):
    """Generate a summary report of the integration"""
    report_lines = [
        "# Beverly Knits Sales Integration Report",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Integration Summary\n"
    ]
    
    if 'integration_metadata' in results:
        meta = results['integration_metadata']
        report_lines.extend([
            f"- Sales Forecasts Generated: {meta.get('sales_forecasts_count', 0)}",
            f"- Manual Forecasts: {meta.get('manual_forecasts_count', 0)}",
            f"- Customer Orders: {meta.get('customer_orders_count', 0)}",
            f"- Combined Forecasts: {meta.get('combined_forecasts_count', 0)}",
            ""
        ])
    
    if 'unified_forecasts' in results:
        df = results['unified_forecasts']
        report_lines.extend([
            "\n## Forecast Summary\n",
            f"- Total SKUs Forecasted: {df['sku'].nunique()}",
            f"- Total Forecast Quantity: {df['quantity'].sum():,.0f} {df['unit'].iloc[0] if len(df) > 0 else ''}",
            f"- Average Confidence: {df['confidence'].mean():.2%}",
            ""
        ])
    
    if 'recommendations' in results:
        df = results['recommendations']
        report_lines.extend([
            "\n## Procurement Recommendations\n",
            f"- Total Materials: {df['material_id'].nunique()}",
            f"- Total Suppliers: {df['supplier_id'].nunique()}",
            f"- Total Order Value: ${df['total_cost'].sum():,.2f}",
            f"- High Risk Orders: {len(df[df['risk_level'] == 'high'])}",
            ""
        ])
    
    # Write report
    report_path = output_dir / 'integration_summary.md'
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Summary report saved to {report_path}")

if __name__ == "__main__":
    main()