"""
Utility functions for Beverly Knits Raw Material Planner
"""

from typing import Dict, List
import pandas as pd
from datetime import datetime, date
import logging
from pathlib import Path

from utils.exceptions import FileLoadError, DataValidationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class UnitConverter:
    """Handles unit conversions for materials"""
    
    # Standard conversion factors (from_unit -> to_unit: factor)
    CONVERSIONS = {
        ('kg', 'lb'): 2.20462,
        ('lb', 'kg'): 0.453592,
        ('g', 'oz'): 0.035274,
        ('oz', 'g'): 28.3495,
        ('m', 'yd'): 1.09361,
        ('yd', 'm'): 0.9144,
        ('m', 'ft'): 3.28084,
        ('ft', 'm'): 0.3048,
        ('ton', 'kg'): 1000,
        ('kg', 'ton'): 0.001,
        ('ton', 'lb'): 2204.62,
        ('lb', 'ton'): 0.000453592
    }
    
    @classmethod
    def convert(cls, quantity: float, from_unit: str, to_unit: str) -> float:
        """
        Convert quantity from one unit to another
        
        Args:
            quantity: Amount to convert
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Converted quantity
            
        Raises:
            ValueError: If conversion not supported
        """
        if from_unit == to_unit:
            return quantity
        
        # Try direct conversion
        conversion_key = (from_unit.lower(), to_unit.lower())
        if conversion_key in cls.CONVERSIONS:
            return quantity * cls.CONVERSIONS[conversion_key]
        
        # Try reverse conversion
        reverse_key = (to_unit.lower(), from_unit.lower())
        if reverse_key in cls.CONVERSIONS:
            return quantity / cls.CONVERSIONS[reverse_key]
        
        # Try multi-step conversion through kg (for weight) or m (for length)
        weight_units = ['kg', 'lb', 'g', 'oz', 'ton']
        length_units = ['m', 'yd', 'ft']
        
        if from_unit.lower() in weight_units and to_unit.lower() in weight_units:
            # Convert through kg
            to_kg = cls.convert(quantity, from_unit, 'kg')
            return cls.convert(to_kg, 'kg', to_unit)
        
        if from_unit.lower() in length_units and to_unit.lower() in length_units:
            # Convert through m
            to_m = cls.convert(quantity, from_unit, 'm')
            return cls.convert(to_m, 'm', to_unit)
        
        logger.error(f"Unsupported conversion: {from_unit} to {to_unit}")
        raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported")


class DataLoader:
    """Handles loading and validation of CSV data files"""
    
    @staticmethod
    def load_csv(file_path: str, required_columns: List[str] = None) -> pd.DataFrame:
        """
        Load CSV file with validation and error handling
        
        Args:
            file_path: Path to CSV file
            required_columns: List of required column names
            
        Returns:
            Loaded DataFrame
            
        Raises:
            FileLoadError: If file cannot be loaded
            DataValidationError: If required columns are missing
        """
        logger.info(f"Loading CSV file: {file_path}")
        
        try:
            # Check if file exists
            path = Path(file_path)
            if not path.exists():
                raise FileLoadError(f"File not found: {file_path}")
            
            # Load the CSV
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            
            # Validate required columns
            if required_columns:
                missing_columns = set(required_columns) - set(df.columns)
                if missing_columns:
                    raise DataValidationError(
                        f"Missing required columns in {file_path}: {missing_columns}"
                    )
            
            # Check for empty dataframe
            if df.empty:
                logger.warning(f"Empty dataframe loaded from {file_path}")
            
            return df
            
        except pd.errors.EmptyDataError:
            logger.error(f"Empty CSV file: {file_path}")
            raise FileLoadError(f"Empty CSV file: {file_path}")
        except pd.errors.ParserError as e:
            logger.error(f"Error parsing CSV file {file_path}: {str(e)}")
            raise FileLoadError(f"Error parsing CSV file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error loading {file_path}: {str(e)}")
            raise FileLoadError(f"Unexpected error loading {file_path}: {str(e)}")
    
    @staticmethod
    def validate_numeric_column(df: pd.DataFrame, column: str, min_value: float = None, 
                              max_value: float = None) -> pd.DataFrame:
        """
        Validate numeric column values
        
        Args:
            df: DataFrame to validate
            column: Column name to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Validated DataFrame
            
        Raises:
            DataValidationError: If validation fails
        """
        if column not in df.columns:
            raise DataValidationError(f"Column '{column}' not found in DataFrame")
        
        # Convert to numeric, coercing errors
        df[column] = pd.to_numeric(df[column], errors='coerce')
        
        # Check for non-numeric values
        non_numeric = df[column].isna().sum()
        if non_numeric > 0:
            logger.warning(f"Found {non_numeric} non-numeric values in column '{column}'")
        
        # Validate range
        if min_value is not None:
            below_min = df[column] < min_value
            if below_min.any():
                logger.warning(f"Found {below_min.sum()} values below minimum {min_value} in column '{column}'")
        
        if max_value is not None:
            above_max = df[column] > max_value
            if above_max.any():
                logger.warning(f"Found {above_max.sum()} values above maximum {max_value} in column '{column}'")
        
        return df


