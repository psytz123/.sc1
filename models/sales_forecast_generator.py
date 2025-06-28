"""
Sales Forecast Generator Module
Generates forecasts from historical sales data for integration with the planning system
Enhanced with automated forecast creation and improved integration
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from scipy import stats
from models.forecast import FinishedGoodsForecast
from models.bom import BillOfMaterials, StyleYarnBOM, BOMExploder

logger = logging.getLogger(__name__)

class SalesForecastGenerator:
    """Generate forecasts from historical sales data with enhanced capabilities"""
    
    # Time aggregation options
    AGGREGATION_PERIODS = {
        'daily': 'D',
        'weekly': 'W',
        'monthly': 'M',
        'quarterly': 'Q'
    }
    
    # Safety stock calculation methods
    SAFETY_STOCK_METHODS = {
        'percentage': 'Simple percentage buffer',
        'statistical': 'Based on demand variability and service level',
        'min_max': 'Minimum/maximum approach',
        'dynamic': 'Adjusts based on recent variability'
    }
    
    def __init__(self, 
                 sales_df: pd.DataFrame,
                 planning_horizon_days: int = 90,
                 lookback_days: int = 90,
                 min_history_days: int = 30,
                 bom_df: Optional[pd.DataFrame] = None,
                 aggregation_period: str = 'weekly',
                 safety_stock_method: str = 'statistical',
                 service_level: float = 0.95):
        """
        Initialize the forecast generator
        
        Args:
            sales_df: DataFrame with sales history (must have 'Invoice Date', 'Style', 'Yds_ordered')
            planning_horizon_days: Number of days to forecast into the future
            lookback_days: Number of historical days to analyze
            min_history_days: Minimum days of history required to generate forecast
            bom_df: Optional DataFrame with style-to-yarn mapping from cfab_Yarn_Demand_By_Style.csv
            aggregation_period: Time period for aggregation ('daily', 'weekly', 'monthly')
            safety_stock_method: Method for calculating safety stock
            service_level: Service level for statistical safety stock (0-1)
        """
        self.sales_df = sales_df.copy()
        self.planning_horizon_days = planning_horizon_days
        self.lookback_days = lookback_days
        self.min_history_days = min_history_days
        self.bom_df = bom_df
        self.aggregation_period = aggregation_period
        self.safety_stock_method = safety_stock_method
        self.service_level = service_level
        
        # Ensure date column is datetime
        if 'Invoice Date' in self.sales_df.columns:
            self.sales_df['Invoice Date'] = pd.to_datetime(self.sales_df['Invoice Date'])
        
        # Calculate date ranges
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=lookback_days)
        self.forecast_end_date = self.end_date + timedelta(days=planning_horizon_days)
        
        # Process style-yarn BOM if provided
        self.style_yarn_boms = None
        if bom_df is not None:
            self.style_yarn_boms = BOMExploder.from_style_yarn_dataframe(bom_df)
    
    def generate_forecasts(self, 
                          include_safety_stock: bool = True,
                          growth_factor: float = 1.0,
                          seasonality_factors: Optional[Dict[int, float]] = None) -> List[FinishedGoodsForecast]:
        """
        Generate forecasts for all styles with sufficient history
        
        Args:
            include_safety_stock: Whether to include safety stock in forecasts
            growth_factor: Multiplier for growth adjustment (1.0 = no growth)
            seasonality_factors: Monthly seasonality factors {month: factor}
            
        Returns:
            List of FinishedGoodsForecast objects
        """
        forecasts = []
        
        # Filter sales data to lookback period
        recent_sales = self.sales_df[
            (self.sales_df['Invoice Date'] >= self.start_date) &
            (self.sales_df['Invoice Date'] <= self.end_date)
        ]
        
        # Get unique styles
        styles = recent_sales['Style'].unique()
        
        for style in styles:
            style_sales = recent_sales[recent_sales['Style'] == style]
            
            # Check if we have enough history
            days_of_history = (style_sales['Invoice Date'].max() - style_sales['Invoice Date'].min()).days
            if days_of_history < self.min_history_days:
                logger.warning(f"Skipping style {style}: only {days_of_history} days of history")
                continue
            
            # Calculate demand statistics
            demand_stats = self.calculate_demand_statistics(style)
            
            if demand_stats['average_demand'] > 0:
                # Apply growth and seasonality
                base_demand = demand_stats['average_demand'] * growth_factor
                
                # Apply seasonality if provided
                current_month = datetime.now().month
                if seasonality_factors and current_month in seasonality_factors:
                    base_demand *= seasonality_factors[current_month]
                
                # Add safety stock if requested
                total_demand = base_demand
                if include_safety_stock:
                    safety_stock = self.calculate_safety_stock(
                        demand_stats['average_demand'],
                        demand_stats['std_deviation'],
                        demand_stats['lead_time_days']
                    )
                    total_demand += safety_stock
                
                # Create forecast object
                forecast = FinishedGoodsForecast(
                    sku_id=style,
                    forecast_qty=int(np.ceil(total_demand)),
                    forecast_date=self.forecast_end_date.date(),
                    source='sales_history',
                    confidence=demand_stats['confidence'],
                    notes=f"Based on {days_of_history} days history, {self.aggregation_period} aggregation"
                )
                forecasts.append(forecast)
        
        return forecasts
    
    def calculate_demand_statistics(self, style_id: str) -> Dict[str, float]:
        """
        Calculate demand statistics for a style
        
        Returns:
            Dictionary with average_demand, std_deviation, cv, confidence, lead_time_days
        """
        # Filter sales for the style
        style_sales = self.sales_df[
            (self.sales_df['Style'] == style_id) &
            (self.sales_df['Invoice Date'] >= self.start_date) &
            (self.sales_df['Invoice Date'] <= self.end_date)
        ].copy()
        
        # Aggregate by selected period
        period = self.AGGREGATION_PERIODS.get(self.aggregation_period, 'W')
        style_sales['period'] = style_sales['Invoice Date'].dt.to_period(period)
        
        # Group by period and sum quantities
        period_demand = style_sales.groupby('period')['Yds_ordered'].sum()
        
        # Fill missing periods with zero
        all_periods = pd.period_range(
            start=style_sales['Invoice Date'].min(),
            end=style_sales['Invoice Date'].max(),
            freq=period
        )
        period_demand = period_demand.reindex(all_periods, fill_value=0)
        
        # Calculate statistics
        average_demand = period_demand.mean()
        std_deviation = period_demand.std()
        cv = std_deviation / average_demand if average_demand > 0 else 0
        
        # Calculate confidence based on CV and number of periods
        num_periods = len(period_demand)
        confidence = min(0.95, (1 - cv) * (num_periods / 52))  # Adjust based on variability and data points
        
        # Estimate lead time (simplified - could be enhanced with actual supplier data)
        lead_time_days = 14  # Default 2 weeks
        
        return {
            'average_demand': average_demand,
            'std_deviation': std_deviation,
            'cv': cv,
            'confidence': confidence,
            'lead_time_days': lead_time_days,
            'num_periods': num_periods
        }
    
    def calculate_safety_stock(self, 
                             average_demand: float,
                             std_deviation: float,
                             lead_time_days: int) -> float:
        """
        Calculate safety stock based on selected method
        
        Args:
            average_demand: Average periodic demand
            std_deviation: Standard deviation of demand
            lead_time_days: Lead time in days
            
        Returns:
            Safety stock quantity
        """
        if self.safety_stock_method == 'percentage':
            # Simple percentage buffer
            return average_demand * 0.2  # 20% buffer
            
        elif self.safety_stock_method == 'statistical':
            # Statistical safety stock calculation
            # Z-score for service level
            z_score = stats.norm.ppf(self.service_level)
            
            # Convert lead time to periods
            if self.aggregation_period == 'weekly':
                lead_time_periods = lead_time_days / 7
            elif self.aggregation_period == 'monthly':
                lead_time_periods = lead_time_days / 30
            else:
                lead_time_periods = lead_time_days
            
            # Safety stock = Z * σ * √(Lead Time)
            safety_stock = z_score * std_deviation * np.sqrt(lead_time_periods)
            
            return max(0, safety_stock)
            
        elif self.safety_stock_method == 'min_max':
            # Min-max approach - keep minimum of 1 period demand
            return average_demand
            
        elif self.safety_stock_method == 'dynamic':
            # Dynamic based on recent variability
            # Higher safety stock for more variable demand
            cv = std_deviation / average_demand if average_demand > 0 else 0
            multiplier = 1 + cv  # Higher CV = higher multiplier
            return average_demand * multiplier * 0.1
            
        else:
            return 0

    def detect_seasonality_patterns(self, style_id: str = None, min_periods: int = 12) -> Dict[int, float]:
        """
        Detect seasonality patterns from historical sales data

        Args:
            style_id: Specific style to analyze (None for all styles)
            min_periods: Minimum number of periods required for seasonality detection

        Returns:
            Dictionary of monthly seasonality factors {month: factor}
        """
        # Filter sales data
        sales_data = self.sales_df.copy()
        if style_id:
            sales_data = sales_data[sales_data['Style'] == style_id]

        # Ensure we have enough data
        if len(sales_data) < min_periods * 30:  # Approximate days needed
            logger.warning(f"Insufficient data for seasonality detection: {len(sales_data)} records")
            return {}

        # Aggregate by month
        sales_data['month'] = sales_data['Invoice Date'].dt.month
        sales_data['year'] = sales_data['Invoice Date'].dt.year
        sales_data['year_month'] = sales_data['Invoice Date'].dt.to_period('M')

        # Calculate monthly totals
        monthly_sales = sales_data.groupby(['year_month'])['Yds_ordered'].sum()

        # Need at least 2 years of data for reliable seasonality
        if len(monthly_sales) < 24:
            logger.info("Using simple monthly averaging for seasonality (less than 2 years of data)")
            # Simple approach: average by month
            monthly_avg = sales_data.groupby('month')['Yds_ordered'].mean()
            overall_avg = monthly_avg.mean()

            # Calculate factors
            seasonality_factors = {}
            for month in range(1, 13):
                if month in monthly_avg.index:
                    factor = monthly_avg[month] / overall_avg if overall_avg > 0 else 1.0
                    seasonality_factors[month] = round(factor, 3)
                else:
                    seasonality_factors[month] = 1.0

            return seasonality_factors

        # Advanced approach: decomposition for longer time series
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose

            # Ensure continuous time series
            monthly_sales = monthly_sales.asfreq('M', fill_value=0)

            # Perform decomposition
            decomposition = seasonal_decompose(monthly_sales, model='multiplicative', period=12)
            seasonal_component = decomposition.seasonal

            # Extract monthly factors
            monthly_factors = seasonal_component.groupby(seasonal_component.index.month).mean()

            # Normalize factors (ensure average = 1.0)
            avg_factor = monthly_factors.mean()
            seasonality_factors = {
                month: round(factor / avg_factor, 3)
                for month, factor in monthly_factors.items()
            }

        except Exception as e:
            logger.warning(f"Advanced seasonality detection failed: {e}. Using simple approach.")
            # Fallback to simple approach
            monthly_avg = sales_data.groupby('month')['Yds_ordered'].mean()
            overall_avg = monthly_avg.mean()

            seasonality_factors = {}
            for month in range(1, 13):
                if month in monthly_avg.index:
                    factor = monthly_avg[month] / overall_avg if overall_avg > 0 else 1.0
                    seasonality_factors[month] = round(factor, 3)
                else:
                    seasonality_factors[month] = 1.0

        # Validate factors (should be reasonable)
        for month, factor in seasonality_factors.items():
            if factor < 0.5 or factor > 2.0:
                logger.warning(f"Extreme seasonality factor detected for month {month}: {factor}")
                # Cap extreme values
                seasonality_factors[month] = max(0.5, min(2.0, factor))

        return seasonality_factors

    def calculate_weekly_average_demand(self, style_id: str,
                                      apply_seasonality: bool = True,
                                      weeks_ahead: int = 12) -> Dict[str, float]:
        """
        Calculate average weekly demand for a style with optional seasonality adjustment

        Args:
            style_id: Style to analyze
            apply_seasonality: Whether to apply seasonality adjustments
            weeks_ahead: Number of weeks to project (for seasonality application)

        Returns:
            Dictionary with weekly demand statistics
        """
        # Get base statistics
        demand_stats = self.calculate_demand_statistics(style_id)

        if demand_stats['average_demand'] == 0:
            return {
                'weekly_avg': 0,
                'weekly_min': 0,
                'weekly_max': 0,
                'seasonally_adjusted': 0,
                'confidence': 0,
                'cv': 0,
                'num_weeks': 0
            }

        # Base weekly average (already in weekly if that's the aggregation period)
        if self.aggregation_period == 'weekly':
            weekly_avg = demand_stats['average_demand']
        elif self.aggregation_period == 'daily':
            weekly_avg = demand_stats['average_demand'] * 7
        elif self.aggregation_period == 'monthly':
            weekly_avg = demand_stats['average_demand'] / 4.33  # Average weeks per month
        else:
            weekly_avg = demand_stats['average_demand']

        # Calculate min/max from historical data
        style_sales = self.sales_df[
            (self.sales_df['Style'] == style_id) &
            (self.sales_df['Invoice Date'] >= self.start_date) &
            (self.sales_df['Invoice Date'] <= self.end_date)
        ].copy()

        # Weekly aggregation
        style_sales['week'] = style_sales['Invoice Date'].dt.to_period('W')
        weekly_demand = style_sales.groupby('week')['Yds_ordered'].sum()

        weekly_min = weekly_demand.min() if len(weekly_demand) > 0 else 0
        weekly_max = weekly_demand.max() if len(weekly_demand) > 0 else weekly_avg * 2

        # Apply seasonality if requested
        seasonally_adjusted = weekly_avg
        if apply_seasonality:
            # Detect seasonality patterns
            seasonality_factors = self.detect_seasonality_patterns(style_id)

            if seasonality_factors:
                # Calculate average factor for the projection period
                from datetime import datetime, timedelta
                projection_start = datetime.now()

                # Calculate weighted average of seasonal factors for the projection period
                total_weight = 0
                weighted_factor = 0

                for week in range(weeks_ahead):
                    week_date = projection_start + timedelta(weeks=week)
                    month = week_date.month
                    factor = seasonality_factors.get(month, 1.0)
                    weighted_factor += factor
                    total_weight += 1

                avg_seasonal_factor = weighted_factor / total_weight if total_weight > 0 else 1.0
                seasonally_adjusted = weekly_avg * avg_seasonal_factor

        return {
            'weekly_avg': round(weekly_avg, 2),
            'weekly_min': round(weekly_min, 2),
            'weekly_max': round(weekly_max, 2),
            'seasonally_adjusted': round(seasonally_adjusted, 2),
            'confidence': demand_stats['confidence'],
            'cv': demand_stats['cv'],
            'num_weeks': demand_stats['num_periods'] if self.aggregation_period == 'weekly' else None
        }

    def generate_forecasts_with_auto_seasonality(self,
                                               include_safety_stock: bool = True,
                                               growth_factor: float = 1.0,
                                               auto_detect_seasonality: bool = True) -> List[FinishedGoodsForecast]:
        """
        Generate forecasts with automatic seasonality detection

        Args:
            include_safety_stock: Whether to include safety stock
            growth_factor: Growth multiplier
            auto_detect_seasonality: Whether to automatically detect and apply seasonality

        Returns:
            List of FinishedGoodsForecast objects
        """
        forecasts = []

        # Filter sales data to lookback period
        recent_sales = self.sales_df[
            (self.sales_df['Invoice Date'] >= self.start_date) &
            (self.sales_df['Invoice Date'] <= self.end_date)
        ]

        # Get unique styles
        styles = recent_sales['Style'].unique()

        for style in styles:
            style_sales = recent_sales[recent_sales['Style'] == style]

            # Check if we have enough history
            days_of_history = (style_sales['Invoice Date'].max() - style_sales['Invoice Date'].min()).days
            if days_of_history < self.min_history_days:
                logger.warning(f"Skipping style {style}: only {days_of_history} days of history")
                continue

            # Get weekly demand with seasonality
            weekly_stats = self.calculate_weekly_average_demand(
                style,
                apply_seasonality=auto_detect_seasonality,
                weeks_ahead=self.planning_horizon_days // 7
            )

            if weekly_stats['weekly_avg'] > 0:
                # Calculate total demand for planning horizon
                weeks_in_horizon = self.planning_horizon_days / 7

                # Use seasonally adjusted demand if available
                base_weekly_demand = (weekly_stats['seasonally_adjusted']
                                    if auto_detect_seasonality and weekly_stats['seasonally_adjusted'] > 0
                                    else weekly_stats['weekly_avg'])

                # Apply growth factor
                base_weekly_demand *= growth_factor

                # Total demand for the planning period
                total_demand = base_weekly_demand * weeks_in_horizon

                # Add safety stock if requested
                if include_safety_stock:
                    # Use weekly statistics for safety stock calculation
                    weekly_std = weekly_stats['weekly_avg'] * weekly_stats['cv'] if weekly_stats['cv'] else 0
                    safety_stock = self.calculate_safety_stock(
                        base_weekly_demand,
                        weekly_std,
                        14  # Default 2-week lead time
                    )
                    total_demand += safety_stock

                # Create forecast object
                seasonality_note = "with seasonality adjustment" if auto_detect_seasonality else "without seasonality"
                forecast = FinishedGoodsForecast(
                    sku_id=style,
                    forecast_qty=int(np.ceil(total_demand)),
                    forecast_date=self.forecast_end_date.date(),
                    source='sales_history',
                    confidence=weekly_stats['confidence'],
                    notes=f"Based on {days_of_history} days history, weekly avg: {weekly_stats['weekly_avg']:.1f} yards, {seasonality_note}"
                )
                forecasts.append(forecast)

        return forecasts
    
    def aggregate_demand_by_period(self, 
                                 period: str = 'weekly',
                                 styles: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Aggregate demand by specified period
        
        Args:
            period: Aggregation period ('daily', 'weekly', 'monthly', 'quarterly')
            styles: Optional list of styles to include
            
        Returns:
            DataFrame with aggregated demand
        """
        # Filter sales data
        sales_data = self.sales_df.copy()
        if styles:
            sales_data = sales_data[sales_data['Style'].isin(styles)]
        
        # Set period
        freq = self.AGGREGATION_PERIODS.get(period, 'W')
        sales_data['period'] = sales_data['Invoice Date'].dt.to_period(freq)
        
        # Aggregate
        aggregated = sales_data.groupby(['period', 'Style']).agg({
            'Yds_ordered': ['sum', 'mean', 'std', 'count'],
            'Line Price': 'sum'
        }).round(2)
        
        # Flatten column names
        aggregated.columns = ['_'.join(col).strip() for col in aggregated.columns]
        aggregated = aggregated.reset_index()
        
        # Add period start and end dates
        aggregated['period_start'] = aggregated['period'].apply(lambda x: x.start_time)
        aggregated['period_end'] = aggregated['period'].apply(lambda x: x.end_time)
        
        return aggregated
    
    def generate_yarn_forecasts(self, 
                              style_forecasts: Optional[List[FinishedGoodsForecast]] = None) -> Dict[str, Dict]:
        """
        Generate yarn-level forecasts from style forecasts using BOM
        
        Args:
            style_forecasts: Optional list of style forecasts (if None, generates them)
            
        Returns:
            Dictionary of yarn requirements
        """
        if not self.style_yarn_boms:
            raise ValueError("No style-to-yarn BOM data available")
        
        # Generate style forecasts if not provided
        if style_forecasts is None:
            style_forecasts = self.generate_forecasts()
        
        # Convert to dictionary format
        style_forecast_dict = {
            f.sku_id: f.forecast_qty 
            for f in style_forecasts
        }
        
        # Explode to yarn requirements
        yarn_requirements = BOMExploder.explode_style_to_yarn_requirements(
            style_forecast_dict,
            self.style_yarn_boms
        )
        
        return yarn_requirements
    
    def analyze_forecast_accuracy(self, 
                                historical_forecasts: pd.DataFrame,
                                actual_sales: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze forecast accuracy against actual sales
        
        Args:
            historical_forecasts: DataFrame with past forecasts
            actual_sales: DataFrame with actual sales
            
        Returns:
            DataFrame with accuracy metrics
        """
        # Merge forecasts with actuals
        comparison = pd.merge(
            historical_forecasts,
            actual_sales,
            on=['Style', 'period'],
            suffixes=('_forecast', '_actual')
        )
        
        # Calculate accuracy metrics
        comparison['error'] = comparison['qty_actual'] - comparison['qty_forecast']
        comparison['abs_error'] = comparison['error'].abs()
        comparison['pct_error'] = (comparison['error'] / comparison['qty_actual'] * 100).round(2)
        comparison['mape'] = comparison['abs_error'] / comparison['qty_actual'] * 100
        
        # Aggregate metrics by style
        accuracy_summary = comparison.groupby('Style').agg({
            'abs_error': 'mean',
            'mape': 'mean',
            'error': ['mean', 'std']
        }).round(2)
        
        return accuracy_summary
    
    def create_forecast_summary(self, forecasts: List[FinishedGoodsForecast]) -> pd.DataFrame:
        """
        Create a summary DataFrame from forecast objects
        
        Args:
            forecasts: List of FinishedGoodsForecast objects
            
        Returns:
            Summary DataFrame
        """
        data = []
        for forecast in forecasts:
            data.append({
                'style_id': forecast.sku_id,
                'forecast_qty': forecast.forecast_qty,
                'forecast_date': forecast.forecast_date,
                'source': forecast.source,
                'confidence': forecast.confidence,
                'notes': forecast.notes
            })
        
        summary_df = pd.DataFrame(data)
        
        # Add total summary
        total_row = pd.DataFrame([{
            'style_id': 'TOTAL',
            'forecast_qty': summary_df['forecast_qty'].sum(),
            'forecast_date': summary_df['forecast_date'].iloc[0] if len(summary_df) > 0 else None,
            'source': 'aggregated',
            'confidence': summary_df['confidence'].mean() if len(summary_df) > 0 else 0,
            'notes': f'Total of {len(summary_df)} styles'
        }])
        
        summary_df = pd.concat([summary_df, total_row], ignore_index=True)
        
        return summary_df