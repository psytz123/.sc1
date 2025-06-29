"""
Beverly Knits Real Data Integration Module
Processes and validates yarn, supplier, inventory, and BOM data
"""

import re
from utils.logger import get_logger

logger = get_logger(__name__)
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd


@dataclass
class DataQualityIssue:
    """Represents a data quality issue found during validation"""
    file_name: str
    row_index: int
    column: str
    issue_type: str
    current_value: str
    suggested_action: str

class BeverlyKnitsDataIntegrator:
    """Integrates and validates Beverly Knits real data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.quality_issues: List[DataQualityIssue] = []
        
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load all data files and return as dictionary of DataFrames"""
        data = {}
        
        # Load yarn specifications
        data['yarn_specs'] = pd.read_csv(self.data_dir / "Yarn_ID_1.csv")
        
        # Load yarn inventory and costs
        data['yarn_inventory'] = pd.read_csv(self.data_dir / "Yarn_ID_Current_Inventory.csv")
        
        # Load supplier data
        data['suppliers'] = pd.read_csv(self.data_dir / "Supplier_ID.csv")
        
        # Load BOM data
        data['bom'] = pd.read_csv(self.data_dir / "Style_BOM.csv")
        
        return data
    
    def validate_supplier_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean supplier data"""
        logger.info("🔍 Validating Supplier Data...")
        
        # Identify suppliers marked for removal
        remove_suppliers = df[df['Lead_time'] == 'Remove'].copy()
        if not remove_suppliers.empty:
            logger.info(f"⚠️  Found {len(remove_suppliers)} suppliers marked for removal:")
            for _, row in remove_suppliers.iterrows():
                logger.info(f"   - {row['Supplier']} (ID: {row['Supplier_ID']})")
                self.quality_issues.append(DataQualityIssue(
                    file_name="Supplier_ID.csv",
                    row_index=row.name,
                    column="Lead_time",
                    issue_type="MARKED_FOR_REMOVAL",
                    current_value=row['Supplier'],
                    suggested_action="Confirm removal or provide valid lead time/MOQ data"
                ))
        
        # Clean data - remove suppliers marked for removal
        clean_df = df[df['Lead_time'] != 'Remove'].copy()
        
        # Convert lead time and MOQ to numeric
        clean_df['Lead_time'] = pd.to_numeric(clean_df['Lead_time'], errors='coerce')
        clean_df['MOQ'] = pd.to_numeric(clean_df['MOQ'], errors='coerce')
        
        # Check for missing lead times or MOQs
        missing_lead_time = clean_df[clean_df['Lead_time'].isna()]
        missing_moq = clean_df[clean_df['MOQ'].isna()]
        
        for _, row in missing_lead_time.iterrows():
            self.quality_issues.append(DataQualityIssue(
                file_name="Supplier_ID.csv",
                row_index=row.name,
                column="Lead_time",
                issue_type="MISSING_VALUE",
                current_value="NaN",
                suggested_action="Provide lead time in days"
            ))
            
        for _, row in missing_moq.iterrows():
            self.quality_issues.append(DataQualityIssue(
                file_name="Supplier_ID.csv",
                row_index=row.name,
                column="MOQ",
                issue_type="MISSING_VALUE",
                current_value="NaN",
                suggested_action="Provide minimum order quantity"
            ))
        
        logger.info(f"✅ Cleaned supplier data: {len(clean_df)} valid suppliers")
        return clean_df
    
    def validate_yarn_inventory_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean yarn inventory data"""
        logger.info("🔍 Validating Yarn Inventory Data...")
        
        # Clean numeric columns - remove $ signs and commas
        numeric_columns = ['Inventory', 'On_Order', 'Allocated', 'Planning_Ballance', 'Cost_Pound', 'Total_Cast']
        
        for col in numeric_columns:
            if col in df.columns:
                # Remove $ signs, commas, parentheses and convert to numeric
                df[col] = df[col].astype(str).str.replace(r'[\$,\(\)]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Check for zero or missing costs
        zero_cost_yarns = df[(df['Cost_Pound'] == 0) | (df['Cost_Pound'].isna())]
        if not zero_cost_yarns.empty:
            logger.info(f"⚠️  Found {len(zero_cost_yarns)} yarns with zero or missing costs:")
            for _, row in zero_cost_yarns.iterrows():
                logger.info(f"   - Yarn {row['Yarn_ID']}: {row['Supplier']} - {row['Description']}")
                self.quality_issues.append(DataQualityIssue(
                    file_name="Yarn_ID_Current_Inventory.csv",
                    row_index=row.name,
                    column="Cost_Pound",
                    issue_type="ZERO_OR_MISSING_COST",
                    current_value=str(row['Cost_Pound']),
                    suggested_action="Provide valid cost per pound"
                ))
        
        # Check for negative planning balances
        negative_balance = df[df['Planning_Ballance'] < 0]
        if not negative_balance.empty:
            logger.info(f"⚠️  Found {len(negative_balance)} yarns with negative planning balance:")
            for _, row in negative_balance.iterrows():
                logger.info(f"   - Yarn {row['Yarn_ID']}: Balance = {row['Planning_Ballance']}")
                self.quality_issues.append(DataQualityIssue(
                    file_name="Yarn_ID_Current_Inventory.csv",
                    row_index=row.name,
                    column="Planning_Ballance",
                    issue_type="NEGATIVE_BALANCE",
                    current_value=str(row['Planning_Ballance']),
                    suggested_action="Review inventory calculation: Inventory + On_Order - Allocated"
                ))
        
        # Check for missing descriptive data
        desc_columns = ['Description', 'Blend', 'Type', 'Color']
        for col in desc_columns:
            missing_desc = df[df[col].isna() | (df[col] == '')]
            for _, row in missing_desc.iterrows():
                self.quality_issues.append(DataQualityIssue(
                    file_name="Yarn_ID_Current_Inventory.csv",
                    row_index=row.name,
                    column=col,
                    issue_type="MISSING_DESCRIPTION",
                    current_value="Empty",
                    suggested_action=f"Provide {col.lower()} information"
                ))
        
        logger.info(f"✅ Processed yarn inventory data: {len(df)} yarns")
        return df
    
    def standardize_yarn_specifications(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize yarn specifications for consistency"""
        logger.info("🔍 Standardizing Yarn Specifications...")
        
        # Standardize blend percentages
        blend_patterns = {
            r'(\d+)/(\d+)': r'\1/\2',  # Ensure consistent format
            r'100%': '100%',
            r'(\d+)%': r'\1%'
        }
        
        # Standardize material types
        material_standardization = {
            'Polyester/Recycled Cotton': 'Polyester/Recycled Cotton',
            'Polyester/Cotton': 'Polyester/Cotton',
            'Combed Cotton/Poly': 'Cotton/Polyester',
            'Karded Cotton/Poly': 'Cotton/Polyester',
            'Cotton/Poly': 'Cotton/Polyester'
        }
        
        # Apply standardization
        for old_type, new_type in material_standardization.items():
            df.loc[df['Type'] == old_type, 'Type'] = new_type
        
        # Check for non-standard material types
        unique_types = df['Type'].unique()
        standard_types = set(material_standardization.values())
        standard_types.update(['Polyester', 'Cotton', 'Polyethylene', 'Polypropylene', 
                              'Rayon', 'Tencel', 'Bamboo', 'Lurex', 'Modacrylic/Fiberglass'])
        
        non_standard_types = [t for t in unique_types if t not in standard_types and pd.notna(t)]
        if non_standard_types:
            logger.info(f"⚠️  Found non-standard material types: {non_standard_types}")
            for yarn_type in non_standard_types:
                affected_yarns = df[df['Type'] == yarn_type]
                for _, row in affected_yarns.iterrows():
                    self.quality_issues.append(DataQualityIssue(
                        file_name="Yarn_ID_1.csv",
                        row_index=row.name,
                        column="Type",
                        issue_type="NON_STANDARD_TYPE",
                        current_value=yarn_type,
                        suggested_action="Standardize material type"
                    ))
        
        logger.info(f"✅ Standardized yarn specifications")
        return df
    
    def find_interchangeable_yarns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Find yarns with same specifications that are interchangeable"""
        logger.info("🔍 Finding Interchangeable Yarns...")
        
        # Group by key specifications
        spec_columns = ['Description', 'Blend', 'Type', 'Color']
        
        # Create specification key
        df['spec_key'] = df[spec_columns].fillna('').apply(
            lambda x: '|'.join(x.astype(str)), axis=1
        )
        
        # Find groups with multiple yarns
        interchangeable_groups = {}
        spec_groups = df.groupby('spec_key')
        
        for spec_key, group in spec_groups:
            if len(group) > 1:
                yarn_ids = group['Yarn_ID'].tolist()
                suppliers = group['Supplier'].tolist()
                
                # Create a readable group name
                first_yarn = group.iloc[0]
                group_name = f"{first_yarn['Description']}_{first_yarn['Type']}_{first_yarn['Color']}"
                group_name = re.sub(r'[^\w\-_]', '_', group_name)
                
                interchangeable_groups[group_name] = {
                    'yarn_ids': yarn_ids,
                    'suppliers': suppliers,
                    'specifications': {
                        'description': first_yarn['Description'],
                        'blend': first_yarn['Blend'],
                        'type': first_yarn['Type'],
                        'color': first_yarn['Color']
                    }
                }
                
                logger.info(f"   📦 {group_name}: {len(yarn_ids)} interchangeable yarns")
        
        logger.info(f"✅ Found {len(interchangeable_groups)} interchangeable yarn groups")
        return interchangeable_groups
    
    def validate_bom_data(self, bom_df: pd.DataFrame, yarn_df: pd.DataFrame) -> pd.DataFrame:
        """Validate BOM data against yarn master data"""
        logger.info("🔍 Validating BOM Data...")
        
        # Check for missing yarn IDs in BOM
        yarn_ids_in_master = set(yarn_df['Yarn_ID'].astype(str))
        yarn_ids_in_bom = set(bom_df['Yarn_ID'].astype(str))
        
        missing_yarns = yarn_ids_in_bom - yarn_ids_in_master
        if missing_yarns:
            logger.info(f"⚠️  Found {len(missing_yarns)} yarn IDs in BOM not in master data:")
            for yarn_id in list(missing_yarns)[:10]:  # Show first 10
                affected_styles = bom_df[bom_df['Yarn_ID'].astype(str) == yarn_id]['Style_ID'].tolist()
                logger.info(f"   - Yarn {yarn_id} used in styles: {affected_styles[:3]}...")
                self.quality_issues.append(DataQualityIssue(
                    file_name="Style_BOM.csv",
                    row_index=-1,
                    column="Yarn_ID",
                    issue_type="MISSING_YARN_MASTER",
                    current_value=yarn_id,
                    suggested_action="Add yarn to master data or remove from BOM"
                ))
        
        # Check BOM percentage totals by style
        style_totals = bom_df.groupby('Style_ID')['BOM_Percentage'].sum()
        incorrect_totals = style_totals[abs(style_totals - 1.0) > 0.001]
        
        if not incorrect_totals.empty:
            logger.info(f"⚠️  Found {len(incorrect_totals)} styles with incorrect BOM percentages:")
            for style_id, total in incorrect_totals.head(10).items():
                logger.info(f"   - Style {style_id}: Total = {total:.3f}")
                self.quality_issues.append(DataQualityIssue(
                    file_name="Style_BOM.csv",
                    row_index=-1,
                    column="BOM_Percentage",
                    issue_type="INCORRECT_BOM_TOTAL",
                    current_value=f"{total:.3f}",
                    suggested_action="BOM percentages should sum to 1.0"
                ))
        
        logger.info(f"✅ Validated BOM data: {len(bom_df)} BOM lines for {bom_df['Style_ID'].nunique()} styles")
        return bom_df
    
    def generate_quality_report(self) -> str:
        """Generate a comprehensive data quality report"""
        report = []
        report.append("=" * 60)
        report.append("BEVERLY KNITS DATA QUALITY REPORT")
        report.append("=" * 60)
        report.append(f"Total Issues Found: {len(self.quality_issues)}")
        report.append("")
        
        # Group issues by type
        issues_by_type = {}
        for issue in self.quality_issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        for issue_type, issues in issues_by_type.items():
            report.append(f"🔍 {issue_type.replace('_', ' ').title()}: {len(issues)} issues")
            for issue in issues[:5]:  # Show first 5 of each type
                report.append(f"   📁 {issue.file_name}")
                report.append(f"   📍 Row {issue.row_index}, Column: {issue.column}")
                report.append(f"   ❌ Current: {issue.current_value}")
                report.append(f"   ✅ Action: {issue.suggested_action}")
                report.append("")
            
            if len(issues) > 5:
                report.append(f"   ... and {len(issues) - 5} more similar issues")
                report.append("")
        
        return "\n".join(report)
    
    def create_integrated_datasets(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Create integrated datasets for the planning system"""
        logger.info("🔧 Creating Integrated Datasets...")
        
        # Merge yarn specs with inventory data
        yarn_master = pd.merge(
            data['yarn_specs'], 
            data['yarn_inventory'], 
            on='Yarn_ID', 
            how='outer',
            suffixes=('_spec', '_inv')
        )
        
        # Clean up duplicate columns
        for col in ['Supplier', 'Description', 'Blend', 'Type', 'Color', 'Desc_1', 'Desc_2', 'Desc_3']:
            if f"{col}_spec" in yarn_master.columns and f"{col}_inv" in yarn_master.columns:
                # Use inventory version if available, otherwise spec version
                yarn_master[col] = yarn_master[f"{col}_inv"].fillna(yarn_master[f"{col}_spec"])
                yarn_master.drop([f"{col}_spec", f"{col}_inv"], axis=1, inplace=True)
        
        # Create supplier mapping
        supplier_mapping = data['suppliers'].set_index('Supplier')['Supplier_ID'].to_dict()
        
        # Add supplier IDs to yarn master
        yarn_master['Supplier_ID'] = yarn_master['Supplier'].map(supplier_mapping)
        
        # Create materials dataset (for planning system)
        materials = yarn_master[['Yarn_ID', 'Supplier', 'Supplier_ID', 'Description', 
                                'Blend', 'Type', 'Color', 'Cost_Pound']].copy()
        materials.rename(columns={'Yarn_ID': 'material_id', 'Cost_Pound': 'cost_per_unit'}, inplace=True)
        
        # Create inventory dataset
        inventory = yarn_master[['Yarn_ID', 'Inventory', 'On_Order', 'Allocated', 'Planning_Ballance']].copy()
        inventory.rename(columns={
            'Yarn_ID': 'material_id',
            'Inventory': 'current_stock',
            'On_Order': 'incoming_stock',
            'Allocated': 'allocated_stock',
            'Planning_Ballance': 'available_stock'
        }, inplace=True)
        
        # Create suppliers dataset for planning system
        suppliers_clean = data['suppliers'][data['suppliers']['Lead_time'] != 'Remove'].copy()
        suppliers_for_planning = []
        
        for _, supplier_row in suppliers_clean.iterrows():
            # Get all yarns for this supplier
            supplier_yarns = yarn_master[yarn_master['Supplier'] == supplier_row['Supplier']]
            
            for _, yarn_row in supplier_yarns.iterrows():
                if pd.notna(yarn_row['Cost_Pound']) and yarn_row['Cost_Pound'] > 0:
                    suppliers_for_planning.append({
                        'material_id': yarn_row['Yarn_ID'],
                        'supplier_id': supplier_row['Supplier'],
                        'cost_per_unit': yarn_row['Cost_Pound'],
                        'lead_time_days': supplier_row['Lead_time'],
                        'moq': supplier_row['MOQ'],
                        'reliability_score': 0.85,  # Default value
                        'supplier_type': supplier_row['Type']
                    })
        
        suppliers_df = pd.DataFrame(suppliers_for_planning)
        
        # Create BOMs dataset
        boms = data['bom'].copy()
        boms.rename(columns={
            'Style_ID': 'sku_id',
            'Yarn_ID': 'material_id',
            'BOM_Percentage': 'quantity_per_unit'
        }, inplace=True)
        
        integrated_data = {
            'yarn_master': yarn_master,
            'materials': materials,
            'inventory': inventory,
            'suppliers': suppliers_df,
            'boms': boms,
            'supplier_master': suppliers_clean
        }
        
        logger.info("✅ Created integrated datasets")
        return integrated_data

def main():
    """Main integration function"""
    logger.info("🚀 Starting Beverly Knits Data Integration...")
    
    integrator = BeverlyKnitsDataIntegrator()
    
    # Load all data
    raw_data = integrator.load_all_data()
    logger.info(f"📊 Loaded {len(raw_data)} data files")
    
    # Validate and clean data
    raw_data['suppliers'] = integrator.validate_supplier_data(raw_data['suppliers'])
    raw_data['yarn_inventory'] = integrator.validate_yarn_inventory_data(raw_data['yarn_inventory'])
    raw_data['yarn_specs'] = integrator.standardize_yarn_specifications(raw_data['yarn_specs'])
    raw_data['bom'] = integrator.validate_bom_data(raw_data['bom'], raw_data['yarn_inventory'])
    
    # Find interchangeable yarns
    interchangeable_groups = integrator.find_interchangeable_yarns(raw_data['yarn_specs'])
    
    # Create integrated datasets
    integrated_data = integrator.create_integrated_datasets(raw_data)
    
    # Generate quality report
    quality_report = integrator.generate_quality_report()
    
    # Save quality report
    with open('data/data_quality_report.txt', 'w', encoding='utf-8') as f:
        f.write(quality_report)
    
    # Save integrated datasets
    for name, df in integrated_data.items():
        if isinstance(df, pd.DataFrame):
            df.to_csv(f'data/integrated_{name}.csv', index=False)
            logger.info(f"💾 Saved integrated_{name}.csv ({len(df)} records)")
    
    # Save interchangeable groups
    import json
    with open('data/interchangeable_yarns.json', 'w') as f:
        json.dump(interchangeable_groups, f, indent=2)
    
    logger.info("\n" + quality_report)
    logger.info(f"\n🎯 Integration complete! Found {len(interchangeable_groups)} interchangeable yarn groups")
    logger.info("📋 Check data_quality_report.txt for detailed issues to address")

if __name__ == "__main__":
    main()