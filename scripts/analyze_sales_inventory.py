# import matplotlib.pyplot as plt
# import seaborn as sns
import warnings
from utils.logger import get_logger

logger = get_logger(__name__)
from datetime import datetime, timedelta

import pandas as pd

warnings.filterwarnings('ignore')

# Load the data files
logger.info("Loading data files...")
sales_df = pd.read_csv('data/Sales Activity Report.csv')
inventory_df = pd.read_csv('data/Inventory.csv')
orders_df = pd.read_csv('data/eFab_SO_List.csv')

# Clean and prepare the data
logger.info("\nCleaning and preparing data...")

# Sales data preparation
sales_df['Invoice Date'] = pd.to_datetime(sales_df['Invoice Date'])
sales_df['Yds_ordered'] = pd.to_numeric(sales_df['Yds_ordered'], errors='coerce')
sales_df['Unit Price'] = sales_df['Unit Price'].str.replace('$', '').str.replace(',', '').astype(float)
sales_df['Line Price'] = sales_df['Line Price'].str.replace('$', '').str.replace(',', '').astype(float)

# Inventory data preparation - handle non-numeric values
inventory_df['yds'] = pd.to_numeric(inventory_df['yds'].astype(str).str.replace(',', ''), errors='coerce')
inventory_df['lbs'] = pd.to_numeric(inventory_df['lbs'].astype(str).str.replace(',', ''), errors='coerce')
# Remove rows with NaN values in yds or lbs
inventory_df = inventory_df.dropna(subset=['yds'])

# Orders data preparation
orders_df['Ordered'] = pd.to_numeric(orders_df['Ordered'].astype(str).str.replace(',', ''), errors='coerce')
# Extract price from format like "$5.95 (yds)"
orders_df['Unit Price'] = orders_df['Unit Price'].astype(str).str.extract(r'\$([0-9.]+)')[0].astype(float)
orders_df['Quoted Date'] = pd.to_datetime(orders_df['Quoted Date'])

# Analysis 1: Sales Summary
logger.info("\n" + "="*60)
logger.info("SALES ACTIVITY ANALYSIS")
logger.info("="*60)

# Overall sales metrics
total_sales_value = sales_df['Line Price'].sum()
total_yards_sold = sales_df['Yds_ordered'].sum()
avg_price_per_yard = sales_df['Unit Price'].mean()
num_transactions = len(sales_df)
num_unique_customers = sales_df['Customer'].nunique()
num_unique_styles = sales_df['Style'].nunique()

logger.info(f"\nOverall Sales Metrics:")
logger.info(f"- Total Sales Value: ${total_sales_value:,.2f}")
logger.info(f"- Total Yards Sold: {total_yards_sold:,.0f} yards")
logger.info(f"- Average Price per Yard: ${avg_price_per_yard:.2f}")
logger.info(f"- Number of Transactions: {num_transactions:,}")
logger.info(f"- Unique Customers: {num_unique_customers}")
logger.info(f"- Unique Styles: {num_unique_styles}")

# Top customers by sales value
logger.info("\nTop 10 Customers by Sales Value:")
customer_sales = sales_df.groupby('Customer').agg({
    'Line Price': 'sum',
    'Yds_ordered': 'sum',
    'Document': 'count'
}).round(2)
customer_sales.columns = ['Total Sales ($)', 'Total Yards', 'Order Count']
customer_sales = customer_sales.sort_values('Total Sales ($)', ascending=False)
logger.info(customer_sales.head(10))

# Top selling styles
logger.info("\nTop 10 Selling Styles by Volume:")
style_sales = sales_df.groupby('Style').agg({
    'Yds_ordered': 'sum',
    'Line Price': 'sum',
    'Document': 'count'
}).round(2)
style_sales.columns = ['Total Yards', 'Total Sales ($)', 'Order Count']
style_sales = style_sales.sort_values('Total Yards', ascending=False)
logger.info(style_sales.head(10))

