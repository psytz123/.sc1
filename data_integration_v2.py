"""
Beverly Knits Data Integration Script - Updated Version
Automatically handles data quality issues:
1. Missing costs updated manually
2. Negative inventory balances rounded to 0 (planning_balances can be negative)
3. BOM percentages > 0.99 rounded to 1.0
"""

import json
from utils.logger import get_logger

logger = get_logger(__name__)
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings('ignore')

class BeverlyKnitsDataIntegrator:
    """Enhanced data integrator with automatic data quality fixes"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.quality_issues = []
        
    def load_and_clean_data(self):
        """Load and automatically clean all data files"""
        logger.info("🔄 Loading and cleaning Beverly Knits data...")
        
        # Load raw data
        yarn_master = pd.read_csv(self.data_dir / "Yarn_ID_1.csv")
        inventory = pd.read_csv(self.data_dir / "Yarn_ID_Current_Inventory.csv")
        suppliers = pd.read_csv(self.data_dir / "Supplier_ID.csv")
        boms = pd.read_csv(self.data_dir / "Style_BOM.csv")
        
        logger.info(f"✅ Loaded raw data:")
        logger.info(f"   • Yarn Master: {len(yarn_master)} records")
        logger.info(f"   • Inventory: {len(inventory)} records")
        logger.info(f"   • Suppliers: {len(suppliers)} records")
        logger.info(f"   • BOMs: {len(boms)} records")
        
        # Apply automatic fixes
        inventory_cleaned = self._fix_inventory_balances(inventory)
        boms_cleaned = self._fix_bom_percentages(boms)
        suppliers_cleaned = self._clean_suppliers(suppliers)
        
        # Integrate data
        integrated_data = self._integrate_datasets(
            yarn_master, inventory_cleaned, suppliers_cleaned, boms_cleaned
        )
        
        return integrated_data
    
    def _fix_inventory_balances(self, inventory_df):
        """Fix negative inventory balances by rounding to 0"""
        logger.info("\n🔧 Fixing inventory balances...")

        inventory_fixed = inventory_df.copy()

        # Clean and convert numeric columns
        numeric_columns = ['Inventory', 'On_Order', 'Allocated']
        for col in numeric_columns:
            if col in inventory_fixed.columns:
                # Remove commas and convert to numeric
                inventory_fixed[col] = pd.to_numeric(
                    inventory_fixed[col].astype(str).str.replace(',', '').str.replace('$', '').str.replace('(', '-').str.replace(')', ''),
                    errors='coerce'
                ).fillna(0)

        # Handle Planning_Ballance column (note the typo in original data)
        planning_col = 'Planning_Ballance' if 'Planning_Ballance' in inventory_fixed.columns else 'Planning_Balance'
        if planning_col in inventory_fixed.columns:
            # Clean planning balance column
            inventory_fixed[planning_col] = inventory_fixed[planning_col].astype(str).str.replace(',', '').str.replace('$', '').str.replace('(', '-').str.replace(')', '').str.strip()
            inventory_fixed[planning_col] = pd.to_numeric(inventory_fixed[planning_col], errors='coerce').fillna(0)

        # Fix negative current stock (round to 0)
        negative_stock = inventory_fixed['Inventory'] < 0
        if negative_stock.any():
            count = negative_stock.sum()
            logger.info(f"   • Fixed {count} negative inventory balances → 0")
            inventory_fixed.loc[negative_stock, 'Inventory'] = 0
            self.quality_issues.append(f"Fixed {count} negative inventory balances")

        # Fix negative on-order (round to 0)
        negative_on_order = inventory_fixed['On_Order'] < 0
        if negative_on_order.any():
            count = negative_on_order.sum()
            logger.info(f"   • Fixed {count} negative on-order balances → 0")
            inventory_fixed.loc[negative_on_order, 'On_Order'] = 0
            self.quality_issues.append(f"Fixed {count} negative on-order balances")

        # Planning balances can remain negative (as per requirement)
        negative_planning = inventory_fixed[planning_col] < 0
        if negative_planning.any():
            count = negative_planning.sum()
            logger.info(f"   • Kept {count} negative planning balances (allowed)")

        return inventory_fixed
    
    def _fix_bom_percentages(self, boms_df):
        """Fix BOM percentages > 0.99 by rounding to 1.0"""
        logger.info("\n🔧 Fixing BOM percentages...")
        
        boms_fixed = boms_df.copy()
        
        # Group by Style_ID and check totals
        style_totals = boms_fixed.groupby('Style_ID')['BOM_Percentage'].sum()

        # Find styles with totals > 0.99 but < 1.01 (close to 1.0)
        close_to_one = (style_totals > 0.99) & (style_totals < 1.01)
        styles_to_fix = style_totals[close_to_one].index

        if len(styles_to_fix) > 0:
            logger.info(f"   • Found {len(styles_to_fix)} styles with percentages close to 1.0")

            for style_id in styles_to_fix:
                style_mask = boms_fixed['Style_ID'] == style_id
                current_total = boms_fixed.loc[style_mask, 'BOM_Percentage'].sum()

                if 0.99 < current_total < 1.01:
                    # Proportionally adjust to sum to 1.0
                    adjustment_factor = 1.0 / current_total
                    boms_fixed.loc[style_mask, 'BOM_Percentage'] *= adjustment_factor

            logger.info(f"   • Adjusted {len(styles_to_fix)} styles to sum to 1.0")
            self.quality_issues.append(f"Fixed BOM percentages for {len(styles_to_fix)} styles")

        # Check for styles still not summing to 1.0
        final_totals = boms_fixed.groupby('Style_ID')['BOM_Percentage'].sum()
        incorrect_totals = final_totals[(final_totals < 0.98) | (final_totals > 1.02)]

        if len(incorrect_totals) > 0:
            logger.info(f"   ⚠️  {len(incorrect_totals)} styles still have incorrect totals (require manual review)")
            self.quality_issues.append(f"{len(incorrect_totals)} styles still have incorrect BOM totals")

        return boms_fixed
    
    def _clean_suppliers(self, suppliers_df):
        """Clean supplier data by removing invalid suppliers"""
        logger.info("\n🔧 Cleaning supplier data...")
        
        # Remove suppliers marked for removal
        valid_suppliers = suppliers_df[
            (suppliers_df['Supplier_ID'] != 'Remove') & 
            (suppliers_df['Supplier_ID'].notna())
        ].copy()
        
        removed_count = len(suppliers_df) - len(valid_suppliers)
        if removed_count > 0:
            logger.info(f"   • Removed {removed_count} invalid suppliers")
            self.quality_issues.append(f"Removed {removed_count} invalid suppliers")
        
        return valid_suppliers
    
    def _integrate_datasets(self, yarn_master, inventory, suppliers, boms):
        """Integrate all datasets with enhanced logic"""
        logger.info("\n🔄 Integrating datasets...")
        
        logger.info("\n🔄 Integrating datasets...")

        # Create master materials dataset
        materials = self._create_materials_master(yarn_master, inventory)

        # Create supplier relationships
        supplier_relationships = self._create_supplier_relationships(materials, suppliers)

        # Create inventory dataset
        inventory_integrated = self._create_inventory_dataset(materials, inventory)

        # Create BOM dataset
        boms_integrated = self._create_bom_dataset(boms, materials)

        # Identify interchangeable yarns
        interchangeable_groups = self._identify_interchangeable_yarns(materials)

        return {
            'materials': materials,
            'suppliers': supplier_relationships,
            'inventory': inventory_integrated,
            'boms': boms_integrated,
            'interchangeable_yarns': interchangeable_groups,
            'quality_issues': self.quality_issues
        }
    
    def _create_materials_master(self, yarn_master, inventory):
        """Create integrated materials master"""
        # Clean cost column in inventory
        inventory_clean = inventory.copy()
        cost_col = 'Cost_Pound' if 'Cost_Pound' in inventory_clean.columns else 'Cost_per_Unit'

        if cost_col in inventory_clean.columns:
            # Clean cost column - remove $ and convert to numeric
            inventory_clean[cost_col] = pd.to_numeric(
                inventory_clean[cost_col].astype(str).str.replace('$', '').str.replace(',', '').str.strip(),
                errors='coerce'
            ).fillna(0)

        # Merge yarn master with inventory data, keeping yarn master supplier info
        materials = pd.merge(
            yarn_master,
            inventory_clean[['Yarn_ID', cost_col]],
            on='Yarn_ID',
            how='left'
        )

        # Rename columns for consistency
        materials = materials.rename(columns={
            'Yarn_ID': 'material_id',
            cost_col: 'cost_per_unit'
        })

        # Handle missing costs (assume they were updated manually)
        zero_cost_count = (materials['cost_per_unit'] == 0).sum()
        if zero_cost_count > 0:
            logger.info(f"   • Found {zero_cost_count} materials with zero cost (assuming manually updated)")

        return materials
    
    def _create_supplier_relationships(self, materials, suppliers):
        """Create supplier-material relationships"""
        # Convert supplier names to string for consistent matching
        materials_clean = materials.copy()
        materials_clean['Supplier'] = materials_clean['Supplier'].astype(str)
        suppliers_clean = suppliers.copy()
        suppliers_clean['Supplier'] = suppliers_clean['Supplier'].astype(str)

        # Merge materials with supplier data using the Supplier name
        supplier_relationships = pd.merge(
            materials_clean[['material_id', 'cost_per_unit', 'Supplier']],
            suppliers_clean,
            left_on='Supplier',
            right_on='Supplier',
            how='left'
        )

        # Filter out rows without valid suppliers
        supplier_relationships = supplier_relationships[supplier_relationships['Supplier_ID'].notna()]

        # Add default values for missing data
        supplier_relationships['lead_time_days'] = pd.to_numeric(supplier_relationships['Lead_time'], errors='coerce').fillna(14)
        supplier_relationships['moq'] = pd.to_numeric(supplier_relationships['MOQ'], errors='coerce').fillna(1000)
        supplier_relationships['reliability_score'] = 0.85  # Default reliability

        # Determine supplier type based on the Type column or name patterns
        supplier_relationships['supplier_type'] = supplier_relationships.apply(
            lambda row: row['Type'] if pd.notna(row['Type']) and row['Type'] not in ['Remove', '']
            else ('Domestic' if any(term in str(row['Supplier']).upper() for term in ['CORP', 'INC', 'LLC', 'USA', 'AMERICA'])
                  else 'Import'), axis=1
        )

        return supplier_relationships[['material_id', 'Supplier_ID', 'cost_per_unit', 'lead_time_days', 'moq', 'reliability_score', 'supplier_type']].rename(columns={'Supplier_ID': 'supplier_id'})
    
    def _create_inventory_dataset(self, materials, inventory):
        """Create integrated inventory dataset"""
        # Use the correct column name (Planning_Ballance with typo)
        planning_col = 'Planning_Ballance' if 'Planning_Ballance' in inventory.columns else 'Planning_Balance'

        inventory_integrated = pd.merge(
            materials[['material_id']],
            inventory[['Yarn_ID', 'Inventory', 'On_Order', 'Allocated', planning_col]],
            left_on='material_id',
            right_on='Yarn_ID',
            how='left'
        )

        # Rename columns
        rename_dict = {
            'Inventory': 'current_stock',
            'On_Order': 'incoming_stock',
            'Allocated': 'allocated_stock',
            planning_col: 'planning_balance'
        }
        inventory_integrated = inventory_integrated.rename(columns=rename_dict)

        # Fill missing values
        inventory_integrated = inventory_integrated.fillna(0)

        return inventory_integrated[['material_id', 'current_stock', 'incoming_stock', 'allocated_stock', 'planning_balance']]
    
    def _create_bom_dataset(self, boms, materials):
        """Create integrated BOM dataset"""
        boms_integrated = pd.merge(
            boms,
            materials[['material_id']],
            left_on='Yarn_ID',
            right_on='material_id',
            how='inner'
        )
        
        # Rename columns
        boms_integrated = boms_integrated.rename(columns={
            'Style_ID': 'sku_id',
            'BOM_Percentage': 'quantity_per_unit'
        })

        return boms_integrated[['sku_id', 'material_id', 'quantity_per_unit']]
    
    def _identify_interchangeable_yarns(self, materials):
        """Identify interchangeable yarn groups"""
        # Group by specifications
        spec_columns = ['Description', 'Blend', 'Type', 'Color']
        available_columns = [col for col in spec_columns if col in materials.columns]
        
        if not available_columns:
            return {}
        
        # Create specification key
        materials['spec_key'] = materials[available_columns].fillna('').apply(
            lambda x: '_'.join(x.astype(str)), axis=1
        )
        
        # Find groups with multiple yarns
        yarn_groups = materials.groupby('spec_key')['material_id'].apply(list)
        interchangeable_groups = yarn_groups[yarn_groups.apply(len) > 1]
        
        # Format as dictionary
        result = {}
        for i, (spec_key, yarn_ids) in enumerate(interchangeable_groups.items()):
            group_name = f"Group_{i+1}_{spec_key[:20]}"
            result[group_name] = {
                'yarn_ids': [float(y) for y in yarn_ids],
                'specifications': dict(zip(available_columns, spec_key.split('_')))
            }
        
        return result
    
    def save_integrated_data(self, integrated_data):
        """Save all integrated datasets"""
        logger.info("\n💾 Saving integrated datasets...")
        
        # Save main datasets
        integrated_data['materials'].to_csv(self.data_dir / 'integrated_materials_v2.csv', index=False)
        integrated_data['suppliers'].to_csv(self.data_dir / 'integrated_suppliers_v2.csv', index=False)
        integrated_data['inventory'].to_csv(self.data_dir / 'integrated_inventory_v2.csv', index=False)
        integrated_data['boms'].to_csv(self.data_dir / 'integrated_boms_v2.csv', index=False)
        
        # Save interchangeable yarns
        with open(self.data_dir / 'interchangeable_yarns_v2.json', 'w') as f:
            json.dump(integrated_data['interchangeable_yarns'], f, indent=2)
        
        # Save quality issues report
        with open(self.data_dir / 'data_quality_report_v2.txt', 'w', encoding='utf-8') as f:
            f.write("Beverly Knits Data Quality Report - Updated Version\n")
            f.write("=" * 60 + "\n\n")
            f.write("AUTOMATIC FIXES APPLIED:\n")
            for issue in integrated_data['quality_issues']:
                f.write(f"• {issue}\n")
            f.write(f"\nTotal automatic fixes applied: {len(integrated_data['quality_issues'])}\n")
        
        logger.info(f"✅ Saved updated datasets:")
        logger.info(f"   • integrated_materials_v2.csv ({len(integrated_data['materials'])} records)")
        logger.info(f"   • integrated_suppliers_v2.csv ({len(integrated_data['suppliers'])} records)")
        logger.info(f"   • integrated_inventory_v2.csv ({len(integrated_data['inventory'])} records)")
        logger.info(f"   • integrated_boms_v2.csv ({len(integrated_data['boms'])} records)")
        logger.info(f"   • interchangeable_yarns_v2.json ({len(integrated_data['interchangeable_yarns'])} groups)")
        logger.info(f"   • data_quality_report_v2.txt ({len(integrated_data['quality_issues'])} fixes)")

def main():
    """Run the enhanced data integration"""
    logger.info("🚀 Beverly Knits Enhanced Data Integration")
    logger.info("=" * 50)
    
    integrator = BeverlyKnitsDataIntegrator()
    integrated_data = integrator.load_and_clean_data()
    integrator.save_integrated_data(integrated_data)
    
    logger.info("\n🎉 Enhanced Integration Complete!")
    logger.info("\nAutomatic fixes applied:")
    for issue in integrated_data['quality_issues']:
        logger.info(f"   ✅ {issue}")
    
    logger.info(f"\n📊 Final Statistics:")
    logger.info(f"   • Materials: {len(integrated_data['materials'])}")
    logger.info(f"   • Supplier relationships: {len(integrated_data['suppliers'])}")
    logger.info(f"   • Inventory records: {len(integrated_data['inventory'])}")
    logger.info(f"   • BOM lines: {len(integrated_data['boms'])}")
    logger.info(f"   • Interchangeable groups: {len(integrated_data['interchangeable_yarns'])}")
    logger.info(f"   • Automatic fixes: {len(integrated_data['quality_issues'])}")

if __name__ == "__main__":
    main()