"""
Sales Data Processor
Handles data pipeline integration between sales analysis and planning system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

from models.forecast import FinishedGoodsForecast
from models.sales_forecast_generator import SalesForecastGenerator
from models.bom import BOMExploder, StyleYarnBOM
from config.settings import PlanningConfig

logger = logging.getLogger(__name__)


class SalesDataProcessor:
    """Process sales data for integration with planning system"""
    
    def __init__(self, config: Optional[PlanningConfig] = None):
        """Initialize the sales data processor"""
        self.config = config or PlanningConfig()
        self.sales_df = None
        self.inventory_df = None
        self.bom_df = None
        self.forecast_generator = None
        
    def load_and_validate_sales_data(self, 
                                   sales_file: str = "data/Sales Activity Report.csv",
                                   date_column: str = "Invoice Date",
                                   style_column: str = "Style",
                                   quantity_column: str = "Yds_ordered") -> pd.DataFrame:
        """
        Load and validate sales data
        
        Args:
            sales_file: Path to sales data file
            date_column: Name of date column
            style_column: Name of style/SKU column
            quantity_column: Name of quantity column
            
        Returns:
            Cleaned and validated sales DataFrame
        """
        logger.info(f"Loading sales data from {sales_file}")
        
        # Load data
        self.sales_df = pd.read_csv(sales_file)
        
        # Validate required columns
        required_columns = [date_column, style_column, quantity_column]
        missing_columns = [col for col in required_columns if col not in self.sales_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean and convert data types
        self.sales_df[date_column] = pd.to_datetime(self.sales_df[date_column], errors='coerce')
        self.sales_df[quantity_column] = pd.to_numeric(self.sales_df[quantity_column], errors='coerce')
        
        # Remove invalid rows
        initial_rows = len(self.sales_df)
        self.sales_df = self.sales_df.dropna(subset=[date_column, style_column, quantity_column])
        removed_rows = initial_rows - len(self.sales_df)
        
        if removed_rows > 0:
            logger.warning(f"Removed {removed_rows} invalid rows from sales data")
        
        # Validate data quality
        validation_results = self._validate_sales_data_quality()
        
        logger.info(f"Loaded {len(self.sales_df)} valid sales records")
        logger.info(f"Date range: {self.sales_df[date_column].min()} to {self.sales_df[date_column].max()}")
        logger.info(f"Unique styles: {self.sales_df[style_column].nunique()}")
        
        return self.sales_df
    
    def _validate_sales_data_quality(self) -> Dict[str, any]:
        """Validate sales data quality"""
        results = {
            'total_records': len(self.sales_df),
            'date_range': (self.sales_df['Invoice Date'].min(), self.sales_df['Invoice Date'].max()),
            'negative_quantities': (self.sales_df['Yds_ordered'] < 0).sum(),
            'zero_quantities': (self.sales_df['Yds_ordered'] == 0).sum(),
            'missing_styles': self.sales_df['Style'].isna().sum()
        }
        
        # Log warnings for data quality issues
        if results['negative_quantities'] > 0:
            logger.warning(f"Found {results['negative_quantities']} records with negative quantities")
        
        if results['zero_quantities'] > 0:
            logger.warning(f"Found {results['zero_quantities']} records with zero quantities")
        
        return results
    
    def load_inventory_data(self, inventory_file: str = "data/Inventory.csv") -> pd.DataFrame:
        """Load and process inventory data"""
        logger.info(f"Loading inventory data from {inventory_file}")
        
        self.inventory_df = pd.read_csv(inventory_file)
        
        # Clean numeric columns
        if 'yds' in self.inventory_df.columns:
            self.inventory_df['yds'] = pd.to_numeric(
                self.inventory_df['yds'].astype(str).str.replace(',', ''), 
                errors='coerce'
            )
        
        if 'lbs' in self.inventory_df.columns:
            self.inventory_df['lbs'] = pd.to_numeric(
                self.inventory_df['lbs'].astype(str).str.replace(',', ''), 
                errors='coerce'
            )
        
        logger.info(f"Loaded {len(self.inventory_df)} inventory records")
        
        return self.inventory_df
    
    def load_bom_data(self, bom_file: str = "data/cfab_Yarn_Demand_By_Style.csv") -> pd.DataFrame:
        """Load style-to-yarn BOM data"""
        logger.info(f"Loading BOM data from {bom_file}")
        
        # Check if file exists
        if not Path(bom_file).exists():
            logger.warning(f"BOM file {bom_file} not found")
            return None
        
        self.bom_df = pd.read_csv(bom_file)
        logger.info(f"Loaded {len(self.bom_df)} BOM records")
        
        return self.bom_df
    
    def merge_sales_with_inventory(self) -> pd.DataFrame:
        """
        Merge sales data with current inventory levels
        
        Returns:
            DataFrame with sales and inventory data merged
        """
        if self.sales_df is None or self.inventory_df is None:
            raise ValueError("Sales and inventory data must be loaded first")
        
        # Aggregate recent sales by style
        recent_date = datetime.now() - timedelta(days=90)
        recent_sales = self.sales_df[self.sales_df['Invoice Date'] >= recent_date]
        
        sales_summary = recent_sales.groupby('Style').agg({
            'Yds_ordered': ['sum', 'mean', 'std', 'count'],
            'Invoice Date': ['min', 'max']
        }).round(2)
        
        sales_summary.columns = ['_'.join(col).strip() for col in sales_summary.columns]
        sales_summary = sales_summary.reset_index()
        
        # Merge with inventory
        merged_df = pd.merge(
            sales_summary,
            self.inventory_df[['Style', 'yds', 'lbs']],
            on='Style',
            how='outer',
            suffixes=('_sales', '_inventory')
        )
        
        # Calculate metrics
        merged_df['avg_weekly_demand'] = merged_df['Yds_ordered_sum'] / 13  # 90 days ≈ 13 weeks
        merged_df['weeks_of_inventory'] = merged_df['yds'] / merged_df['avg_weekly_demand']
        merged_df['weeks_of_inventory'] = merged_df['weeks_of_inventory'].replace([np.inf, -np.inf], 0)
        
        # Flag low stock items
        merged_df['low_stock_flag'] = merged_df['weeks_of_inventory'] < 4
        
        return merged_df
    
    def generate_planning_inputs(self,
                               lookback_days: int = 90,
                               planning_horizon_days: int = 90,
                               aggregation_period: str = 'weekly',
                               safety_stock_method: str = 'statistical',
                               include_safety_stock: bool = True) -> Dict[str, any]:
        """
        Generate all inputs needed for the planning system
        
        Returns:
            Dictionary containing forecasts, inventory, and other planning inputs
        """
        if self.sales_df is None:
            raise ValueError("Sales data must be loaded first")
        
        # Initialize forecast generator
        self.forecast_generator = SalesForecastGenerator(
            sales_df=self.sales_df,
            planning_horizon_days=planning_horizon_days,
            lookback_days=lookback_days,
            bom_df=self.bom_df,
            aggregation_period=aggregation_period,
            safety_stock_method=safety_stock_method
        )
        
        # Generate forecasts
        logger.info("Generating forecasts from sales history...")
        forecasts = self.forecast_generator.generate_forecasts(
            include_safety_stock=include_safety_stock
        )
        
        logger.info(f"Generated {len(forecasts)} style forecasts")
        
        # Generate yarn forecasts if BOM is available
        yarn_requirements = None
        if self.bom_df is not None:
            try:
                yarn_requirements = self.forecast_generator.generate_yarn_forecasts(forecasts)
                logger.info(f"Generated requirements for {len(yarn_requirements)} yarns")
            except Exception as e:
                logger.error(f"Error generating yarn forecasts: {e}")
        
        # Create planning inputs dictionary
        planning_inputs = {
            'forecasts': forecasts,
            'yarn_requirements': yarn_requirements,
            'sales_summary': self.merge_sales_with_inventory() if self.inventory_df is not None else None,
            'demand_statistics': self._calculate_overall_statistics(),
            'metadata': {
                'generated_at': datetime.now(),
                'lookback_days': lookback_days,
                'planning_horizon_days': planning_horizon_days,
                'aggregation_period': aggregation_period,
                'safety_stock_method': safety_stock_method,
                'num_styles': len(forecasts)
            }
        }
        
        return planning_inputs
    
    def _calculate_overall_statistics(self) -> Dict[str, float]:
        """Calculate overall demand statistics"""
        if self.sales_df is None:
            return {}
        
        recent_date = datetime.now() - timedelta(days=90)
        recent_sales = self.sales_df[self.sales_df['Invoice Date'] >= recent_date]
        
        # Daily statistics
        daily_sales = recent_sales.groupby('Invoice Date')['Yds_ordered'].sum()
        
        return {
            'avg_daily_demand': daily_sales.mean(),
            'std_daily_demand': daily_sales.std(),
            'cv_daily_demand': daily_sales.std() / daily_sales.mean() if daily_sales.mean() > 0 else 0,
            'total_demand_90d': recent_sales['Yds_ordered'].sum(),
            'unique_styles_90d': recent_sales['Style'].nunique(),
            'avg_order_size': recent_sales['Yds_ordered'].mean()
        }
    
    def create_automated_forecast_pipeline(self,
                                         sales_file: str,
                                         inventory_file: Optional[str] = None,
                                         bom_file: Optional[str] = None,
                                         output_dir: str = "output") -> Dict[str, str]:
        """
        Create an automated pipeline from sales data to forecasts
        
        Args:
            sales_file: Path to sales data file
            inventory_file: Optional path to inventory file
            bom_file: Optional path to BOM file
            output_dir: Directory to save output files
            
        Returns:
            Dictionary with paths to generated output files
        """
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Load all data
        self.load_and_validate_sales_data(sales_file)
        
        if inventory_file:
            self.load_inventory_data(inventory_file)
        
        if bom_file:
            self.load_bom_data(bom_file)
        
        # Generate planning inputs
        planning_inputs = self.generate_planning_inputs()
        
        # Save outputs
        output_files = {}
        
        # Save forecasts
        if planning_inputs['forecasts']:
            forecast_df = self.forecast_generator.create_forecast_summary(planning_inputs['forecasts'])
            forecast_file = f"{output_dir}/style_forecasts_{datetime.now().strftime('%Y%m%d')}.csv"
            forecast_df.to_csv(forecast_file, index=False)
            output_files['style_forecasts'] = forecast_file
            logger.info(f"Saved style forecasts to {forecast_file}")
        
        # Save yarn requirements
        if planning_inputs['yarn_requirements']:
            yarn_df = pd.DataFrame([
                {
                    'yarn_id': yarn_id,
                    'total_qty': data['total_qty'],
                    'unit': data['unit'],
                    'yarn_name': data.get('yarn_name', yarn_id),
                    'num_styles': len(data['sources'])
                }
                for yarn_id, data in planning_inputs['yarn_requirements'].items()
            ])
            yarn_file = f"{output_dir}/yarn_requirements_{datetime.now().strftime('%Y%m%d')}.csv"
            yarn_df.to_csv(yarn_file, index=False)
            output_files['yarn_requirements'] = yarn_file
            logger.info(f"Saved yarn requirements to {yarn_file}")
        
        # Save sales summary
        if planning_inputs['sales_summary'] is not None:
            summary_file = f"{output_dir}/sales_inventory_summary_{datetime.now().strftime('%Y%m%d')}.csv"
            planning_inputs['sales_summary'].to_csv(summary_file, index=False)
            output_files['sales_summary'] = summary_file
            logger.info(f"Saved sales/inventory summary to {summary_file}")
        
        # Save metadata
        import json
        metadata_file = f"{output_dir}/forecast_metadata_{datetime.now().strftime('%Y%m%d')}.json"
        with open(metadata_file, 'w') as f:
            json.dump(planning_inputs['metadata'], f, indent=2, default=str)
        output_files['metadata'] = metadata_file
        
        logger.info(f"Automated forecast pipeline completed. Generated {len(output_files)} output files.")
        
        return output_files
    
    def validate_style_yarn_mapping(self) -> Dict[str, List[str]]:
        """
        Validate that all forecasted styles have yarn mappings
        
        Returns:
            Dictionary with validation results
        """
        if self.sales_df is None or self.bom_df is None:
            return {'error': 'Sales and BOM data must be loaded first'}
        
        # Get unique styles from sales
        sales_styles = set(self.sales_df['Style'].unique())
        
        # Get styles from BOM
        bom_style_col = 'Style' if 'Style' in self.bom_df.columns else 'style_id'
        bom_styles = set(self.bom_df[bom_style_col].unique())
        
        return {
            'sales_styles_without_bom': list(sales_styles - bom_styles),
            'bom_styles_without_sales': list(bom_styles - sales_styles),
            'matched_styles': list(sales_styles & bom_styles),
            'coverage_percentage': len(sales_styles & bom_styles) / len(sales_styles) * 100 if sales_styles else 0
        }