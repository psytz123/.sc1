"""
Utility functions for Beverly Knits Raw Material Planner
"""

from typing import Dict, List, Optional, Union, Any
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import csv
from utils.logger import get_logger


logger = get_logger(__name__)


class DateUtils:
    """Date manipulation utilities"""
    
    @staticmethod
    def get_week_start(date_obj: Union[datetime, date]) -> date:
        """
        Get the start of the week (Monday) for a given date
        
        Args:
            date_obj: Date to process
            
        Returns:
            Monday of the week containing the date
        """
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        days_since_monday = date_obj.weekday()
        return date_obj - timedelta(days=days_since_monday)
    
    @staticmethod
    def get_week_end(date_obj: Union[datetime, date]) -> date:
        """
        Get the end of the week (Sunday) for a given date
        
        Args:
            date_obj: Date to process
            
        Returns:
            Sunday of the week containing the date
        """
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        days_until_sunday = 6 - date_obj.weekday()
        return date_obj + timedelta(days=days_until_sunday)
    
    @staticmethod
    def get_weeks_between(start_date: date, end_date: date) -> int:
        """
        Calculate number of weeks between two dates
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Number of weeks
        """
        delta = end_date - start_date
        return delta.days // 7
    
    @staticmethod
    def add_business_days(start_date: date, business_days: int) -> date:
        """
        Add business days to a date (excluding weekends)
        
        Args:
            start_date: Starting date
            business_days: Number of business days to add
            
        Returns:
            Resulting date
        """
        current_date = start_date
        days_added = 0
        
        while days_added < business_days:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                days_added += 1
                
        return current_date


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
            
        # Normalize units to lowercase
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        # Direct conversion
        if (from_unit, to_unit) in cls.CONVERSIONS:
            return quantity * cls.CONVERSIONS[(from_unit, to_unit)]
            
        # Reverse conversion
        if (to_unit, from_unit) in cls.CONVERSIONS:
            return quantity / cls.CONVERSIONS[(to_unit, from_unit)]
            
        raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported")
    
    @classmethod
    def normalize_unit(cls, unit: str) -> str:
        """
        Normalize unit string to standard format
        
        Args:
            unit: Unit string
            
        Returns:
            Normalized unit
        """
        unit_map = {
            'kilogram': 'kg',
            'kilograms': 'kg',
            'pound': 'lb',
            'pounds': 'lb',
            'gram': 'g',
            'grams': 'g',
            'ounce': 'oz',
            'ounces': 'oz',
            'meter': 'm',
            'meters': 'm',
            'yard': 'yd',
            'yards': 'yd',
            'foot': 'ft',
            'feet': 'ft'
        }
        
        return unit_map.get(unit.lower(), unit.lower())


class DataValidator:
    """Data validation utilities"""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: List[str], 
                          name: str = "DataFrame") -> None:
        """
        Validate that a DataFrame has required columns
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            name: Name of the DataFrame for error messages
            
        Raises:
            ValueError: If validation fails
        """
        if df is None or df.empty:
            raise ValueError(f"{name} is empty or None")
            
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"{name} missing required columns: {missing_columns}")
    
    @staticmethod
    def validate_positive_values(df: pd.DataFrame, columns: List[str]) -> None:
        """
        Validate that specified columns contain only positive values
        
        Args:
            df: DataFrame to validate
            columns: Columns to check
            
        Raises:
            ValueError: If negative values found
        """
        for col in columns:
            if col in df.columns:
                negative_mask = df[col] < 0
                if negative_mask.any():
                    negative_rows = df[negative_mask].index.tolist()
                    raise ValueError(
                        f"Column '{col}' contains negative values at rows: {negative_rows[:5]}"
                        + (" and more..." if len(negative_rows) > 5 else "")
                    )
    
    @staticmethod
    def validate_date_column(df: pd.DataFrame, column: str) -> None:
        """
        Validate and convert date column to datetime
        
        Args:
            df: DataFrame to validate
            column: Date column name
            
        Raises:
            ValueError: If date conversion fails
        """
        try:
            df[column] = pd.to_datetime(df[column])
        except Exception as e:
            raise ValueError(f"Failed to convert column '{column}' to datetime: {str(e)}")


class ReportGenerator:
    """Generate various report formats"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_csv_report(self, data: pd.DataFrame, filename: str) -> Path:
        """
        Generate CSV report
        
        Args:
            data: Data to export
            filename: Output filename (without extension)
            
        Returns:
            Path to generated file
        """
        output_path = self.output_dir / f"{filename}.csv"
        try:
            data.to_csv(output_path, index=False)
            logger.info(f"Generated CSV report: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate CSV report: {e}")
            raise
    
    def generate_excel_report(self, data: Dict[str, pd.DataFrame], 
                            filename: str) -> Path:
        """
        Generate Excel report with multiple sheets
        
        Args:
            data: Dictionary of sheet_name -> DataFrame
            filename: Output filename (without extension)
            
        Returns:
            Path to generated file
        """
        output_path = self.output_dir / f"{filename}.xlsx"
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            logger.info(f"Generated Excel report: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate Excel report: {e}")
            raise
    
    def generate_json_report(self, data: Dict[str, Any], filename: str) -> Path:
        """
        Generate JSON report
        
        Args:
            data: Data to export
            filename: Output filename (without extension)
            
        Returns:
            Path to generated file
        """
        output_path = self.output_dir / f"{filename}.json"
        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Generated JSON report: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise