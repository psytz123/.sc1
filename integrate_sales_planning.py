#!/usr/bin/env python3
"""
Complete Sales Integration for Beverly Knits Raw Material Planner
This script integrates sales-based forecasting with the existing planning system
"""

import logging
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.settings import PlanningConfig
from data.enhanced_real_data_loader import EnhancedRealDataLoader
from engine.sales_planning_integration import (
    SalesPlanningIntegration, 
    SalesPlanningIntegrationError,
    DataValidationError,
    ForecastGenerationError,
    PlanningExecutionError
)

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

class IntegrationRunner:
    """Handles the complete sales integration process with error recovery"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.output_dir = Path('output/sales_integration')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def log_error(self, stage: str, error: Exception):
        """Log error with context"""
        error_msg = f"[{stage}] {type(error).__name__}: {str(error)}"
        logger.error(error_msg)
        self.errors.append({
            'stage': stage,
            'error_type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        })
        
    def log_warning(self, message: str):
        """Log warning"""
        logger.warning(message)
        self.warnings.append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
    def save_error_report(self):
        """Save detailed error report"""
        error_report = {
            'run_timestamp': datetime.now().isoformat(),
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
        
        error_file = self.output_dir / f'error_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(error_file, 'w') as f:
            json.dump(error_report, f, indent=2)
        
        logger.info(f"Error report saved to {error_file}")
        
    def fix_bom_data(self) -> dict:
        """Fix BOM data issues with error handling"""
        try:
            logger.info("Step 1: Fixing BOM data issues...")
            from fix_bom_integration import create_corrected_bom_file
            bom_report = create_corrected_bom_file()
            logger.info(f"BOM correction complete: {bom_report}")
            return bom_report
        except ImportError:
            self.log_warning("BOM fix module not found, proceeding with existing BOM data")
            return {'status': 'skipped', 'message': 'BOM fix module not available'}
        except Exception as e:
            self.log_error("BOM_FIX", e)
            return {'status': 'failed', 'error': str(e)}
            
    def load_configuration(self) -> dict:
        """Load configuration with error handling"""
        try:
            logger.info("Step 2: Loading configuration...")
            config = PlanningConfig.get_default_config()
            config['enable_sales_forecasts'] = True
            
            # Add error handling configuration
            config['error_handling'] = {
                'continue_on_warning': True,
                'max_retries': 3,
                'retry_delay': 5
            }
            
            return config
        except Exception as e:
            self.log_error("CONFIG_LOAD", e)
            # Return minimal default config
            return {
                'enable_sales_forecasts': True,
                'planning_horizon_days': 90,
                'lookback_days': 90
            }
            
    def initialize_integration(self, config: dict) -> SalesPlanningIntegration:
        """Initialize integration with error handling"""
        try:
            logger.info("Step 3: Initializing sales planning integration...")
            return SalesPlanningIntegration(config)
        except SalesPlanningIntegrationError as e:
            self.log_error("INTEGRATION_INIT", e)
            raise
        except Exception as e:
            self.log_error("INTEGRATION_INIT", e)
            raise SalesPlanningIntegrationError(f"Failed to initialize integration: {str(e)}")
            
    def validate_integration(self, integration: SalesPlanningIntegration) -> bool:
        """Validate integration with detailed error reporting"""
        try:
            logger.info("Step 4: Validating integration...")
            validation = integration.validate_integration()
            
            # Log errors and warnings from validation
            for error in validation.get('errors', []):
                self.log_error("VALIDATION", Exception(error))
                
            for warning in validation.get('warnings', []):
                self.log_warning(warning)
                
            if not validation.get('overall', False):
                logger.error("Integration validation failed")
                return False
                
            logger.info("Integration validation passed")
            return True
            
        except Exception as e:
            self.log_error("VALIDATION", e)
            return False
            
    def load_data(self) -> tuple:
        """Load all required data with error handling"""
        logger.info("Step 5: Loading planning data...")
        
        data_loader = None
        bom_df = None
        inventory_df = None
        supplier_df = None
        
        try:
            data_loader = EnhancedRealDataLoader()
        except Exception as e:
            self.log_error("DATA_LOADER_INIT", e)
            logger.error("Failed to initialize data loader, using direct file loading")
        
        # Load BOM data
        try:
            if Path('data/corrected_bom.csv').exists():
                bom_df = pd.read_csv('data/corrected_bom.csv')
                logger.info(f"Loaded corrected BOM data: {len(bom_df)} entries")
            elif data_loader:
                bom_df = data_loader.load_bom()
                logger.info(f"Loaded BOM data via loader: {len(bom_df)} entries")
            else:
                # Try to load any available BOM file
                bom_files = ['data/integrated_boms_v3_corrected.csv', 
                           'data/integrated_boms_v2.csv',
                           'data/integrated_boms.csv']
                for bom_file in bom_files:
                    if Path(bom_file).exists():
                        bom_df = pd.read_csv(bom_file)
                        logger.info(f"Loaded BOM data from {bom_file}: {len(bom_df)} entries")
                        break
        except Exception as e:
            self.log_error("BOM_LOAD", e)
            self.log_warning("Proceeding without BOM data")
        
        # Load inventory data
        try:
            if data_loader:
                inventory_df = data_loader.load_inventory()
                logger.info(f"Loaded inventory data: {len(inventory_df)} items")
            else:
                # Try direct file loading
                inv_files = ['data/integrated_inventory_v2.csv',
                           'data/integrated_inventory.csv']
                for inv_file in inv_files:
                    if Path(inv_file).exists():
                        inventory_df = pd.read_csv(inv_file)
                        logger.info(f"Loaded inventory from {inv_file}: {len(inventory_df)} items")
                        break
        except Exception as e:
            self.log_error("INVENTORY_LOAD", e)
            self.log_warning("Proceeding without inventory data")
        
        # Load supplier data
        try:
            if data_loader:
                supplier_df = data_loader.load_suppliers()
                logger.info(f"Loaded supplier data: {len(supplier_df)} suppliers")
            else:
                # Try direct file loading
                supplier_files = ['data/suppliers.csv',
                                'data/supplier_data.csv',
                                'integrations/suppliers/supplier_list.csv']
                for sup_file in supplier_files:
                    if Path(sup_file).exists():
                        supplier_df = pd.read_csv(sup_file)
                        logger.info(f"Loaded suppliers from {sup_file}: {len(supplier_df)} suppliers")
                        break
        except Exception as e:
            self.log_error("SUPPLIER_LOAD", e)
            self.log_warning("Proceeding without supplier data")
        
        return bom_df, inventory_df, supplier_df
        
    def run_integrated_planning(self, integration: SalesPlanningIntegration, 
                              bom_df: pd.DataFrame, inventory_df: pd.DataFrame, 
                              supplier_df: pd.DataFrame) -> dict:
        """Run integrated planning with comprehensive error handling"""
        try:
            logger.info("Step 6: Running integrated planning with sales forecasts...")
            
            # Load customer orders if available
            customer_orders = []
            try:
                if Path('data/eFab_SO_List.csv').exists():
                    orders_df = pd.read_csv('data/eFab_SO_List.csv')
                    logger.info(f"Loaded {len(orders_df)} customer orders")
                    # Convert to forecast format if needed
                    # customer_orders = convert_orders_to_forecasts(orders_df)
            except Exception as e:
                self.log_warning(f"Failed to load customer orders: {str(e)}")
            
            results = integration.run_integrated_planning(
                manual_forecasts=[],
                customer_orders=customer_orders,
                bom_data=bom_df,
                inventory_data=inventory_df,
                supplier_data=supplier_df
            )
            
            # Check for errors in results
            if 'error' in results:
                raise PlanningExecutionError(results['error'])
                
            # Log any errors/warnings from the integration
            if 'integration_metadata' in results:
                meta = results['integration_metadata']
                for error in meta.get('errors', []):
                    self.errors.append({
                        'stage': 'PLANNING_EXECUTION',
                        'error_type': 'IntegrationError',
                        'message': error,
                        'timestamp': datetime.now().isoformat()
                    })
                for warning in meta.get('warnings', []):
                    self.log_warning(warning)
                    
            return results
            
        except (DataValidationError, ForecastGenerationError, PlanningExecutionError) as e:
            self.log_error("PLANNING_EXECUTION", e)
            raise
        except Exception as e:
            self.log_error("PLANNING_EXECUTION", e)
            raise PlanningExecutionError(f"Unexpected error during planning: {str(e)}")
            
    def save_results(self, results: dict):
        """Save results with error handling"""
        logger.info("Step 7: Saving results...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save unified forecasts
        try:
            if 'unified_forecasts' in results and isinstance(results['unified_forecasts'], pd.DataFrame):
                if not results['unified_forecasts'].empty:
                    file_path = self.output_dir / f'unified_forecasts_{timestamp}.csv'
                    results['unified_forecasts'].to_csv(file_path, index=False)
                    logger.info(f"Saved unified forecasts to {file_path}")
                else:
                    self.log_warning("No unified forecasts to save")
        except Exception as e:
            self.log_error("SAVE_FORECASTS", e)
        
        # Save recommendations
        try:
            if 'recommendations' in results and isinstance(results['recommendations'], pd.DataFrame):
                if not results['recommendations'].empty:
                    file_path = self.output_dir / f'recommendations_{timestamp}.csv'
                    results['recommendations'].to_csv(file_path, index=False)
                    logger.info(f"Saved recommendations to {file_path}")
                else:
                    self.log_warning("No recommendations to save")
        except Exception as e:
            self.log_error("SAVE_RECOMMENDATIONS", e)
        
        # Save integration metadata
        try:
            if 'integration_metadata' in results:
                file_path = self.output_dir / 'integration_metadata.json'
                with open(file_path, 'w') as f:
                    json.dump(results['integration_metadata'], f, indent=2)
                logger.info(f"Saved integration metadata to {file_path}")
        except Exception as e:
            self.log_error("SAVE_METADATA", e)
        
        # Save analytics
        try:
            if 'analytics' in results:
                file_path = self.output_dir / f'analytics_{timestamp}.json'
                with open(file_path, 'w') as f:
                    json.dump(results['analytics'], f, indent=2)
                logger.info(f"Saved analytics to {file_path}")
        except Exception as e:
            self.log_error("SAVE_ANALYTICS", e)
            
    def generate_summary_report(self, results: dict):
        """Generate summary report with error handling"""
        try:
            logger.info("Step 8: Generating summary report...")
            
            report_lines = [
                "# Beverly Knits Sales Integration Report",
                f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "\n## Integration Summary\n"
            ]
            
            # Add error summary if any
            if self.errors:
                report_lines.extend([
                    f"\n## ⚠️ Errors Encountered: {len(self.errors)}\n"
                ])
                for error in self.errors[:5]:  # Show first 5 errors
                    report_lines.append(f"- [{error['stage']}] {error['message']}")
                if len(self.errors) > 5:
                    report_lines.append(f"- ... and {len(self.errors) - 5} more errors")
                report_lines.append("")
            
            # Add warning summary if any
            if self.warnings:
                report_lines.extend([
                    f"\n## ⚠️ Warnings: {len(self.warnings)}\n"
                ])
                for warning in self.warnings[:5]:  # Show first 5 warnings
                    report_lines.append(f"- {warning['message']}")
                if len(self.warnings) > 5:
                    report_lines.append(f"- ... and {len(self.warnings) - 5} more warnings")
                report_lines.append("")
            
            # Add integration metadata
            if 'integration_metadata' in results:
                meta = results['integration_metadata']
                report_lines.extend([
                    "\n## Integration Statistics\n",
                    f"- Status: {meta.get('status', 'unknown')}",
                    f"- Sales Forecasts Generated: {meta.get('sales_forecasts_count', 0)}",
                    f"- Manual Forecasts: {meta.get('manual_forecasts_count', 0)}",
                    f"- Customer Orders: {meta.get('customer_orders_count', 0)}",
                    f"- Combined Forecasts: {meta.get('combined_forecasts_count', 0)}",
                    f"- Recommendations Generated: {meta.get('recommendations_count', 0)}",
                    ""
                ])
            
            # Add forecast summary
            if 'unified_forecasts' in results and isinstance(results['unified_forecasts'], pd.DataFrame):
                df = results['unified_forecasts']
                if not df.empty:
                    report_lines.extend([
                        "\n## Forecast Summary\n",
                        f"- Total SKUs Forecasted: {df['sku'].nunique()}",
                        f"- Total Forecast Quantity: {df['quantity'].sum():,.0f} {df['unit'].iloc[0] if len(df) > 0 else ''}",
                        f"- Average Confidence: {df['confidence'].mean():.2%}",
                        ""
                    ])
            
            # Add recommendation summary
            if 'recommendations' in results and isinstance(results['recommendations'], pd.DataFrame):
                df = results['recommendations']
                if not df.empty:
                    report_lines.extend([
                        "\n## Procurement Recommendations\n",
                        f"- Total Materials: {df['material_id'].nunique() if 'material_id' in df.columns else 0}",
                        f"- Total Suppliers: {df['supplier_id'].nunique() if 'supplier_id' in df.columns else 0}",
                        f"- Total Order Value: ${df['total_cost'].sum():,.2f}" if 'total_cost' in df.columns else "N/A",
                        f"- High Risk Orders: {len(df[df['risk_level'] == 'high']) if 'risk_level' in df.columns else 0}",
                        ""
                    ])
            
            # Add analytics summary
            if 'analytics' in results:
                analytics = results['analytics']
                if 'forecast_summary' in analytics:
                    fs = analytics['forecast_summary']
                    report_lines.extend([
                        "\n## Analytics Summary\n",
                        f"- Total Forecast Value: {fs.get('total_forecast_quantity', 0):,.0f}",
                        f"- Average Confidence: {fs.get('avg_confidence', 0):.2%}",
                        ""
                    ])
            
            # Write report
            report_path = self.output_dir / 'integration_summary.md'
            with open(report_path, 'w') as f:
                f.write('\n'.join(report_lines))
            
            logger.info(f"Summary report saved to {report_path}")
            
        except Exception as e:
            self.log_error("REPORT_GENERATION", e)

def main():
    """Run the complete sales integration with comprehensive error handling"""
    runner = IntegrationRunner()
    
    logger.info("Starting Beverly Knits Sales Integration...")
    logger.info("=" * 60)
    
    integration = None
    results = {}
    
    try:
        # Step 1: Fix BOM data
        bom_fix_result = runner.fix_bom_data()
        
        # Step 2: Load configuration
        config = runner.load_configuration()
        
        # Step 3: Initialize integration
        integration = runner.initialize_integration(config)
        
        # Step 4: Validate integration
        if not runner.validate_integration(integration):
            logger.warning("Integration validation failed, but continuing...")
        
        # Step 5: Load data
        bom_df, inventory_df, supplier_df = runner.load_data()
        
        # Step 6: Run integrated planning
        results = runner.run_integrated_planning(integration, bom_df, inventory_df, supplier_df)
        
        # Step 7: Save results
        runner.save_results(results)
        
        # Step 8: Generate summary report
        runner.generate_summary_report(results)
        
        logger.info("=" * 60)
        logger.info("Sales integration completed successfully!")
        
        if runner.errors:
            logger.warning(f"Completed with {len(runner.errors)} errors")
        if runner.warnings:
            logger.info(f"Completed with {len(runner.warnings)} warnings")
            
    except SalesPlanningIntegrationError as e:
        logger.error(f"Integration failed: {str(e)}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        runner.log_error("MAIN", e)
    finally:
        # Always save error report
        if runner.errors or runner.warnings:
            runner.save_error_report()
        
        # Generate partial report if we have any results
        if results:
            try:
                runner.generate_summary_report(results)
            except:
                pass

if __name__ == "__main__":
    main()