"""
Master Integration Orchestrator
Coordinates all integration points for the Beverly Knits Raw Material Planner
"""

import logging
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd

from engine.sales_planning_integration import (
    SalesPlanningIntegration,
    SalesPlanningIntegrationError
)
from integrations.suppliers.supplier_integration import (
    SupplierIntegration,
    SupplierIntegrationError
)
from integrations.inventory_integration import (
    InventoryIntegration,
    InventoryIntegrationError
)
from config.settings import PlanningConfig

logger = logging.getLogger(__name__)

class IntegrationOrchestrator:
    """Master orchestrator for all system integrations"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the integration orchestrator"""
        self.config = config or PlanningConfig.get_default_config()
        self.output_dir = Path('output/master_integration')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize integration modules
        self.sales_integration = None
        self.supplier_integration = None
        self.inventory_integration = None
        
        # Track integration status
        self.integration_status = {
            'sales': {'status': 'pending', 'errors': [], 'warnings': []},
            'supplier': {'status': 'pending', 'errors': [], 'warnings': []},
            'inventory': {'status': 'pending', 'errors': [], 'warnings': []},
            'planning': {'status': 'pending', 'errors': [], 'warnings': []}
        }
        
        # Store integration results
        self.integration_results = {}
        
    def initialize_integrations(self) -> bool:
        """
        Initialize all integration modules
        
        Returns:
            True if all integrations initialized successfully
        """
        logger.info("Initializing integration modules...")
        
        success = True
        
        # Initialize sales integration
        try:
            self.sales_integration = SalesPlanningIntegration(self.config)
            self.integration_status['sales']['status'] = 'initialized'
            logger.info("Sales integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sales integration: {str(e)}")
            self.integration_status['sales']['status'] = 'failed'
            self.integration_status['sales']['errors'].append(str(e))
            success = False
        
        # Initialize supplier integration
        try:
            self.supplier_integration = SupplierIntegration(self.config)
            self.integration_status['supplier']['status'] = 'initialized'
            logger.info("Supplier integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize supplier integration: {str(e)}")
            self.integration_status['supplier']['status'] = 'failed'
            self.integration_status['supplier']['errors'].append(str(e))
            success = False
        
        # Initialize inventory integration
        try:
            self.inventory_integration = InventoryIntegration(self.config)
            self.integration_status['inventory']['status'] = 'initialized'
            logger.info("Inventory integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize inventory integration: {str(e)}")
            self.integration_status['inventory']['status'] = 'failed'
            self.integration_status['inventory']['errors'].append(str(e))
            success = False
        
        return success
    
    def validate_all_integrations(self) -> Dict[str, bool]:
        """
        Validate all integration points
        
        Returns:
            Dictionary with validation results for each integration
        """
        logger.info("Validating all integrations...")
        
        validation_results = {}
        
        # Validate sales integration
        if self.sales_integration:
            try:
                sales_validation = self.sales_integration.validate_integration()
                validation_results['sales'] = sales_validation.get('overall', False)
                
                # Store errors and warnings
                for error in sales_validation.get('errors', []):
                    self.integration_status['sales']['errors'].append(error)
                for warning in sales_validation.get('warnings', []):
                    self.integration_status['sales']['warnings'].append(warning)
                    
            except Exception as e:
                logger.error(f"Sales validation failed: {str(e)}")
                validation_results['sales'] = False
                self.integration_status['sales']['errors'].append(str(e))
        else:
            validation_results['sales'] = False
        
        # Validate supplier data
        if self.supplier_integration:
            try:
                supplier_df = self.supplier_integration.load_supplier_data()
                supplier_validation = self.supplier_integration.validate_supplier_data(supplier_df)
                
                validation_results['supplier'] = len(supplier_validation['errors']) == 0
                
                # Store errors and warnings
                self.integration_status['supplier']['errors'].extend(supplier_validation['errors'])
                self.integration_status['supplier']['warnings'].extend(supplier_validation['warnings'])
                
            except Exception as e:
                logger.error(f"Supplier validation failed: {str(e)}")
                validation_results['supplier'] = False
                self.integration_status['supplier']['errors'].append(str(e))
        else:
            validation_results['supplier'] = False
        
        # Validate inventory data
        if self.inventory_integration:
            try:
                inventory_df = self.inventory_integration.load_inventory_data()
                inventory_validation = self.inventory_integration.validate_inventory_data(inventory_df)
                
                validation_results['inventory'] = len(inventory_validation['errors']) == 0
                
                # Store errors and warnings
                self.integration_status['inventory']['errors'].extend(inventory_validation['errors'])
                self.integration_status['inventory']['warnings'].extend(inventory_validation['warnings'])
                
            except Exception as e:
                logger.error(f"Inventory validation failed: {str(e)}")
                validation_results['inventory'] = False
                self.integration_status['inventory']['errors'].append(str(e))
        else:
            validation_results['inventory'] = False
        
        validation_results['overall'] = all(validation_results.values())
        
        return validation_results
    
    def run_complete_integration(self, 
                               manual_forecasts: Optional[List] = None,
                               customer_orders: Optional[List] = None) -> Dict:
        """
        Run complete integration across all modules
        
        Args:
            manual_forecasts: Optional manual forecasts
            customer_orders: Optional customer orders
            
        Returns:
            Dictionary with complete integration results
        """
        logger.info("Starting complete system integration...")
        
        # Initialize if not already done
        if not all([self.sales_integration, self.supplier_integration, self.inventory_integration]):
            if not self.initialize_integrations():
                logger.error("Failed to initialize integrations")
                return {
                    'status': 'failed',
                    'error': 'Integration initialization failed',
                    'integration_status': self.integration_status
                }
        
        # Validate integrations
        validation_results = self.validate_all_integrations()
        if not validation_results.get('overall', False):
            logger.warning("Some integrations failed validation, proceeding with available data...")
        
        try:
            # Step 1: Load and process supplier data
            logger.info("Step 1: Processing supplier data...")
            supplier_results = self._process_supplier_data()
            
            # Step 2: Load and process inventory data
            logger.info("Step 2: Processing inventory data...")
            inventory_results = self._process_inventory_data()
            
            # Step 3: Run sales-based planning
            logger.info("Step 3: Running sales-based planning...")
            planning_results = self._run_sales_planning(
                manual_forecasts,
                customer_orders,
                supplier_results.get('supplier_df'),
                inventory_results.get('inventory_df')
            )
            
            # Step 4: Optimize procurement based on all data
            logger.info("Step 4: Optimizing procurement...")
            optimization_results = self._optimize_procurement(
                planning_results,
                supplier_results,
                inventory_results
            )
            
            # Step 5: Generate comprehensive reports
            logger.info("Step 5: Generating reports...")
            reports = self._generate_comprehensive_reports(
                planning_results,
                supplier_results,
                inventory_results,
                optimization_results
            )
            
            # Compile final results
            self.integration_results = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'validation_results': validation_results,
                'planning_results': planning_results,
                'supplier_results': supplier_results,
                'inventory_results': inventory_results,
                'optimization_results': optimization_results,
                'reports': reports,
                'integration_status': self.integration_status
            }
            
            # Save results
            self._save_integration_results()
            
            logger.info("Complete integration finished successfully")
            
            return self.integration_results
            
        except Exception as e:
            logger.error(f"Integration failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'integration_status': self.integration_status
            }
    
    def _process_supplier_data(self) -> Dict:
        """Process supplier data with error handling"""
        try:
            # Load supplier data
            supplier_df = self.supplier_integration.load_supplier_data()
            
            # Enrich supplier data
            supplier_df = self.supplier_integration.enrich_supplier_data(supplier_df)
            
            # Validate supplier data
            validation = self.supplier_integration.validate_supplier_data(supplier_df)
            
            self.integration_status['supplier']['status'] = 'completed'
            
            return {
                'supplier_df': supplier_df,
                'validation': validation,
                'supplier_count': len(supplier_df),
                'tier_distribution': supplier_df['tier'].value_counts().to_dict() if 'tier' in supplier_df.columns else {}
            }
            
        except Exception as e:
            logger.error(f"Supplier processing failed: {str(e)}")
            self.integration_status['supplier']['status'] = 'failed'
            self.integration_status['supplier']['errors'].append(str(e))
            return {'error': str(e), 'supplier_df': pd.DataFrame()}
    
    def _process_inventory_data(self) -> Dict:
        """Process inventory data with error handling"""
        try:
            # Load inventory data
            inventory_df = self.inventory_integration.load_inventory_data()
            
            # Enrich inventory data
            inventory_df = self.inventory_integration.enrich_inventory_data(inventory_df)
            
            # Identify inventory issues
            issues_df = self.inventory_integration.identify_inventory_issues(inventory_df)
            
            # Calculate reorder points
            reorder_df = self.inventory_integration.calculate_reorder_points(inventory_df)
            
            self.integration_status['inventory']['status'] = 'completed'
            
            return {
                'inventory_df': inventory_df,
                'issues_df': issues_df,
                'reorder_df': reorder_df,
                'total_items': len(inventory_df),
                'critical_items': len(issues_df[issues_df['severity'] == 'high']) if not issues_df.empty else 0
            }
            
        except Exception as e:
            logger.error(f"Inventory processing failed: {str(e)}")
            self.integration_status['inventory']['status'] = 'failed'
            self.integration_status['inventory']['errors'].append(str(e))
            return {'error': str(e), 'inventory_df': pd.DataFrame()}
    
    def _run_sales_planning(self, manual_forecasts, customer_orders, 
                          supplier_df, inventory_df) -> Dict:
        """Run sales-based planning with error handling"""
        try:
            # Convert DataFrames to appropriate format if needed
            bom_df = None  # Will be loaded by sales integration
            
            # Run integrated planning
            results = self.sales_integration.run_integrated_planning(
                manual_forecasts=manual_forecasts,
                customer_orders=customer_orders,
                bom_data=bom_df,
                inventory_data=inventory_df,
                supplier_data=supplier_df
            )
            
            if 'error' in results:
                raise SalesPlanningIntegrationError(results['error'])
            
            self.integration_status['planning']['status'] = 'completed'
            
            return results
            
        except Exception as e:
            logger.error(f"Sales planning failed: {str(e)}")
            self.integration_status['planning']['status'] = 'failed'
            self.integration_status['planning']['errors'].append(str(e))
            return {'error': str(e)}
    
    def _optimize_procurement(self, planning_results: Dict, 
                            supplier_results: Dict, 
                            inventory_results: Dict) -> Dict:
        """Optimize procurement based on all available data"""
        try:
            optimization_results = {}
            
            # Get recommendations from planning
            if 'recommendations' in planning_results and isinstance(planning_results['recommendations'], pd.DataFrame):
                recommendations_df = planning_results['recommendations']
                
                # Match suppliers to recommended materials
                if not recommendations_df.empty and 'supplier_df' in supplier_results:
                    matches_df = self.supplier_integration.match_suppliers_to_materials(
                        supplier_results['supplier_df'],
                        recommendations_df
                    )
                    
                    # Optimize supplier selection
                    optimized_df = self.supplier_integration.optimize_supplier_selection(
                        matches_df,
                        constraints={
                            'max_suppliers_per_material': 2,
                            'prefer_tier_a': True
                        }
                    )
                    
                    optimization_results['optimized_suppliers'] = optimized_df
                    optimization_results['total_materials'] = optimized_df['material_id'].nunique()
                    optimization_results['total_suppliers'] = optimized_df['supplier_id'].nunique()
            
            # Consider inventory constraints
            if 'reorder_df' in inventory_results and not inventory_results['reorder_df'].empty:
                optimization_results['urgent_reorders'] = len(
                    inventory_results['reorder_df'][
                        inventory_results['reorder_df']['stock_status'] == 'critical'
                    ]
                )
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Procurement optimization failed: {str(e)}")
            return {'error': str(e)}
    
    def _generate_comprehensive_reports(self, planning_results: Dict,
                                      supplier_results: Dict,
                                      inventory_results: Dict,
                                      optimization_results: Dict) -> Dict:
        """Generate comprehensive reports from all integrations"""
        reports = {}
        
        try:
            # Generate supplier report
            if 'supplier_df' in supplier_results:
                supplier_report = self.supplier_integration.generate_supplier_report(
                    supplier_results['supplier_df'],
                    optimization_results.get('optimized_suppliers')
                )
                reports['supplier_report'] = supplier_report
            
            # Generate inventory report
            if 'inventory_df' in inventory_results:
                inventory_report = self.inventory_integration.generate_inventory_report(
                    inventory_results['inventory_df'],
                    inventory_results.get('issues_df'),
                    inventory_results.get('reorder_df')
                )
                reports['inventory_report'] = inventory_report
            
            # Generate planning analytics
            if 'analytics' in planning_results:
                reports['planning_analytics'] = planning_results['analytics']
            
            # Generate master summary
            reports['master_summary'] = self._generate_master_summary(
                planning_results, supplier_results, inventory_results, optimization_results
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            reports['error'] = str(e)
        
        return reports
    
    def _generate_master_summary(self, planning_results: Dict,
                               supplier_results: Dict,
                               inventory_results: Dict,
                               optimization_results: Dict) -> Dict:
        """Generate master summary of all integrations"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'integration_status': self.integration_status,
            'key_metrics': {}
        }
        
        # Planning metrics
        if 'integration_metadata' in planning_results:
            meta = planning_results['integration_metadata']
            summary['key_metrics']['forecasts_generated'] = meta.get('combined_forecasts_count', 0)
            summary['key_metrics']['recommendations_count'] = meta.get('recommendations_count', 0)
        
        # Supplier metrics
        if 'supplier_count' in supplier_results:
            summary['key_metrics']['active_suppliers'] = supplier_results['supplier_count']
            summary['key_metrics']['supplier_tiers'] = supplier_results.get('tier_distribution', {})
        
        # Inventory metrics
        if 'total_items' in inventory_results:
            summary['key_metrics']['inventory_items'] = inventory_results['total_items']
            summary['key_metrics']['critical_stock_items'] = inventory_results.get('critical_items', 0)
        
        # Optimization metrics
        if 'total_materials' in optimization_results:
            summary['key_metrics']['materials_optimized'] = optimization_results['total_materials']
            summary['key_metrics']['suppliers_selected'] = optimization_results['total_suppliers']
        
        # Calculate overall health score
        health_score = self._calculate_system_health_score()
        summary['system_health_score'] = health_score
        summary['system_health_status'] = self._get_health_status(health_score)
        
        return summary
    
    def _calculate_system_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Deduct points for errors and warnings
        for integration, status in self.integration_status.items():
            error_count = len(status.get('errors', []))
            warning_count = len(status.get('warnings', []))
            
            # Deduct 10 points per error, 2 points per warning
            score -= (error_count * 10 + warning_count * 2)
            
            # Additional deduction for failed status
            if status.get('status') == 'failed':
                score -= 20
        
        return max(0, min(100, score))
    
    def _get_health_status(self, score: float) -> str:
        """Get health status based on score"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'critical'
    
    def _save_integration_results(self):
        """Save integration results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main results
        results_file = self.output_dir / f'integration_results_{timestamp}.json'
        with open(results_file, 'w') as f:
            # Convert DataFrames to dict for JSON serialization
            serializable_results = self._make_serializable(self.integration_results)
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Integration results saved to {results_file}")
        
        # Save specific reports
        if 'reports' in self.integration_results:
            reports_dir = self.output_dir / f'reports_{timestamp}'
            reports_dir.mkdir(exist_ok=True)
            
            for report_name, report_data in self.integration_results['reports'].items():
                report_file = reports_dir / f'{report_name}.json'
                with open(report_file, 'w') as f:
                    json.dump(report_data, f, indent=2)
        
        # Save master summary as markdown
        if 'reports' in self.integration_results and 'master_summary' in self.integration_results['reports']:
            self._save_master_summary_markdown(
                self.integration_results['reports']['master_summary'],
                timestamp
            )
    
    def _make_serializable(self, obj):
        """Convert non-serializable objects for JSON"""
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj
    
    def _save_master_summary_markdown(self, summary: Dict, timestamp: str):
        """Save master summary as markdown report"""
        report_lines = [
            "# Beverly Knits Master Integration Report",
            f"\nGenerated: {summary.get('timestamp', timestamp)}",
            f"\nSystem Health Score: **{summary.get('system_health_score', 0):.1f}/100** ({summary.get('system_health_status', 'unknown')})",
            "\n## Integration Status\n"
        ]
        
        # Add integration status
        for integration, status in summary.get('integration_status', {}).items():
            status_emoji = "✅" if status['status'] == 'completed' else "❌"
            report_lines.append(f"- **{integration.title()}**: {status_emoji} {status['status']}")
            
            if status['errors']:
                report_lines.append(f"  - Errors: {len(status['errors'])}")
            if status['warnings']:
                report_lines.append(f"  - Warnings: {len(status['warnings'])}")
        
        # Add key metrics
        report_lines.append("\n## Key Metrics\n")
        
        metrics = summary.get('key_metrics', {})
        if metrics:
            report_lines.extend([
                f"- **Forecasts Generated**: {metrics.get('forecasts_generated', 0)}",
                f"- **Recommendations**: {metrics.get('recommendations_count', 0)}",
                f"- **Active Suppliers**: {metrics.get('active_suppliers', 0)}",
                f"- **Inventory Items**: {metrics.get('inventory_items', 0)}",
                f"- **Critical Stock Items**: {metrics.get('critical_stock_items', 0)}",
                f"- **Materials Optimized**: {metrics.get('materials_optimized', 0)}"
            ])
        
        # Save report
        report_file = self.output_dir / f'master_summary_{timestamp}.md'
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Master summary saved to {report_file}")

def run_master_integration():
    """Convenience function to run the complete integration"""
    orchestrator = IntegrationOrchestrator()
    return orchestrator.run_complete_integration()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the integration
    results = run_master_integration()
    
    if results['status'] == 'success':
        logger.info("Master integration completed successfully!")
    else:
        logger.error(f"Master integration failed: {results.get('error', 'Unknown error')}")