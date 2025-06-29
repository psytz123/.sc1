"""
Beverly Knits Raw Material Planning System
==========================================
Main script demonstrating complete data integration and planning
"""

import pandas as pd
import numpy as np
from datetime import datetime
from beverly_knits_data_integration import BeverlyKnitsDataIntegrator
import warnings
warnings.filterwarnings('ignore')


def main():
    """Main function to run the complete raw material planning process"""
    
    print("="*70)
    print("BEVERLY KNITS RAW MATERIAL PLANNING SYSTEM")
    print("="*70)
    print(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Initialize the data integrator
    print("\n1. INITIALIZING DATA INTEGRATION...")
    integrator = BeverlyKnitsDataIntegrator(data_path="data/")
    
    # Load all data files
    print("\n2. LOADING DATA FILES...")
    data = integrator.load_all_data()
    
    # Clean and standardize data
    print("\n3. CLEANING AND STANDARDIZING DATA...")
    integrator.clean_and_standardize_data()
    
    # Create integrated datasets
    print("\n4. CREATING INTEGRATED DATASETS...")
    
    # Integrated yarn master
    yarn_master = integrator.create_integrated_yarn_master()
    print(f"\n   Integrated Yarn Master Summary:")
    print(f"   - Total yarns: {len(yarn_master)}")
    print(f"   - Yarns with inventory: {(yarn_master['Current_Inventory'] > 0).sum()}")
    print(f"   - Yarns on order: {(yarn_master['Current_On_Order'] > 0).sum()}")
    
    # Calculate total demand
    total_demand = integrator.calculate_total_yarn_demand()
    print(f"\n   Total Yarn Demand Summary:")
    print(f"   - Yarns with demand: {len(total_demand)}")
    print(f"   - Total demand quantity: {total_demand['Total_Demand'].sum():,.0f} lbs")
    
    # Calculate net requirements
    net_requirements = integrator.calculate_net_requirements()
    print(f"\n   Net Requirements Summary:")
    print(f"   - Yarns needing orders: {(net_requirements['Net_Requirement'] > 0).sum()}")
    print(f"   - Total net requirement: {net_requirements['Net_Requirement'].sum():,.0f} lbs")
    
    # Generate procurement plan
    print("\n5. GENERATING PROCUREMENT PLAN...")
    procurement_plan = integrator.generate_procurement_plan()
    
    # Display key metrics
    print("\n6. KEY METRICS AND INSIGHTS")
    print("="*70)
    
    # Procurement summary by urgency
    if not procurement_plan.empty:
        urgency_summary = procurement_plan.groupby('Urgency').agg({
            'Yarn_ID': 'count',
            'Order_Quantity': 'sum',
            'Order_Value': 'sum'
        }).round(2)
        urgency_summary.columns = ['Count', 'Total Quantity', 'Total Value']
        
        print("\n   Procurement Summary by Urgency:")
        print(urgency_summary.to_string(float_format='%.2f'))
        
        # Top 10 orders by value
        print("\n   Top 10 Orders by Value:")
        top_orders = procurement_plan.nlargest(10, 'Order_Value')[
            ['Yarn_ID', 'Description', 'Supplier', 'Order_Quantity', 'Order_Value', 'Urgency']
        ]
        print(top_orders.to_string(index=False, float_format='%.2f'))
        
        # Supplier summary
        supplier_summary = procurement_plan.groupby('Supplier').agg({
            'Yarn_ID': 'count',
            'Order_Value': 'sum'
        }).round(2)
        supplier_summary.columns = ['Order Count', 'Total Value']
        supplier_summary = supplier_summary.sort_values('Total Value', ascending=False).head(10)
        
        print("\n   Top 10 Suppliers by Order Value:")
        print(supplier_summary.to_string(float_format='%.2f'))
    
    # Weekly demand analysis
    print("\n7. WEEKLY DEMAND ANALYSIS...")
    weekly_analysis = integrator.create_weekly_demand_analysis()
    
    # Export all results
    print("\n8. EXPORTING RESULTS...")
    integrator.export_integrated_data()
    
    # Generate summary report
    generate_summary_report(integrator)
    
    print("\n" + "="*70)
    print("PLANNING PROCESS COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nOutput files generated:")
    print("  - output/integrated_yarn_master.csv")
    print("  - output/total_yarn_demand.csv")
    print("  - output/net_requirements.csv")
    print("  - output/procurement_plan.csv")
    print("  - output/weekly_demand_analysis.csv")
    print("  - planning_summary_report.txt")
    

def generate_summary_report(integrator):
    """Generate a comprehensive summary report"""
    
    report_lines = []
    report_lines.append("="*70)
    report_lines.append("BEVERLY KNITS RAW MATERIAL PLANNING SUMMARY REPORT")
    report_lines.append("="*70)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Data loading summary
    report_lines.append("1. DATA LOADING SUMMARY")
    report_lines.append("-" * 30)
    for key, df in integrator.data.items():
        report_lines.append(f"   {key}: {len(df)} rows")
    
    # Integration summary
    report_lines.append("\n2. INTEGRATION SUMMARY")
    report_lines.append("-" * 30)
    
    if 'yarn_master' in integrator.integrated_data:
        yarn_master = integrator.integrated_data['yarn_master']
        report_lines.append(f"   Total unique yarns: {len(yarn_master)}")
        report_lines.append(f"   Yarns with valid suppliers: {yarn_master['Supplier'].notna().sum()}")
        report_lines.append(f"   Average cost per pound: ${yarn_master['Current_Cost_Pound'].mean():.2f}")
    
    # Demand summary
    if 'total_yarn_demand' in integrator.integrated_data:
        demand = integrator.integrated_data['total_yarn_demand']
        report_lines.append(f"\n3. DEMAND SUMMARY")
        report_lines.append("-" * 30)
        report_lines.append(f"   Yarns with demand: {len(demand)}")
        report_lines.append(f"   Total demand: {demand['Total_Demand'].sum():,.0f} lbs")
        
        # Top 5 yarns by demand
        top_demand = demand.nlargest(5, 'Total_Demand')
        report_lines.append("\n   Top 5 Yarns by Demand:")
        for _, row in top_demand.iterrows():
            report_lines.append(f"   - Yarn {int(row['Yarn_ID'])}: {row['Total_Demand']:,.0f} lbs")
    
    # Procurement summary
    if 'procurement_plan' in integrator.integrated_data:
        proc = integrator.integrated_data['procurement_plan']
        report_lines.append(f"\n4. PROCUREMENT SUMMARY")
        report_lines.append("-" * 30)
        report_lines.append(f"   Total purchase orders: {len(proc)}")
        report_lines.append(f"   Total order value: ${proc['Order_Value'].sum():,.2f}")
        report_lines.append(f"   Average order value: ${proc['Order_Value'].mean():,.2f}")
        
        # Urgency breakdown
        urgency_counts = proc['Urgency'].value_counts()
        report_lines.append("\n   Orders by Urgency:")
        for urgency, count in urgency_counts.items():
            report_lines.append(f"   - {urgency}: {count}")
    
    # Risk analysis
    report_lines.append(f"\n5. RISK ANALYSIS")
    report_lines.append("-" * 30)
    
    if 'net_requirements' in integrator.integrated_data:
        net_req = integrator.integrated_data['net_requirements']
        
        # Yarns with no supplier
        no_supplier = net_req[net_req['Supplier'].isna() & (net_req['Net_Requirement'] > 0)]
        if len(no_supplier) > 0:
            report_lines.append(f"   ⚠ {len(no_supplier)} yarns need orders but have no supplier")
        
        # Critical items
        if 'procurement_plan' in integrator.integrated_data:
            critical = proc[proc['Urgency'] == 'Critical']
            if len(critical) > 0:
                report_lines.append(f"   ⚠ {len(critical)} critical orders need immediate attention")
                report_lines.append(f"      Total value at risk: ${critical['Order_Value'].sum():,.2f}")
    
    # Recommendations
    report_lines.append(f"\n6. RECOMMENDATIONS")
    report_lines.append("-" * 30)
    
    if 'procurement_plan' in integrator.integrated_data:
        # High value orders
        high_value = proc[proc['Order_Value'] > 10000]
        if len(high_value) > 0:
            report_lines.append(f"   • Review {len(high_value)} high-value orders (>${10000})")
        
        # Import vs domestic
        if 'Supplier_Type' in proc.columns:
            import_orders = proc[proc['Supplier_Type'] == 'Import']
            if len(import_orders) > 0:
                report_lines.append(f"   • {len(import_orders)} import orders - verify lead times")
        
        # Consolidation opportunities
        supplier_counts = proc['Supplier'].value_counts()
        multi_item_suppliers = supplier_counts[supplier_counts > 3]
        if len(multi_item_suppliers) > 0:
            report_lines.append(f"   • Consider consolidating orders for {len(multi_item_suppliers)} suppliers")
    
    # Write report
    with open('planning_summary_report.txt', 'w') as f:
        f.write('\n'.join(report_lines))
    
    print("\n✓ Summary report generated: planning_summary_report.txt")


def demonstrate_specific_queries():
    """Demonstrate specific data queries and analysis"""
    
    print("\n" + "="*70)
    print("DEMONSTRATION: SPECIFIC DATA QUERIES")
    print("="*70)
    
    integrator = BeverlyKnitsDataIntegrator(data_path="data/")
    integrator.load_all_data()
    integrator.clean_and_standardize_data()
    
    # Query 1: Find all yarns for a specific style
    print("\n1. Yarns required for style '125792/1':")
    if 'style_bom' in integrator.data:
        style_yarns = integrator.data['style_bom'][
            integrator.data['style_bom']['Style_ID'] == '125792/1'
        ]
        print(style_yarns[['Yarn_ID', 'BOM_Percentage']].to_string(index=False))
    
    # Query 2: Check inventory status for specific yarn
    print("\n2. Inventory status for Yarn 18767:")
    if 'yarn_inventory' in integrator.data:
        yarn_status = integrator.data['yarn_inventory'][
            integrator.data['yarn_inventory']['Yarn_ID'] == 18767
        ]
        if not yarn_status.empty:
            print(f"   Current Inventory: {yarn_status['Inventory'].iloc[0]}")
            print(f"   On Order: {yarn_status['On_Order'].iloc[0]}")
            print(f"   Planning Balance: {yarn_status['Planning_Ballance'].iloc[0]}")
    
    # Query 3: Supplier lead times
    print("\n3. Suppliers with shortest lead times:")
    if 'suppliers' in integrator.data:
        suppliers = integrator.data['suppliers'][
            integrator.data['suppliers']['Lead_time'] != 'Remove'
        ].copy()
        suppliers['Lead_time'] = pd.to_numeric(suppliers['Lead_time'])
        shortest_lead = suppliers.nsmallest(5, 'Lead_time')[
            ['Supplier', 'Lead_time', 'MOQ', 'Type']
        ]
        print(shortest_lead.to_string(index=False))


if __name__ == "__main__":
    # Run main planning process
    main()
    
    # Demonstrate specific queries
    demonstrate_specific_queries()