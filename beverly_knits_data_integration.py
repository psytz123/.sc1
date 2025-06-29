"""
Beverly Knits Data Integration Module
=====================================
This module provides comprehensive data integration for all CSV files
in the Beverly Knits raw material planning system.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class BeverlyKnitsDataIntegrator:
    """Main class for integrating all Beverly Knits data sources"""
    
    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        self.data = {}
        self.integrated_data = {}
        
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files into memory"""
        print("Loading all data files...")
        
        # Define file mappings
        file_mappings = {
            'sales_orders': 'eFab_SO_List.csv',
            'yarn_demand_by_style': 'cfab_Yarn_Demand_By_Style.csv',
            'style_bom': 'Style_BOM.csv',
            'yarn_master': 'Yarn_ID.csv',
            'yarn_inventory': 'Yarn_ID_Current_Inventory.csv',
            'inventory_upload': 'upload_ready/inventory.csv',
            'suppliers': 'Supplier_ID.csv',
            'yarn_demand_weekly': 'Yarn_Demand_2025-06-27_0442.csv',
            'sales_history': 'Sales Activity Report.csv'
        }
        
        # Load each file
        for key, filename in file_mappings.items():
            try:
                filepath = f"{self.data_path}{filename}"
                self.data[key] = pd.read_csv(filepath)
                print(f"✓ Loaded {key}: {len(self.data[key])} rows")
            except Exception as e:
                print(f"✗ Error loading {key}: {str(e)}")
                
        return self.data
    
    def clean_and_standardize_data(self):
        """Clean and standardize all loaded data"""
        print("\nCleaning and standardizing data...")
        
        # Clean suppliers data
        if 'suppliers' in self.data:
            df = self.data['suppliers']
            # Remove rows with "Remove" values
            df = df[df['Lead_time'] != 'Remove']
            df['Lead_time'] = pd.to_numeric(df['Lead_time'], errors='coerce')
            df['MOQ'] = pd.to_numeric(df['MOQ'], errors='coerce')
            self.data['suppliers'] = df
            
        # Standardize yarn IDs across all files
        yarn_id_columns = {
            'yarn_demand_by_style': 'Yarn',
            'style_bom': 'Yarn_ID',
            'yarn_master': 'Yarn_ID',
            'yarn_inventory': 'Yarn_ID',
            'inventory_upload': 'material_id',
            'yarn_demand_weekly': 'Yarn_ID'
        }
        
        for key, col in yarn_id_columns.items():
            if key in self.data and col in self.data[key].columns:
                self.data[key][col] = pd.to_numeric(self.data[key][col], errors='coerce')
                
        # Standardize style IDs
        if 'sales_orders' in self.data:
            # Extract style from cFVersion (remove version suffix)
            self.data['sales_orders']['Style_ID'] = self.data['sales_orders']['cFVersion'].str.split('-').str[0]
            
        print("✓ Data cleaning completed")
        
    def create_integrated_yarn_master(self) -> pd.DataFrame:
        """Create a unified yarn master table combining all yarn information"""
        print("\nCreating integrated yarn master...")
        
        # Start with yarn master data
        yarn_master = self.data['yarn_master'].copy()
        
        # Merge with current inventory
        if 'yarn_inventory' in self.data:
            inventory_cols = ['Yarn_ID', 'Inventory', 'On_Order', 'Allocated', 
                            'Planning_Ballance', 'Cost_Pound', 'Total_Cost']
            yarn_inventory = self.data['yarn_inventory'][inventory_cols].copy()
            yarn_inventory.columns = ['Yarn_ID', 'Current_Inventory', 'Current_On_Order', 
                                    'Current_Allocated', 'Current_Planning_Balance', 
                                    'Current_Cost_Pound', 'Current_Total_Cost']
            
            yarn_master = yarn_master.merge(yarn_inventory, on='Yarn_ID', how='left')
            
        # Merge with simplified inventory
        if 'inventory_upload' in self.data:
            inv_upload = self.data['inventory_upload'].copy()
            inv_upload.columns = ['Yarn_ID', 'Upload_On_Hand', 'Unit', 'Upload_Open_PO', 'PO_Expected_Date']
            yarn_master = yarn_master.merge(inv_upload, on='Yarn_ID', how='left')
            
        # Add supplier information
        if 'suppliers' in self.data:
            supplier_info = self.data['suppliers'][['Supplier', 'Lead_time', 'MOQ', 'Type']].copy()
            supplier_info.columns = ['Supplier', 'Supplier_Lead_Time', 'Supplier_MOQ', 'Supplier_Type']
            yarn_master = yarn_master.merge(supplier_info, on='Supplier', how='left')
            
        self.integrated_data['yarn_master'] = yarn_master
        print(f"✓ Created integrated yarn master with {len(yarn_master)} yarns")
        return yarn_master
    
    def calculate_total_yarn_demand(self) -> pd.DataFrame:
        """Calculate total yarn demand from sales orders and BOM"""
        print("\nCalculating total yarn demand...")
        
        # Get active sales orders
        sales_orders = self.data['sales_orders'].copy()
        
        # Extract numeric quantity from 'Ordered' column
        sales_orders['Quantity'] = pd.to_numeric(sales_orders['Ordered'], errors='coerce')
        
        # Group by style
        style_demand = sales_orders.groupby('Style_ID')['Quantity'].sum().reset_index()
        
        # Explode BOM to get yarn requirements
        bom = self.data['style_bom'].copy()
        
        # Merge style demand with BOM
        yarn_demand = style_demand.merge(bom, on='Style_ID', how='inner')
        
        # Calculate yarn quantity needed
        yarn_demand['Yarn_Quantity_Required'] = yarn_demand['Quantity'] * yarn_demand['BOM_Percentage']
        
        # Aggregate by yarn
        total_yarn_demand = yarn_demand.groupby('Yarn_ID')['Yarn_Quantity_Required'].sum().reset_index()
        total_yarn_demand.columns = ['Yarn_ID', 'Total_Demand_From_Orders']
        
        # Add demand from yarn_demand_by_style file
        if 'yarn_demand_by_style' in self.data:
            style_yarn_demand = self.data['yarn_demand_by_style'].copy()
            style_yarn_demand['Total'] = pd.to_numeric(
                style_yarn_demand['Total'].str.replace(',', ''), errors='coerce'
            )
            
            style_demand_summary = style_yarn_demand.groupby('Yarn')['Total'].sum().reset_index()
            style_demand_summary.columns = ['Yarn_ID', 'Total_Demand_From_Forecast']
            
            # Merge both demand sources
            total_yarn_demand = total_yarn_demand.merge(
                style_demand_summary, on='Yarn_ID', how='outer'
            ).fillna(0)
            
            # Take the maximum of both sources (conservative approach)
            total_yarn_demand['Total_Demand'] = total_yarn_demand[
                ['Total_Demand_From_Orders', 'Total_Demand_From_Forecast']
            ].max(axis=1)
            
        self.integrated_data['total_yarn_demand'] = total_yarn_demand
        print(f"✓ Calculated demand for {len(total_yarn_demand)} yarns")
        return total_yarn_demand
    
    def calculate_net_requirements(self) -> pd.DataFrame:
        """Calculate net requirements considering inventory and on-order quantities"""
        print("\nCalculating net requirements...")
        
        # Get integrated yarn master and total demand
        yarn_master = self.integrated_data.get('yarn_master', self.create_integrated_yarn_master())
        total_demand = self.integrated_data.get('total_yarn_demand', self.calculate_total_yarn_demand())
        
        # Merge demand with inventory
        net_req = total_demand.merge(
            yarn_master[['Yarn_ID', 'Current_Inventory', 'Current_On_Order', 
                        'Supplier', 'Supplier_Lead_Time', 'Supplier_MOQ', 
                        'Current_Cost_Pound', 'Description', 'Blend', 'Type']],
            on='Yarn_ID',
            how='left'
        )
        
        # Fill missing values
        net_req['Current_Inventory'] = net_req['Current_Inventory'].fillna(0)
        net_req['Current_On_Order'] = net_req['Current_On_Order'].fillna(0)
        
        # Calculate net requirement
        net_req['Available_Supply'] = net_req['Current_Inventory'] + net_req['Current_On_Order']
        net_req['Net_Requirement'] = net_req['Total_Demand'] - net_req['Available_Supply']
        net_req['Net_Requirement'] = net_req['Net_Requirement'].clip(lower=0)
        
        # Apply safety stock (20% buffer)
        net_req['Safety_Stock'] = net_req['Total_Demand'] * 0.2
        net_req['Net_Requirement_With_Safety'] = net_req['Net_Requirement'] + net_req['Safety_Stock']
        
        # Apply MOQ constraints
        net_req['Order_Quantity'] = net_req.apply(
            lambda row: self._apply_moq(row['Net_Requirement_With_Safety'], row['Supplier_MOQ']),
            axis=1
        )
        
        # Calculate order value
        net_req['Order_Value'] = net_req['Order_Quantity'] * net_req['Current_Cost_Pound']
        
        # Add urgency indicator based on lead time
        net_req['Days_Until_Needed'] = 14  # Default 2 weeks
        net_req['Urgency'] = net_req.apply(
            lambda row: self._calculate_urgency(row['Days_Until_Needed'], row['Supplier_Lead_Time']),
            axis=1
        )
        
        self.integrated_data['net_requirements'] = net_req
        print(f"✓ Calculated net requirements for {len(net_req)} yarns")
        return net_req
    
    def generate_procurement_plan(self) -> pd.DataFrame:
        """Generate final procurement recommendations"""
        print("\nGenerating procurement plan...")
        
        net_req = self.integrated_data.get('net_requirements', self.calculate_net_requirements())
        
        # Filter only items that need ordering
        procurement = net_req[net_req['Order_Quantity'] > 0].copy()
        
        # Sort by urgency and value
        procurement['Priority_Score'] = (
            procurement['Urgency'].map({'Critical': 3, 'High': 2, 'Medium': 1, 'Low': 0}) * 
            procurement['Order_Value']
        )
        
        procurement = procurement.sort_values('Priority_Score', ascending=False)
        
        # Select key columns for output
        output_columns = [
            'Yarn_ID', 'Description', 'Blend', 'Type', 'Supplier',
            'Total_Demand', 'Current_Inventory', 'Current_On_Order',
            'Net_Requirement', 'Safety_Stock', 'Order_Quantity',
            'Supplier_MOQ', 'Supplier_Lead_Time', 'Current_Cost_Pound',
            'Order_Value', 'Urgency'
        ]
        
        procurement_plan = procurement[output_columns].copy()
        
        # Add order date recommendation
        procurement_plan['Recommended_Order_Date'] = pd.Timestamp.now().date()
        procurement_plan['Expected_Delivery_Date'] = procurement_plan.apply(
            lambda row: pd.Timestamp.now().date() + timedelta(days=int(row['Supplier_Lead_Time'] or 14)),
            axis=1
        )
        
        self.integrated_data['procurement_plan'] = procurement_plan
        print(f"✓ Generated procurement plan with {len(procurement_plan)} purchase recommendations")
        
        # Summary statistics
        total_value = procurement_plan['Order_Value'].sum()
        critical_items = len(procurement_plan[procurement_plan['Urgency'] == 'Critical'])
        
        print(f"\nProcurement Summary:")
        print(f"- Total items to order: {len(procurement_plan)}")
        print(f"- Total order value: ${total_value:,.2f}")
        print(f"- Critical items: {critical_items}")
        
        return procurement_plan
    
    def create_weekly_demand_analysis(self) -> pd.DataFrame:
        """Create time-phased demand analysis"""
        print("\nCreating weekly demand analysis...")
        
        if 'yarn_demand_by_style' not in self.data:
            print("✗ Weekly demand data not available")
            return pd.DataFrame()
            
        demand_data = self.data['yarn_demand_by_style'].copy()
        
        # Extract week columns
        week_columns = [col for col in demand_data.columns if col.startswith('Week') or col == 'This Week']
        
        # Melt the data to long format
        demand_long = demand_data.melt(
            id_vars=['Style', 'Yarn', 'Percentage'],
            value_vars=week_columns,
            var_name='Week',
            value_name='Demand'
        )
        
        # Clean demand values
        demand_long['Demand'] = pd.to_numeric(
            demand_long['Demand'].astype(str).str.replace(',', ''), 
            errors='coerce'
        ).fillna(0)
        
        # Aggregate by yarn and week
        weekly_demand = demand_long.groupby(['Yarn', 'Week'])['Demand'].sum().reset_index()
        weekly_demand.columns = ['Yarn_ID', 'Week', 'Weekly_Demand']
        
        # Pivot back to wide format
        weekly_pivot = weekly_demand.pivot(index='Yarn_ID', columns='Week', values='Weekly_Demand').fillna(0)
        
        # Add yarn information
        yarn_info = self.integrated_data.get('yarn_master', pd.DataFrame())
        if not yarn_info.empty:
            weekly_analysis = weekly_pivot.merge(
                yarn_info[['Yarn_ID', 'Description', 'Supplier', 'Current_Inventory']],
                on='Yarn_ID',
                how='left'
            )
        else:
            weekly_analysis = weekly_pivot
            
        self.integrated_data['weekly_demand_analysis'] = weekly_analysis
        print(f"✓ Created weekly demand analysis for {len(weekly_analysis)} yarns")
        return weekly_analysis
    
    def _apply_moq(self, quantity: float, moq: float) -> float:
        """Apply minimum order quantity constraint"""
        if pd.isna(moq) or moq == 0:
            return quantity
        if quantity == 0:
            return 0
        return max(moq, np.ceil(quantity / moq) * moq)
    
    def _calculate_urgency(self, days_until_needed: int, lead_time: float) -> str:
        """Calculate urgency based on lead time"""
        if pd.isna(lead_time):
            lead_time = 14  # Default 2 weeks
            
        buffer_days = days_until_needed - lead_time
        
        if buffer_days <= 0:
            return 'Critical'
        elif buffer_days <= 7:
            return 'High'
        elif buffer_days <= 14:
            return 'Medium'
        else:
            return 'Low'
    
    def export_integrated_data(self, output_path: str = "output/"):
        """Export all integrated data to CSV files"""
        print(f"\nExporting integrated data to {output_path}...")
        
        import os
        os.makedirs(output_path, exist_ok=True)
        
        export_mappings = {
            'integrated_yarn_master.csv': 'yarn_master',
            'total_yarn_demand.csv': 'total_yarn_demand',
            'net_requirements.csv': 'net_requirements',
            'procurement_plan.csv': 'procurement_plan',
            'weekly_demand_analysis.csv': 'weekly_demand_analysis'
        }
        
        for filename, data_key in export_mappings.items():
            if data_key in self.integrated_data:
                filepath = f"{output_path}{filename}"
                self.integrated_data[data_key].to_csv(filepath, index=False)
                print(f"✓ Exported {filename}")
                
    def run_full_integration(self):
        """Run the complete data integration process"""
        print("="*60)
        print("Beverly Knits Data Integration Process")
        print("="*60)
        
        # Load all data
        self.load_all_data()
        
        # Clean and standardize
        self.clean_and_standardize_data()
        
        # Create integrated datasets
        self.create_integrated_yarn_master()
        self.calculate_total_yarn_demand()
        self.calculate_net_requirements()
        self.generate_procurement_plan()
        self.create_weekly_demand_analysis()
        
        # Export results
        self.export_integrated_data()
        
        print("\n✓ Data integration completed successfully!")
        return self.integrated_data


# Example usage
if __name__ == "__main__":
    # Initialize the integrator
    integrator = BeverlyKnitsDataIntegrator(data_path="data/")
    
    # Run full integration
    integrated_data = integrator.run_full_integration()
    
    # Display sample results
    if 'procurement_plan' in integrated_data:
        print("\nTop 10 Procurement Recommendations:")
        print(integrated_data['procurement_plan'].head(10))