class DateUtils:
    """Date calculation utilities"""
    
    @staticmethod
    def get_next_business_day(start_date: datetime) -> date:
        """Get the next business day from a given date"""
        try:
            current = start_date.date() if hasattr(start_date, 'date') else start_date
            
            # Move to next day
            from datetime import timedelta
            next_day = current + timedelta(days=1)
            
            # Skip weekends
            while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
                next_day += timedelta(days=1)
            
            return next_day
        except Exception as e:
            logger.error(f"Error calculating next business day: {str(e)}")
            raise
    
    @staticmethod
    def add_business_days(start_date: date, days: int) -> date:
        """Add business days to a date, skipping weekends"""
        try:
            from datetime import timedelta
            current = start_date
            
            for _ in range(days):
                current += timedelta(days=1)
                # Skip weekends
                while current.weekday() >= 5:
                    current += timedelta(days=1)
            
            return current
        except Exception as e:
            logger.error(f"Error adding business days: {str(e)}")
            raise
    
    @staticmethod
    def calculate_lead_time_date(order_date: date, lead_time_days: int) -> date:
        """Calculate expected delivery date based on lead time"""
        return DateUtils.add_business_days(order_date, lead_time_days)


class ReportGenerator:
    """Generates executive summary reports"""
    
    @staticmethod
    def generate_summary(recommendations: List, config: Dict) -> str:
        """Generate executive summary of recommendations"""
        try:
            if not recommendations:
                return "No procurement recommendations generated."
            
            total_cost = sum(r.total_cost for r in recommendations)
            total_items = len(recommendations)
            
            # Group by urgency based on lead time
            urgent = [r for r in recommendations if r.lead_time_days <= 14]
            normal = [r for r in recommendations if 14 < r.lead_time_days <= 30]
            low = [r for r in recommendations if r.lead_time_days > 30]
            
            summary = f"""
Beverly Knits Raw Material Planning Summary
==========================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Recommendations: {total_items}
Total Procurement Cost: ${total_cost:,.2f}

Urgency Breakdown:
- High Priority (Urgent): {len(urgent)} items
- Normal Priority: {len(normal)} items  
- Low Priority: {len(low)} items

Configuration:
- Safety Stock: {config.get('safety_stock_percentage', 0) * 100:.0f}%
- Planning Horizon: {config.get('planning_horizon_days', 30)} days
- EOQ Optimization: {'Enabled' if config.get('enable_eoq_optimization', False) else 'Disabled'}
- Multi-Supplier: {'Enabled' if config.get('enable_multi_supplier', False) else 'Disabled'}
"""
            return summary
        except Exception as e:
            logger.error(f"Error generating report summary: {str(e)}")
            return "Error generating summary report"


class ValidationUtils:
    """Data validation utilities"""
    
    @staticmethod
    def validate_date_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Validate and convert date column"""
        try:
            if column not in df.columns:
                raise DataValidationError(f"Date column '{column}' not found")
            
            # Convert to datetime
            df[column] = pd.to_datetime(df[column], errors='coerce')
            
            # Check for invalid dates
            invalid_dates = df[column].isna().sum()
            if invalid_dates > 0:
                logger.warning(f"Found {invalid_dates} invalid dates in column '{column}'")
            
            # Check for dates too far in past or future
            current_date = datetime.now().date()
            if not df[column].isna().all():
                dates = pd.to_datetime(df[column].dropna()).dt.date
                
                # Check for very old dates (more than 5 years ago)
                if hasattr(dates, '__iter__'):
                    old_dates = dates < date(current_date.year - 5, 1, 1)
                    if old_dates.any():
                        logger.warning(f"Found {old_dates.sum()} dates older than 5 years in column '{column}'")
                
                # Check for far future dates (more than 2 years ahead)
                if hasattr(dates, '__iter__'):
                    future_dates = dates > date(current_date.year + 2, 12, 31)
                    if future_dates.any():
                        logger.warning(f"Found {future_dates.sum()} dates more than 2 years in future in column '{column}'")
            
            return df
        except Exception as e:
            logger.error(f"Error validating date column '{column}': {str(e)}")
            raise DataValidationError(f"Error validating date column '{column}': {str(e)}")