# Sales trend analysis
logger.info("\nMonthly Sales Trend:")
sales_df['Month'] = sales_df['Invoice Date'].dt.to_period('M')
monthly_sales = sales_df.groupby('Month').agg({
    'Line Price': 'sum',
    'Yds_ordered': 'sum'
}).round(2)
monthly_sales.columns = ['Sales ($)', 'Yards']
logger.info(monthly_sales)

# Analysis 2: Inventory Analysis
logger.info("\n" + "="*60)
logger.info("INVENTORY ANALYSIS")
logger.info("="*60)

# Inventory summary
total_inventory_yards = inventory_df['yds'].sum()
total_inventory_pounds = inventory_df['lbs'].sum()
num_styles_in_inventory = len(inventory_df)

logger.info(f"\nInventory Summary:")
logger.info(f"- Total Inventory: {total_inventory_yards:,.0f} yards")
logger.info(f"- Total Weight: {total_inventory_pounds:,.0f} lbs")
logger.info(f"- Number of Styles in Stock: {num_styles_in_inventory}")

# Top inventory items
logger.info("\nTop 10 Inventory Items by Yards:")
top_inventory = inventory_df.nlargest(10, 'yds')[['style_id', 'yds', 'lbs']]
logger.info(top_inventory)

# Analysis 3: Current Orders Analysis
logger.info("\n" + "="*60)
logger.info("CURRENT ORDERS ANALYSIS")
logger.info("="*60)

# Orders summary
total_orders_value = (orders_df['Ordered'] * orders_df['Unit Price']).sum()
total_orders_yards = orders_df['Ordered'].sum()
num_open_orders = len(orders_df[orders_df['Status'] == 'Open'])

logger.info(f"\nCurrent Orders Summary:")
logger.info(f"- Total Orders Value: ${total_orders_value:,.2f}")
logger.info(f"- Total Yards on Order: {total_orders_yards:,.0f} yards")
logger.info(f"- Number of Open Orders: {num_open_orders}")

# Top customers with pending orders
logger.info("\nTop Customers by Pending Order Volume:")
customer_orders = orders_df.groupby('Sold To').agg({
    'Ordered': 'sum',
    'Status': 'count'
}).round(2)
customer_orders.columns = ['Total Yards', 'Order Count']
customer_orders['Estimated Value'] = orders_df.groupby('Sold To').apply(
    lambda x: (x['Ordered'] * x['Unit Price']).sum()
).round(2)
customer_orders = customer_orders.sort_values('Total Yards', ascending=False)
logger.info(customer_orders.head(10))

# Analysis 4: Cross-Analysis - Matching Sales History with Current Inventory and Orders
logger.info("\n" + "="*60)
logger.info("INTEGRATED ANALYSIS")
logger.info("="*60)

# Find styles that appear in both sales history and current orders
sales_styles = set(sales_df['Style'].unique())
order_styles = set(orders_df['fBase'].str.split('/').str[0].unique())
inventory_styles = set(inventory_df['style_id'].str.split('/').str[0].unique())

common_sales_orders = sales_styles.intersection(order_styles)
common_sales_inventory = sales_styles.intersection(inventory_styles)

logger.info(f"\nStyle Overlap Analysis:")
logger.info(f"- Styles in sales history: {len(sales_styles)}")
logger.info(f"- Styles in current orders: {len(order_styles)}")
logger.info(f"- Styles in inventory: {len(inventory_styles)}")
logger.info(f"- Styles in both sales and orders: {len(common_sales_orders)}")
logger.info(f"- Styles in both sales and inventory: {len(common_sales_inventory)}")

# Demand vs Supply Analysis for common styles
logger.info("\nDemand vs Supply Analysis (Top 20 styles by sales):")
logger.info("Style | Historical Sales (yds) | Current Inventory (yds) | Pending Orders (yds)")
logger.info("-" * 80)

# Get top selling styles
top_selling_styles = sales_df.groupby('Style')['Yds_ordered'].sum().nlargest(20)

