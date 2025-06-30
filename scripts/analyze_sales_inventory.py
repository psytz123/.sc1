# import matplotlib.pyplot as plt
# import seaborn as sns
import warnings
import logging
from datetime import datetime, timedelta

import pandas as pd
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback to standard logging if custom logger not available
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

from models.sales_forecast_generator import SalesForecastGenerator
from models.forecast import FinishedGoodsForecast
from data.sales_data_processor import SalesDataProcessor
from config.settings import PlanningConfig

warnings.filterwarnings('ignore')

class SalesInventoryAnalyzer:
    """Enhanced sales and inventory analyzer with forecast generation and planner integration"""
    
    def __init__(self, config: PlanningConfig = None):
        """Initialize the analyzer with configuration"""
        self.config = config or PlanningConfig()
        self.sales_df = None
        self.inventory_df = None
        self.orders_df = None
        self.forecasts = []
        self.analysis_results = {}
        
    def load_data(self):
        """Load all required data files"""
        logger.info("Loading data files...")
        
        # Load sales data
        self.sales_df = pd.read_csv('data/Sales Activity Report.csv')
        self.sales_df['Invoice Date'] = pd.to_datetime(self.sales_df['Invoice Date'])
        self.sales_df['Yds_ordered'] = pd.to_numeric(self.sales_df['Yds_ordered'], errors='coerce')
        self.sales_df['Unit Price'] = self.sales_df['Unit Price'].str.replace('$', '').str.replace(',', '').astype(float)
        self.sales_df['Line Price'] = self.sales_df['Line Price'].str.replace('$', '').str.replace(',', '').astype(float)
        
        # Load inventory data
        self.inventory_df = pd.read_csv('data/Inventory.csv')
        self.inventory_df['yds'] = pd.to_numeric(self.inventory_df['yds'].astype(str).str.replace(',', ''), errors='coerce')
        self.inventory_df['lbs'] = pd.to_numeric(self.inventory_df['lbs'].astype(str).str.replace(',', ''), errors='coerce')
        self.inventory_df = self.inventory_df.dropna(subset=['yds'])
        
        # Load orders data
        self.orders_df = pd.read_csv('data/eFab_SO_List.csv')
        self.orders_df['Ordered'] = pd.to_numeric(self.orders_df['Ordered'].astype(str).str.replace(',', ''), errors='coerce')
        self.orders_df['Unit Price'] = self.orders_df['Unit Price'].astype(str).str.extract(r'\$([0-9.]+)')[0].astype(float)
        self.orders_df['Quoted Date'] = pd.to_datetime(self.orders_df['Quoted Date'])
        
        logger.info("Data files loaded successfully")
        
    def analyze_sales(self):
        """Perform comprehensive sales analysis"""
        logger.info("\n" + "="*60)
        logger.info("SALES ACTIVITY ANALYSIS")
        logger.info("="*60)
        
        # Overall sales metrics
        total_sales_value = self.sales_df['Line Price'].sum()
        total_yards_sold = self.sales_df['Yds_ordered'].sum()
        avg_price_per_yard = self.sales_df['Unit Price'].mean()
        num_transactions = len(self.sales_df)
        num_unique_customers = self.sales_df['Customer'].nunique()
        num_unique_styles = self.sales_df['Style'].nunique()
        
        self.analysis_results['sales_summary'] = {
            'total_sales_value': total_sales_value,
            'total_yards_sold': total_yards_sold,
            'avg_price_per_yard': avg_price_per_yard,
            'num_transactions': num_transactions,
            'unique_customers': num_unique_customers,
            'unique_styles': num_unique_styles
        }
        
        logger.info(f"\nOverall Sales Metrics:")
        logger.info(f"- Total Sales Value: ${total_sales_value:,.2f}")
        logger.info(f"- Total Yards Sold: {total_yards_sold:,.0f} yards")
        logger.info(f"- Average Price per Yard: ${avg_price_per_yard:.2f}")
        logger.info(f"- Number of Transactions: {num_transactions:,}")
        logger.info(f"- Unique Customers: {num_unique_customers}")
        logger.info(f"- Unique Styles: {num_unique_styles}")
        
        # Top customers by sales value
        logger.info("\nTop 10 Customers by Sales Value:")
        customer_sales = self.sales_df.groupby('Customer').agg({
            'Line Price': 'sum',
            'Yds_ordered': 'sum',
            'Document': 'count'
        }).round(2)
        customer_sales.columns = ['Total Sales ($)', 'Total Yards', 'Order Count']
        customer_sales = customer_sales.sort_values('Total Sales ($)', ascending=False)
        self.analysis_results['top_customers'] = customer_sales.head(10).to_dict()
        logger.info(customer_sales.head(10))
        
        # Top selling styles
        logger.info("\nTop 10 Selling Styles by Volume:")
        style_sales = self.sales_df.groupby('Style').agg({
            'Yds_ordered': 'sum',
            'Line Price': 'sum',
            'Document': 'count'
        }).round(2)
        style_sales.columns = ['Total Yards', 'Total Sales ($)', 'Order Count']
        style_sales = style_sales.sort_values('Total Yards', ascending=False)
        self.analysis_results['top_styles'] = style_sales.head(10).to_dict()
        logger.info(style_sales.head(10))
        
        # Sales trend analysis
        logger.info("\nMonthly Sales Trend:")
        self.sales_df['Month'] = self.sales_df['Invoice Date'].dt.to_period('M')
        monthly_sales = self.sales_df.groupby('Month').agg({
            'Line Price': 'sum',
            'Yds_ordered': 'sum'
        }).round(2)
        monthly_sales.columns = ['Sales ($)', 'Yards']
        self.analysis_results['monthly_trend'] = monthly_sales.to_dict()
        logger.info(monthly_sales)
        
    def analyze_inventory(self):
        """Analyze current inventory levels"""
        logger.info("\n" + "="*60)
        logger.info("INVENTORY ANALYSIS")
        logger.info("="*60)
        
        # Inventory summary
        total_inventory_yards = self.inventory_df['yds'].sum()
        total_inventory_pounds = self.inventory_df['lbs'].sum()
        num_styles_in_inventory = len(self.inventory_df)
        
        self.analysis_results['inventory_summary'] = {
            'total_yards': total_inventory_yards,
            'total_pounds': total_inventory_pounds,
            'num_styles': num_styles_in_inventory
        }
        
        logger.info(f"\nInventory Summary:")
        logger.info(f"- Total Inventory: {total_inventory_yards:,.0f} yards")
        logger.info(f"- Total Weight: {total_inventory_pounds:,.0f} lbs")
        logger.info(f"- Number of Styles in Stock: {num_styles_in_inventory}")
        
        # Top inventory items
        logger.info("\nTop 10 Inventory Items by Yards:")
        top_inventory = self.inventory_df.nlargest(10, 'yds')[['style_id', 'yds', 'lbs']]
        self.analysis_results['top_inventory'] = top_inventory.to_dict()
        logger.info(top_inventory)
        
    def analyze_orders(self):
        """Analyze current orders"""
        logger.info("\n" + "="*60)
        logger.info("CURRENT ORDERS ANALYSIS")
        logger.info("="*60)
        
        # Orders summary
        total_orders_value = (self.orders_df['Ordered'] * self.orders_df['Unit Price']).sum()
        total_orders_yards = self.orders_df['Ordered'].sum()
        num_open_orders = len(self.orders_df[self.orders_df['Status'] == 'Open'])
        
        self.analysis_results['orders_summary'] = {
            'total_value': total_orders_value,
            'total_yards': total_orders_yards,
            'open_orders': num_open_orders
        }
        
        logger.info(f"\nCurrent Orders Summary:")
        logger.info(f"- Total Orders Value: ${total_orders_value:,.2f}")
        logger.info(f"- Total Yards on Order: {total_orders_yards:,.0f} yards")
        logger.info(f"- Number of Open Orders: {num_open_orders}")
        
        # Top customers with pending orders
        logger.info("\nTop Customers by Pending Order Volume:")
        customer_orders = self.orders_df.groupby('Sold To').agg({
            'Ordered': 'sum',
            'Status': 'count'
        }).round(2)
        customer_orders.columns = ['Total Yards', 'Order Count']
        customer_orders['Estimated Value'] = self.orders_df.groupby('Sold To').apply(
            lambda x: (x['Ordered'] * x['Unit Price']).sum()
        ).round(2)
        customer_orders = customer_orders.sort_values('Total Yards', ascending=False)
        self.analysis_results['top_order_customers'] = customer_orders.head(10).to_dict()
        logger.info(customer_orders.head(10))
        
    def generate_forecasts(self, 
                         lookback_days: int = 90,
                         planning_horizon_days: int = 90,
                         aggregation_period: str = 'weekly',
                         safety_stock_method: str = 'statistical',
                         include_safety_stock: bool = True):
        """
        Generate forecasts from sales data
        
        Args:
            lookback_days: Number of historical days to analyze
            planning_horizon_days: Number of days to forecast
            aggregation_period: Time period for aggregation
            safety_stock_method: Method for calculating safety stock
            include_safety_stock: Whether to include safety stock
            
        Returns:
            List of FinishedGoodsForecast objects
        """
        logger.info("\n" + "="*60)
        logger.info("FORECAST GENERATION")
        logger.info("="*60)
        
        # Initialize forecast generator
        forecast_generator = SalesForecastGenerator(
            sales_df=self.sales_df,
            planning_horizon_days=planning_horizon_days,
            lookback_days=lookback_days,
            aggregation_period=aggregation_period,
            safety_stock_method=safety_stock_method
        )
        
        # Generate forecasts
        logger.info(f"Generating forecasts with {lookback_days} days lookback and {planning_horizon_days} days horizon...")
        self.forecasts = forecast_generator.generate_forecasts(
            include_safety_stock=include_safety_stock
        )
        
        logger.info(f"Generated {len(self.forecasts)} style forecasts")

        # Summarize forecasts
        total_forecast_qty = sum(f.forecast_qty for f in self.forecasts)
        avg_forecast_qty = total_forecast_qty / len(self.forecasts) if self.forecasts else 0

        self.analysis_results['forecast_summary'] = {
            'num_forecasts': len(self.forecasts),
            'total_quantity': total_forecast_qty,
            'avg_quantity': avg_forecast_qty,
            'lookback_days': lookback_days,
            'planning_horizon_days': planning_horizon_days,
            'aggregation_period': aggregation_period,
            'safety_stock_method': safety_stock_method
        }

        logger.info(f"Total forecast quantity: {total_forecast_qty:,.0f} yards")
        logger.info(f"Average forecast per style: {avg_forecast_qty:,.0f} yards")

        # Show top forecasted styles
        logger.info("\nTop 10 Forecasted Styles:")
        forecast_df = pd.DataFrame([
            {
                'Style': f.sku_id,
                'Forecast Qty': f.forecast_qty,
                'Source': f.source,
                'Confidence': f.confidence
            } for f in self.forecasts
        ])
        forecast_df = forecast_df.sort_values('Forecast Qty', ascending=False)
        logger.info(forecast_df.head(10))
        
        return self.forecasts
        
    def calculate_inventory_alerts(self):
        """Calculate inventory alerts based on forecasts and current inventory"""
        logger.info("\n" + "="*60)
        logger.info("INVENTORY ALERTS")
        logger.info("="*60)
        
        if not self.forecasts:
            logger.warning("No forecasts available. Generate forecasts first.")
            return []
        
        # Create forecast lookup
        forecast_lookup = {f.sku_id: f.forecast_qty for f in self.forecasts}

        # Calculate coverage for each style
        alerts = []
        for style, forecast_qty in forecast_lookup.items():
            # Check inventory
            inventory_match = self.inventory_df[self.inventory_df['style_id'].str.startswith(style)]
            current_inventory = inventory_match['yds'].sum() if not inventory_match.empty else 0
            
            # Calculate monthly demand (assuming 90-day forecast)
            monthly_demand = forecast_qty / 3  # 3 months
            
            # Calculate coverage
            coverage_months = current_inventory / monthly_demand if monthly_demand > 0 else float('inf')
            
            if coverage_months < 2:  # Less than 2 months coverage
                alerts.append({
                    'style': style,
                    'forecast_qty': forecast_qty,
                    'monthly_demand': monthly_demand,
                    'inventory': current_inventory,
                    'coverage': coverage_months,
                    'shortage': max(0, forecast_qty - current_inventory)
                })
        
        # Sort by coverage (lowest first)
        alerts.sort(key=lambda x: x['coverage'])
        
        logger.info("Style | Forecast (90d) | Current Inv | Coverage (months) | Shortage")
        logger.info("-" * 80)
        
        for alert in alerts[:15]:  # Show top 15 alerts
            logger.info(
                f"{alert['style']:<15} | {alert['forecast_qty']:>13,.0f} | "
                f"{alert['inventory']:>11,.0f} | {alert['coverage']:>16.1f} | "
                f"{alert['shortage']:>8,.0f}"
            )
        
        self.analysis_results['inventory_alerts'] = alerts
        return alerts
        
    def save_results(self):
        """Save all analysis results and forecasts"""
        logger.info("\n" + "="*60)
        logger.info("SAVING RESULTS")
        logger.info("="*60)
        
        # Create output directory if it doesn't exist
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Save analysis results
        analysis_file = output_dir / 'sales_inventory_analysis.json'
        with open(analysis_file, 'w') as f:
            # Convert Period objects to strings for JSON serialization
            results_copy = self.analysis_results.copy()
            if 'monthly_trend' in results_copy:
                monthly_trend = results_copy['monthly_trend']
                if 'Sales ($)' in monthly_trend:
                    monthly_trend['Sales ($)'] = {str(k): v for k, v in monthly_trend['Sales ($)'].items()}
                if 'Yards' in monthly_trend:
                    monthly_trend['Yards'] = {str(k): v for k, v in monthly_trend['Yards'].items()}
            
            json.dump(results_copy, f, indent=2, default=str)
        logger.info(f"Analysis results saved to {analysis_file}")
        
        # Save forecasts in a format compatible with the planning engine
        if self.forecasts:
            forecast_file = output_dir / 'generated_forecasts.csv'
            forecast_data = []
            for f in self.forecasts:
                forecast_data.append({
                    'sku_id': f.sku_id,
                    'quantity': f.forecast_qty,  # Save as 'quantity' for compatibility
                    'forecast_qty': f.forecast_qty,
                    'source': f.source,
                    'confidence': f.confidence,
                    'forecast_date': f.forecast_date.strftime('%Y-%m-%d') if f.forecast_date else None,
                    'unit': getattr(f, 'unit', 'yards'),
                    'notes': getattr(f, 'notes', '')
                })
            forecast_df = pd.DataFrame(forecast_data)
            forecast_df.to_csv(forecast_file, index=False)
            logger.info(f"Forecasts saved to {forecast_file}")
        
        # Save inventory alerts
        if 'inventory_alerts' in self.analysis_results:
            alerts_file = output_dir / 'inventory_alerts.csv'
            alerts_df = pd.DataFrame(self.analysis_results['inventory_alerts'])
            if not alerts_df.empty:
                alerts_df.to_csv(alerts_file, index=False)
                logger.info(f"Inventory alerts saved to {alerts_file}")
        
        # Create integration file for the planning engine
        integration_file = output_dir / 'sales_forecast_integration.json'
        integration_data = {
            'generated_at': datetime.now().isoformat(),
            'forecast_file': str(forecast_file) if self.forecasts else None,
            'num_forecasts': len(self.forecasts),
            'total_forecast_qty': sum(f.forecast_qty for f in self.forecasts),
            'analysis_file': str(analysis_file),
            'alerts_file': str(alerts_file) if 'inventory_alerts' in self.analysis_results else None,
            'config': {
                'lookback_days': self.analysis_results.get('forecast_summary', {}).get('lookback_days', 90),
                'planning_horizon_days': self.analysis_results.get('forecast_summary', {}).get('planning_horizon_days', 90),
                'aggregation_period': self.analysis_results.get('forecast_summary', {}).get('aggregation_period', 'weekly'),
                'safety_stock_method': self.analysis_results.get('forecast_summary', {}).get('safety_stock_method', 'statistical')
            }
        }
        with open(integration_file, 'w') as f:
            json.dump(integration_data, f, indent=2)
        logger.info(f"Integration file saved to {integration_file}")
        
        logger.info("\nAll results saved successfully!")
        
    def run_full_analysis(self):
        """Run the complete analysis pipeline"""
        # Load data
        self.load_data()
        
        # Perform analyses
        self.analyze_sales()
        self.analyze_inventory()
        self.analyze_orders()
        
        # Generate forecasts
        self.generate_forecasts()
        
        # Calculate alerts
        self.calculate_inventory_alerts()
        
        # Save results
        self.save_results()
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*60)
        
        return self.analysis_results, self.forecasts


def main():
    """Main entry point for the sales inventory analyzer"""
    # Initialize analyzer
    analyzer = SalesInventoryAnalyzer()
    
    # Run full analysis
    results, forecasts = analyzer.run_full_analysis()
    
    # Print summary
    logger.info("\nSUMMARY:")
    logger.info(f"- Generated {len(forecasts)} forecasts")
    logger.info(f"- Identified {len(results.get('inventory_alerts', []))} inventory alerts")
    logger.info(f"- Analysis results saved to output/sales_inventory_analysis.json")
    logger.info(f"- Forecasts saved to output/generated_forecasts.csv")
    logger.info(f"- Integration file saved to output/sales_forecast_integration.json")
    
    logger.info("\nThe forecasts are now ready to be used by the main planning engine!")
    logger.info("To integrate with the planner, ensure 'enable_sales_forecasting' is set to True in the config.")


if __name__ == "__main__":
    main()