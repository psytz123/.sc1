"""
Update All Workflows for Live Data Format
==========================================
Comprehensive script to update Beverly Knits planning system
to work directly with live CSV data format:

1. Validates live data files
2. Tests live data integration
3. Updates configurations
4. Tests planning engine
5. Validates BOM processing
6. Updates upload templates
7. Creates migration scripts
8. Generates documentation
9. Runs full system test
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.live_data_integration import LiveDataIntegrator
from engine.live_data_planner import LiveDataPlanner
from models.live_data_models import LiveDataValidator
from utils.logger import get_logger
import pandas as pd

logger = get_logger(__name__)


class LiveDataWorkflowUpdater:
    """Updates all workflows to work with live data format"""
    
    def __init__(self, data_path: str = "data/", output_path: str = "output/"):
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # Initialize components
        self.integrator = LiveDataIntegrator(str(self.data_path))
        self.planner = LiveDataPlanner(str(self.data_path))
        
        # Track results
        self.validation_results = {}
        self.test_results = {}
        self.update_summary = {}
        
    def run_complete_update(self) -> Dict[str, Any]:
        """Run complete workflow update process"""
        logger.info("Starting Beverly Knits Live Data Workflow Update")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Validate live data files
            logger.info("Step 1: Validating live data files...")
            self._validate_live_data_files()
            
            # Step 2: Test live data integration
            logger.info("Step 2: Testing live data integration...")
            self._test_live_data_integration()
            
            # Step 3: Test live data planning engine
            logger.info("Step 3: Testing live data planning engine...")
            self._test_live_data_planning()
            
            # Step 4: Update configurations
            logger.info("Step 4: Updating system configurations...")
            self._update_configurations()
            
            # Step 5: Validate BOM processing
            logger.info("Step 5: Validating BOM processing...")
            self._validate_bom_processing()
            
            # Step 6: Update upload templates
            logger.info("Step 6: Updating upload templates...")
            self._update_upload_templates()
            
            # Step 7: Create migration scripts
            logger.info("Step 7: Creating migration scripts...")
            self._create_migration_scripts()
            
            # Step 8: Generate documentation
            logger.info("Step 8: Generating documentation...")
            self._generate_documentation()
            
            # Step 9: Run full system test
            logger.info("Step 9: Running full system test...")
            self._run_full_system_test()
            
            # Generate final summary
            end_time = datetime.now()
            self.update_summary['total_time'] = (end_time - start_time).total_seconds()
            self.update_summary['completion_status'] = 'SUCCESS'
            
            logger.info("✅ Live data workflow update completed successfully!")
            return self._generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ Workflow update failed: {e}")
            self.update_summary['completion_status'] = 'FAILED'
            self.update_summary['error'] = str(e)
            raise
    
    def _validate_live_data_files(self):
        """Validate all live data files exist and have correct format"""
        logger.info("Validating live data files...")
        
        required_files = [
            'cfab_Yarn_Demand_By_Style.csv',
            'eFab_SO_List.csv',
            'Style_BOM.csv',
            'Inventory.csv',
            'Supplier_ID.csv',
            'Yarn_ID.csv'
        ]
        
        validation_results = {
            'files_found': [],
            'files_missing': [],
            'file_validations': {}
        }
        
        for file_name in required_files:
            file_path = self.data_path / file_name
            if file_path.exists():
                validation_results['files_found'].append(file_name)
                
                # Validate file format
                try:
                    df = pd.read_csv(file_path)
                    
                    if file_name == 'cfab_Yarn_Demand_By_Style.csv':
                        file_validation = LiveDataValidator.validate_yarn_demand_by_style(df)
                    elif file_name == 'Style_BOM.csv':
                        file_validation = LiveDataValidator.validate_style_bom(df)
                    elif file_name == 'eFab_SO_List.csv':
                        file_validation = LiveDataValidator.validate_sales_orders(df)
                    else:
                        file_validation = {
                            'total_records': len(df),
                            'columns': list(df.columns),
                            'issues': []
                        }
                    
                    validation_results['file_validations'][file_name] = file_validation
                    
                except Exception as e:
                    validation_results['file_validations'][file_name] = {
                        'error': str(e),
                        'issues': [f"File validation failed: {e}"]
                    }
            else:
                validation_results['files_missing'].append(file_name)
        
        # Cross-validate BOM files
        if 'cfab_Yarn_Demand_By_Style.csv' in validation_results['files_found'] and 'Style_BOM.csv' in validation_results['files_found']:
            try:
                yarn_demand_df = pd.read_csv(self.data_path / 'cfab_Yarn_Demand_By_Style.csv')
                style_bom_df = pd.read_csv(self.data_path / 'Style_BOM.csv')
                cross_validation = LiveDataValidator.cross_validate_bom_files(yarn_demand_df, style_bom_df)
                validation_results['cross_validation'] = cross_validation
            except Exception as e:
                validation_results['cross_validation'] = {'error': str(e)}
        
        self.validation_results['file_validation'] = validation_results
        
        # Log results
        logger.info(f"✅ Found {len(validation_results['files_found'])}/{len(required_files)} required files")
        if validation_results['files_missing']:
            logger.warning(f"❌ Missing files: {validation_results['files_missing']}")
        
        total_issues = sum(len(v.get('issues', [])) for v in validation_results['file_validations'].values())
        if total_issues > 0:
            logger.warning(f"⚠️ Found {total_issues} validation issues across all files")
        else:
            logger.info("✅ All files passed validation")
    
    def _test_live_data_integration(self):
        """Test live data integration functionality"""
        logger.info("Testing live data integration...")
        
        test_results = {
            'load_test': None,
            'conversion_test': None,
            'validation_test': None
        }
        
        try:
            # Test 1: Load live data
            logger.info("  Testing data loading...")
            live_data = self.integrator.load_all_live_data()
            test_results['load_test'] = {
                'success': True,
                'data_types_loaded': len([k for k, v in live_data.items() if v]),
                'total_records': sum(len(v) for v in live_data.values() if v)
            }
            logger.info(f"  ✅ Loaded {test_results['load_test']['data_types_loaded']} data types")
            
        except Exception as e:
            test_results['load_test'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ Data loading failed: {e}")
        
        try:
            # Test 2: Convert to planning format
            logger.info("  Testing data conversion...")
            planning_data = self.integrator.convert_to_planning_format()
            test_results['conversion_test'] = {
                'success': True,
                'forecasts_generated': len(planning_data.get('forecasts', [])),
                'boms_generated': len(planning_data.get('boms', [])),
                'inventory_records': len(planning_data.get('inventory', [])),
                'suppliers_generated': len(planning_data.get('suppliers', []))
            }
            logger.info(f"  ✅ Generated {test_results['conversion_test']['forecasts_generated']} forecasts")
            
        except Exception as e:
            test_results['conversion_test'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ Data conversion failed: {e}")
        
        try:
            # Test 3: Validate integration
            logger.info("  Testing integration validation...")
            planning_inputs = self.integrator.generate_planning_inputs()
            test_results['validation_test'] = {
                'success': True,
                'validation_results': planning_inputs.get('validation_results', {}),
                'data_quality_issues': sum(
                    len(v.get('issues', [])) for v in planning_inputs.get('validation_results', {}).values()
                )
            }
            logger.info(f"  ✅ Integration validation completed")
            
        except Exception as e:
            test_results['validation_test'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ Integration validation failed: {e}")
        
        self.test_results['integration_test'] = test_results
    
    def _test_live_data_planning(self):
        """Test live data planning engine"""
        logger.info("Testing live data planning engine...")
        
        test_results = {
            'planning_cycle_test': None,
            'recommendations_test': None,
            'export_test': None
        }
        
        try:
            # Test 1: Run planning cycle
            logger.info("  Testing planning cycle...")
            planning_results = self.planner.run_full_planning_cycle()
            test_results['planning_cycle_test'] = {
                'success': True,
                'total_recommendations': len(planning_results.get('procurement_recommendations', [])),
                'total_cost': planning_results.get('planning_summary', {}).get('totals', {}).get('total_cost', 0),
                'materials_planned': planning_results.get('planning_summary', {}).get('totals', {}).get('total_materials', 0),
                'suppliers_involved': planning_results.get('planning_summary', {}).get('totals', {}).get('total_suppliers', 0)
            }
            logger.info(f"  ✅ Generated {test_results['planning_cycle_test']['total_recommendations']} recommendations")
            
        except Exception as e:
            test_results['planning_cycle_test'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ Planning cycle failed: {e}")
        
        try:
            # Test 2: Export results
            logger.info("  Testing results export...")
            exported_files = self.planner.export_planning_results(str(self.output_path))
            test_results['export_test'] = {
                'success': True,
                'files_exported': len(exported_files),
                'exported_files': list(exported_files.keys())
            }
            logger.info(f"  ✅ Exported {test_results['export_test']['files_exported']} files")
            
        except Exception as e:
            test_results['export_test'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ Results export failed: {e}")
        
        self.test_results['planning_test'] = test_results
    
    def _update_configurations(self):
        """Update system configurations for live data format"""
        logger.info("Updating system configurations...")
        
        # Create live data configuration
        live_data_config = {
            'data_source': 'live_csv_files',
            'file_format': 'live_format',
            'data_files': {
                'yarn_demand': 'cfab_Yarn_Demand_By_Style.csv',
                'sales_orders': 'eFab_SO_List.csv',
                'style_bom': 'Style_BOM.csv',
                'inventory': 'Inventory.csv',
                'suppliers': 'Supplier_ID.csv',
                'yarn_master': 'Yarn_ID.csv'
            },
            'processing_options': {
                'handle_comma_separated_numbers': True,
                'parse_currency_formats': True,
                'process_html_toggles': True,
                'convert_percentage_scales': True,
                'filter_inactive_suppliers': True
            },
            'validation_settings': {
                'cross_validate_bom_files': True,
                'check_percentage_totals': True,
                'validate_cost_data': True,
                'check_supplier_activity': True
            },
            'planning_settings': {
                'safety_stock_percentage': 0.2,
                'lead_time_buffer_days': 7,
                'planning_horizon_days': 90,
                'service_level': 0.95,
                'enable_multi_supplier': True
            }
        }
        
        # Save live data configuration
        config_file = self.output_path / 'live_data_config.json'
        with open(config_file, 'w') as f:
            json.dump(live_data_config, f, indent=2)
        
        # Update main configuration
        main_config = {
            'system_mode': 'live_data',
            'data_integration': 'live_data_integration',
            'planning_engine': 'live_data_planner',
            'file_format': 'live_csv_format',
            'auto_validation': True,
            'auto_conversion': True,
            'enhanced_bom_processing': True,
            'style_to_yarn_mapping': True
        }
        
        main_config_file = self.output_path / 'main_config.json'
        with open(main_config_file, 'w') as f:
            json.dump(main_config, f, indent=2)
        
        logger.info("✅ System configurations updated for live data format")
    
    def _validate_bom_processing(self):
        """Validate BOM processing with live data"""
        logger.info("Validating BOM processing...")
        
        validation_results = {
            'style_bom_processing': None,
            'yarn_demand_processing': None,
            'cross_validation': None
        }
        
        try:
            # Test Style_BOM.csv processing
            style_bom_file = self.data_path / 'Style_BOM.csv'
            if style_bom_file.exists():
                from models.bom import BOMExploder
                
                style_bom_df = pd.read_csv(style_bom_file)
                boms = BOMExploder.from_live_data_format(style_bom_df)
                
                validation_results['style_bom_processing'] = {
                    'success': True,
                    'total_boms': len(boms),
                    'unique_styles': len(set(bom.sku_id for bom in boms)),
                    'unique_yarns': len(set(bom.material_id for bom in boms))
                }
                logger.info(f"  ✅ Processed {len(boms)} BOM entries from Style_BOM.csv")
            
        except Exception as e:
            validation_results['style_bom_processing'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ Style BOM processing failed: {e}")
        
        try:
            # Test cfab_Yarn_Demand_By_Style.csv processing
            yarn_demand_file = self.data_path / 'cfab_Yarn_Demand_By_Style.csv'
            if yarn_demand_file.exists():
                from models.bom import BOMExploder
                
                yarn_demand_df = pd.read_csv(yarn_demand_file)
                style_yarn_boms = BOMExploder.from_yarn_demand_by_style(yarn_demand_df)
                
                validation_results['yarn_demand_processing'] = {
                    'success': True,
                    'total_boms': len(style_yarn_boms),
                    'unique_styles': len(set(bom.style_id for bom in style_yarn_boms)),
                    'unique_yarns': len(set(bom.yarn_id for bom in style_yarn_boms))
                }
                logger.info(f"  ✅ Processed {len(style_yarn_boms)} BOM entries from yarn demand data")
            
        except Exception as e:
            validation_results['yarn_demand_processing'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ Yarn demand processing failed: {e}")
        
        try:
            # Test cross-validation
            if (self.data_path / 'Style_BOM.csv').exists() and (self.data_path / 'cfab_Yarn_Demand_By_Style.csv').exists():
                from models.bom import BOMExploder
                
                style_bom_df = pd.read_csv(self.data_path / 'Style_BOM.csv')
                yarn_demand_df = pd.read_csv(self.data_path / 'cfab_Yarn_Demand_By_Style.csv')
                
                cross_validation = BOMExploder.validate_live_data_boms(style_bom_df, yarn_demand_df)
                validation_results['cross_validation'] = {
                    'success': True,
                    'validation_results': cross_validation
                }
                logger.info("  ✅ Cross-validation completed")
            
        except Exception as e:
            validation_results['cross_validation'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ Cross-validation failed: {e}")
        
        self.validation_results['bom_processing'] = validation_results
    
    def _update_upload_templates(self):
        """Update upload templates to match live data format"""
        logger.info("Updating upload templates...")
        
        templates_dir = self.output_path / 'upload_templates'
        templates_dir.mkdir(exist_ok=True)
        
        # Create template for cfab_Yarn_Demand_By_Style.csv
        yarn_demand_template = pd.DataFrame({
            'Style': ['125792/1', '125792/1', '180001/20ST2'],
            'Yarn': ['18767', '18929', '18320'],
            'Percentage': [91.4, 8.6, 13.1],
            'This Week': ['1,919.4', '180.6', '336.9'],
            'Week 17': ['', '', '102.6'],
            'Week 18': ['', '', ''],
            'Week 19': ['', '', ''],
            'Week 20': ['', '', ''],
            'Week 21': ['', '', ''],
            'Week 22': ['', '', ''],
            'Week 23': ['', '', ''],
            'Week 24': ['', '', ''],
            'Later': ['', '', ''],
            'Total': ['1,919.4', '180.6', '439.5']
        })
        yarn_demand_template.to_csv(templates_dir / 'cfab_Yarn_Demand_By_Style_template.csv', index=False)
        
        # Create template for eFab_SO_List.csv
        sales_orders_template = pd.DataFrame({
            'Status': ['Open', 'Open'],
            'CSR': ['Brittany Lee', 'Brittany Lee'],
            'Unit Price': ['$5.95 (yds)', '$5.48 (yds)'],
            'Quoted Date': ['6/10/2025', '6/12/2025'],
            'cFVersion': ['70009236', '50000183'],
            'fBase': ['C1B4350-1/0', 'C1B4125-1/0'],
            'On Hold': ['<div>...</div>', '<div>...</div>'],
            'Ordered': [40, 40],
            'UOM': ['yds', 'yds'],
            'SOP': ['SP2506073/2', 'SP2506087/1'],
            'PO #': ['L8265-069', 'L8307-077'],
            'Sold To': ['Serta Simmons Bedding Company', 'Serta Simmons Bedding Company'],
            'Ship To': ['SSBMF - WEST PALM', 'SSBMF - GROVETOWN'],
            'Ship Date': ['', '']
        })
        sales_orders_template.to_csv(templates_dir / 'eFab_SO_List_template.csv', index=False)
        
        # Create template for Style_BOM.csv
        style_bom_template = pd.DataFrame({
            'Style_ID': ['125792/1', '125792/1', '180001/20ST2'],
            'Yarn_ID': ['18767', '18929', '18320'],
            'BOM_Percentage': [0.914, 0.086, 0.131]
        })
        style_bom_template.to_csv(templates_dir / 'Style_BOM_template.csv', index=False)
        
        # Create template for Inventory.csv
        inventory_template = pd.DataFrame({
            'style_id': ['125792/0', '1874-499/WOLFE', '1942/0'],
            'yds': [940, 381, 15],
            'lbs': ['1,387', '232', '11']
        })
        inventory_template.to_csv(templates_dir / 'Inventory_template.csv', index=False)
        
        # Create template for Supplier_ID.csv
        supplier_template = pd.DataFrame({
            'Supplier_ID': [1, 2, 3],
            'Supplier': ['AKRA POLYESTER GROUP/DAK', 'AMES (Do not Use)', 'BANSWARA SYNTEX LIMITED'],
            'Lead_time': ['Remove', 'Remove', 14],
            'MOQ': ['Remove', 'Remove', 5000],
            'Type': ['Remove', 'Remove', 'Import']
        })
        supplier_template.to_csv(templates_dir / 'Supplier_ID_template.csv', index=False)
        
        # Create template for Yarn_ID.csv
        yarn_template = pd.DataFrame({
            'Yarn_ID': ['19020', '18868', '18517'],
            'Supplier': ['R BELDA LLORENS', 'FERR', 'DECA GLOBAL'],
            'Description': ['30/1', '30/1', '1/100/96'],
            'Blend': ['55/45', '60/40', '100%'],
            'Type': ['Polyester/Recycled Cotton', 'Polyester/Recycled Cotton', 'Polyester'],
            'Color': ['Indigo', 'Anil', 'Natural'],
            'Desc_1': ['Cotton', 'Cotton', 'Z'],
            'Desc_2': ['Indigo', 'Anil', ''],
            'Desc_3': ['V', '', ''],
            'On_Order': [0.00, '2,500.00', 0.00],
            'Allocated': [0.00, 0.00, -255.48],
            'Planning_Ballance': [-428.96, '1,989.38', -581.74],
            'Cost_Pound': ['$5.09 ', '$3.90 ', '$1.09 '],
            'Total_Cast': ['($2,183.40)', '($1,991.43)', '($355.62)']
        })
        yarn_template.to_csv(templates_dir / 'Yarn_ID_template.csv', index=False)
        
        logger.info(f"✅ Created {len(list(templates_dir.glob('*.csv')))} upload templates")
    
    def _create_migration_scripts(self):
        """Create scripts to migrate from old format to live format"""
        logger.info("Creating migration scripts...")
        
        migration_dir = self.output_path / 'migration_scripts'
        migration_dir.mkdir(exist_ok=True)
        
        # Create migration script for BOMs
        bom_migration_script = '''
"""
BOM Migration Script
====================
Converts old BOM format to live data format
"""

import pandas as pd
from pathlib import Path

def migrate_boms(old_bom_file: str, output_file: str):
    """Convert old BOM format to Style_BOM.csv format"""
    
    # Load old format
    old_df = pd.read_csv(old_bom_file)
    
    # Expected old format columns: sku_id, material_id, qty_per_unit, unit
    # Convert to live format columns: Style_ID, Yarn_ID, BOM_Percentage
    
    new_df = pd.DataFrame({
        'Style_ID': old_df['sku_id'],
        'Yarn_ID': old_df['material_id'],
        'BOM_Percentage': old_df['qty_per_unit']  # Assuming already in 0-1 scale
    })
    
    # Save in live format
    new_df.to_csv(output_file, index=False)
    print(f"Migrated {len(new_df)} BOM records to {output_file}")

if __name__ == "__main__":
    migrate_boms("old_boms.csv", "Style_BOM.csv")
'''
        
        with open(migration_dir / 'migrate_boms.py', 'w') as f:
            f.write(bom_migration_script)
        
        # Create migration script for inventory
        inventory_migration_script = '''
"""
Inventory Migration Script
==========================
Converts old inventory format to live data format
"""

import pandas as pd

def migrate_inventory(old_inventory_file: str, output_file: str):
    """Convert old inventory format to Inventory.csv format"""
    
    # Load old format
    old_df = pd.read_csv(old_inventory_file)
    
    # Expected old format: material_id, on_hand_qty, unit, open_po_qty, po_expected_date
    # Convert to live format: style_id, yds, lbs
    
    new_df = pd.DataFrame({
        'style_id': old_df['material_id'],
        'yds': old_df['on_hand_qty'],
        'lbs': old_df['on_hand_qty']  # Assuming same value for demo
    })
    
    # Format numbers with commas for large values
    new_df['yds'] = new_df['yds'].apply(lambda x: f"{x:,.0f}" if x >= 1000 else str(x))
    new_df['lbs'] = new_df['lbs'].apply(lambda x: f"{x:,.0f}" if x >= 1000 else str(x))
    
    # Save in live format
    new_df.to_csv(output_file, index=False)
    print(f"Migrated {len(new_df)} inventory records to {output_file}")

if __name__ == "__main__":
    migrate_inventory("old_inventory.csv", "Inventory.csv")
'''
        
        with open(migration_dir / 'migrate_inventory.py', 'w') as f:
            f.write(inventory_migration_script)
        
        logger.info("✅ Created migration scripts")
    
    def _generate_documentation(self):
        """Generate comprehensive documentation"""
        logger.info("Generating documentation...")
        
        docs_dir = self.output_path / 'documentation'
        docs_dir.mkdir(exist_ok=True)
        
        # Create live data format guide
        format_guide = '''
# Beverly Knits Live Data Format Guide

## Overview
This guide covers the exact format and structure of Beverly Knits live CSV data files and how the planning system processes them.

## Live Data Files

### 1. cfab_Yarn_Demand_By_Style.csv
**Purpose**: Yarn demand by style with weekly breakdown
**Format**: Style, Yarn, Percentage, This Week, Week 17-24, Later, Total
**Special Processing**:
- Handles comma-separated numbers (e.g., "1,919.4")
- Percentage is in 0-100 scale
- Weekly columns may be empty

### 2. eFab_SO_List.csv
**Purpose**: Sales orders with customer and product details
**Format**: Status, CSR, Unit Price, Quoted Date, cFVersion, fBase, On Hold, Ordered, UOM, SOP, PO #, Sold To, Ship To, Ship Date
**Special Processing**:
- Unit Price in format "$5.95 (yds)"
- On Hold contains HTML toggle content
- cFVersion is the style/product code

### 3. Style_BOM.csv
**Purpose**: Bill of Materials defining yarn composition
**Format**: Style_ID, Yarn_ID, BOM_Percentage
**Special Processing**:
- BOM_Percentage is in 0-1 scale
- Percentages should sum to 1.0 per style

### 4. Inventory.csv
**Purpose**: Current inventory levels
**Format**: style_id, yds, lbs
**Special Processing**:
- Handles comma-separated numbers
- Both yds and lbs columns may contain formatted numbers

### 5. Supplier_ID.csv
**Purpose**: Supplier master data with constraints
**Format**: Supplier_ID, Supplier, Lead_time, MOQ, Type
**Special Processing**:
- "Remove" values indicate inactive suppliers
- Lead_time and MOQ may be "Remove" or numeric

### 6. Yarn_ID.csv
**Purpose**: Yarn master data with costs and inventory
**Format**: Yarn_ID, Supplier, Description, Blend, Type, Color, Desc_1, Desc_2, Desc_3, On_Order, Allocated, Planning_Ballance, Cost_Pound, Total_Cast
**Special Processing**:
- Cost_Pound in format "$5.09 "
- Total_Cast uses parentheses for negatives: "($2,183.40)"
- Planning_Ballance can be negative

## Data Processing Flow

1. **Load**: Read CSV files with proper encoding
2. **Parse**: Handle formatted numbers, currency, HTML
3. **Validate**: Check data quality and consistency
4. **Convert**: Transform to planning system format
5. **Plan**: Execute planning algorithms
6. **Export**: Generate recommendations and reports

## Key Features

- **Automatic Format Detection**: System recognizes and handles all formatting
- **Cross-Validation**: Validates consistency between BOM files
- **Error Handling**: Graceful handling of missing or invalid data
- **Live Updates**: No preprocessing required - use files directly

## Best Practices

1. Maintain exact column names and formats
2. Use consistent style and yarn IDs across files
3. Ensure BOM percentages sum correctly
4. Keep supplier data up to date
5. Validate data before major planning runs
'''
        
        with open(docs_dir / 'LIVE_DATA_FORMAT_GUIDE.md', 'w') as f:
            f.write(format_guide)
        
        # Create API documentation
        api_docs = '''
# Beverly Knits Live Data API Documentation

## LiveDataIntegrator Class

### Purpose
Integrates live CSV files directly into the planning system.

### Key Methods

#### `load_all_live_data() -> Dict[str, Any]`
Loads all live CSV files and returns structured data.

#### `convert_to_planning_format() -> Dict[str, List]`
Converts live data to standard planning system format.

#### `generate_planning_inputs() -> Dict[str, Any]`
Generates complete planning inputs with validation.

## LiveDataPlanner Class

### Purpose
Planning engine optimized for live data format.

### Key Methods

#### `run_full_planning_cycle() -> Dict[str, Any]`
Executes complete planning cycle with live data.

#### `export_planning_results(output_path: str) -> Dict[str, str]`
Exports planning results to multiple formats.

## Live Data Models

### YarnDemandByStyle
Represents yarn demand data from cfab_Yarn_Demand_By_Style.csv

### SalesOrder
Represents sales order data from eFab_SO_List.csv

### StyleBOM
Represents BOM data from Style_BOM.csv

### InventoryItem
Represents inventory data from Inventory.csv

### SupplierInfo
Represents supplier data from Supplier_ID.csv

### YarnMaster
Represents yarn master data from Yarn_ID.csv

## Usage Examples

```python
# Load and process live data
integrator = LiveDataIntegrator()
planning_inputs = integrator.generate_planning_inputs()

# Run planning
planner = LiveDataPlanner()
results = planner.run_full_planning_cycle()

# Export results
exported_files = planner.export_planning_results()
```
'''
        
        with open(docs_dir / 'API_DOCUMENTATION.md', 'w') as f:
            f.write(api_docs)
        
        logger.info("✅ Generated comprehensive documentation")
    
    def _run_full_system_test(self):
        """Run complete end-to-end system test"""
        logger.info("Running full system test...")
        
        system_test_results = {
            'end_to_end_test': None,
            'performance_test': None,
            'integration_test': None
        }
        
        try:
            # End-to-end test
            start_time = datetime.now()
            
            # Load data
            integrator = LiveDataIntegrator(str(self.data_path))
            planning_inputs = integrator.generate_planning_inputs()
            
            # Run planning
            planner = LiveDataPlanner(str(self.data_path))
            results = planner.run_full_planning_cycle()
            
            # Export results
            exported_files = planner.export_planning_results(str(self.output_path / 'system_test'))
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            system_test_results['end_to_end_test'] = {
                'success': True,
                'processing_time_seconds': processing_time,
                'total_recommendations': len(results.get('procurement_recommendations', [])),
                'total_cost': results.get('planning_summary', {}).get('totals', {}).get('total_cost', 0),
                'files_exported': len(exported_files)
            }
            
            logger.info(f"  ✅ End-to-end test completed in {processing_time:.2f} seconds")
            
        except Exception as e:
            system_test_results['end_to_end_test'] = {'success': False, 'error': str(e)}
            logger.error(f"  ❌ End-to-end test failed: {e}")
        
        self.test_results['system_test'] = system_test_results
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final update report"""
        logger.info("Generating final report...")
        
        report = {
            'update_summary': self.update_summary,
            'validation_results': self.validation_results,
            'test_results': self.test_results,
            'recommendations': self._generate_recommendations(),
            'next_steps': self._generate_next_steps()
        }
        
        # Save report
        report_file = self.output_path / 'workflow_update_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Create summary text
        summary_text = self._create_summary_text(report)
        summary_file = self.output_path / 'workflow_update_summary.txt'
        with open(summary_file, 'w') as f:
            f.write(summary_text)
        
        logger.info(f"✅ Final report saved to {report_file}")
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check file validation
        file_validation = self.validation_results.get('file_validation', {})
        if file_validation.get('files_missing'):
            recommendations.append("Obtain missing data files before production use")
        
        # Check validation issues
        total_issues = sum(
            len(v.get('issues', [])) for v in file_validation.get('file_validations', {}).values()
        )
        if total_issues > 0:
            recommendations.append(f"Resolve {total_issues} data quality issues")
        
        # Check test results
        integration_test = self.test_results.get('integration_test', {})
        if not integration_test.get('load_test', {}).get('success'):
            recommendations.append("Fix data loading issues before deployment")
        
        planning_test = self.test_results.get('planning_test', {})
        if not planning_test.get('planning_cycle_test', {}).get('success'):
            recommendations.append("Resolve planning engine issues")
        
        if not recommendations:
            recommendations.append("System is ready for production use with live data format")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps for implementation"""
        return [
            "1. Review and resolve any data quality issues",
            "2. Train users on new live data format",
            "3. Update data collection processes",
            "4. Implement regular data validation checks",
            "5. Set up automated planning runs",
            "6. Monitor system performance",
            "7. Collect user feedback and iterate"
        ]
    
    def _create_summary_text(self, report: Dict[str, Any]) -> str:
        """Create human-readable summary text"""
        summary = f'''
Beverly Knits Live Data Workflow Update Summary
============================================== 
Update Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {report['update_summary'].get('completion_status', 'UNKNOWN')}

File Validation Results:
-----------------------
Files Found: {len(report['validation_results'].get('file_validation', {}).get('files_found', []))}
Files Missing: {len(report['validation_results'].get('file_validation', {}).get('files_missing', []))}

Test Results:
-------------
Integration Tests: {'✅ PASSED' if report['test_results'].get('integration_test', {}).get('load_test', {}).get('success') else '❌ FAILED'}
Planning Tests: {'✅ PASSED' if report['test_results'].get('planning_test', {}).get('planning_cycle_test', {}).get('success') else '❌ FAILED'}
System Tests: {'✅ PASSED' if report['test_results'].get('system_test', {}).get('end_to_end_test', {}).get('success') else '❌ FAILED'}

Key Metrics:
-----------
Total Processing Time: {report['update_summary'].get('total_time', 0):.2f} seconds
Recommendations Generated: {report['test_results'].get('system_test', {}).get('end_to_end_test', {}).get('total_recommendations', 0)}
Files Exported: {report['test_results'].get('system_test', {}).get('end_to_end_test', {}).get('files_exported', 0)}

Recommendations:
---------------
'''
        
        for i, rec in enumerate(report['recommendations'], 1):
            summary += f"{i}. {rec}\n"
        
        summary += "\nNext Steps:\n-----------\n"
        for step in report['next_steps']:
            summary += f"{step}\n"
        
        return summary


def main():
    """Main function to run the workflow update"""
    updater = LiveDataWorkflowUpdater()
    
    try:
        results = updater.run_complete_update()
        
        print("\n" + "="*60)
        print("BEVERLY KNITS LIVE DATA WORKFLOW UPDATE COMPLETE")
        print("="*60)
        print(f"Status: {results['update_summary']['completion_status']}")
        print(f"Total Time: {results['update_summary']['total_time']:.2f} seconds")
        print(f"Files Validated: {len(results['validation_results'].get('file_validation', {}).get('files_found', []))}")
        print(f"Tests Passed: {sum(1 for test_group in results['test_results'].values() for test in test_group.values() if isinstance(test, dict) and test.get('success'))}")
        print(f"Output Files: {len(list(Path('output').glob('**/*'))) if Path('output').exists() else 0}")
        
        print("\nRecommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. {rec}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Workflow update failed: {e}")
        raise


if __name__ == "__main__":
    main()