# Fill NaNs in 'fBase' to prevent errors
orders_df['fBase'] = orders_df['fBase'].fillna('')

for style in top_selling_styles.index:
    historical_sales = top_selling_styles[style]

    # Check inventory (accounting for style variations)
    inventory_match = inventory_df[inventory_df['style_id'].str.startswith(style)]
    current_inventory = inventory_match['yds'].sum() if not inventory_match.empty else 0

    # Check pending orders
    orders_match = orders_df[orders_df['fBase'].str.startswith(style)]
    pending_orders = orders_match['Ordered'].sum() if not orders_match.empty else 0

    logger.info(f"{style:<15} | {historical_sales:>20,.0f} | {current_inventory:>22,.0f} | {pending_orders:>18,.0f}")

# Analysis 5: Recommendations
logger.info("\n" + "="*60)
logger.info("RECOMMENDATIONS")
logger.info("="*60)

# Calculate average monthly demand for top styles
recent_sales = sales_df[sales_df['Invoice Date'] >= sales_df['Invoice Date'].max() - timedelta(days=90)]
avg_monthly_demand = recent_sales.groupby('Style')['Yds_ordered'].sum() / 3  # 3 months

logger.info("\nInventory Alerts (Styles with high demand but low inventory):")
logger.info("Style | Avg Monthly Demand | Current Inventory | Coverage (months)")
logger.info("-" * 70)

alerts = []
for style in avg_monthly_demand.nlargest(20).index:
    monthly_demand = avg_monthly_demand[style]
    
    # Check inventory
    inventory_match = inventory_df[inventory_df['style_id'].str.startswith(style)]
    current_inventory = inventory_match['yds'].sum() if not inventory_match.empty else 0
    
    # Calculate coverage
    coverage_months = current_inventory / monthly_demand if monthly_demand > 0 else float('inf')
    
    if coverage_months < 2:  # Less than 2 months coverage
        alerts.append({
            'style': style,
            'monthly_demand': monthly_demand,
            'inventory': current_inventory,
            'coverage': coverage_months
        })

# Sort by coverage (lowest first)
alerts.sort(key=lambda x: x['coverage'])
for alert in alerts[:10]:  # Show top 10 alerts
    logger.info(f"{alert['style']:<15} | {alert['monthly_demand']:>17,.0f} | {alert['inventory']:>16,.0f} | {alert['coverage']:>16.1f}")

# Save detailed reports
logger.info("\n" + "="*60)
logger.info("SAVING DETAILED REPORTS")
logger.info("="*60)

# Create summary report
summary_report = {
    'Report Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'Sales Summary': {
        'Total Sales Value': f"${total_sales_value:,.2f}",
        'Total Yards Sold': f"{total_yards_sold:,.0f}",
        'Average Price per Yard': f"${avg_price_per_yard:.2f}",
        'Number of Transactions': num_transactions,
        'Unique Customers': num_unique_customers,
        'Unique Styles': num_unique_styles
    },
    'Inventory Summary': {
        'Total Inventory (yards)': f"{total_inventory_yards:,.0f}",
        'Total Weight (lbs)': f"{total_inventory_pounds:,.0f}",
        'Number of Styles': num_styles_in_inventory
    },
    'Orders Summary': {
        'Total Orders Value': f"${total_orders_value:,.2f}",
        'Total Yards on Order': f"{total_orders_yards:,.0f}",
        'Open Orders': num_open_orders
    }
}

# Save summary to JSON
import json

with open('sales_inventory_summary.json', 'w') as f:
    json.dump(summary_report, f, indent=2)

# Save detailed alerts to CSV
alerts_df = pd.DataFrame(alerts)
if not alerts_df.empty:
    alerts_df.to_csv('inventory_alerts.csv', index=False)

logger.info("\nReports saved:")
logger.info("- sales_inventory_summary.json")
logger.info("- inventory_alerts.csv")

logger.info("\nAnalysis complete!")