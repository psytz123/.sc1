"""
Live Data Models for Beverly Knits
==================================
Data models that match the exact format of live CSV files:
- cfab_Yarn_Demand_By_Style.csv
- eFab_SO_List.csv
- Style_BOM.csv
- Inventory.csv
- Supplier_ID.csv
- Yarn_ID.csv
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List, Any
import pandas as pd
import re
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class YarnDemandByStyle:
    """Model for cfab_Yarn_Demand_By_Style.csv"""
    style: str
    yarn: str
    percentage: float  # 0-100 scale in live data
    this_week: float
    week_17: float
    week_18: float
    week_19: float
    week_20: float
    week_21: float
    week_22: float
    week_23: float
    week_24: float
    later: float
    total: float
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> 'YarnDemandByStyle':
        """Create from CSV row, handling comma-separated numbers"""
        def parse_number(value):
            if pd.isna(value) or value == '':
                return 0.0
            # Remove commas and convert to float
            return float(str(value).replace(',', '').strip())
        
        return cls(
            style=str(row['Style']),
            yarn=str(row['Yarn']),
            percentage=parse_number(row['Percentage']),
            this_week=parse_number(row.get('This Week', 0)),
            week_17=parse_number(row.get('Week 17', 0)),
            week_18=parse_number(row.get('Week 18', 0)),
            week_19=parse_number(row.get('Week 19', 0)),
            week_20=parse_number(row.get('Week 20', 0)),
            week_21=parse_number(row.get('Week 21', 0)),
            week_22=parse_number(row.get('Week 22', 0)),
            week_23=parse_number(row.get('Week 23', 0)),
            week_24=parse_number(row.get('Week 24', 0)),
            later=parse_number(row.get('Later', 0)),
            total=parse_number(row.get('Total', 0))
        )


@dataclass
class SalesOrder:
    """Model for eFab_SO_List.csv"""
    status: str
    csr: str
    unit_price: str  # Keep as string initially (e.g., "$5.95 (yds)")
    quoted_date: str
    cf_version: str  # Style/product code
    f_base: str
    on_hold: str  # HTML toggle content
    ordered: int
    uom: str
    sop: str
    po_number: str
    sold_to: str
    ship_to: str
    ship_date: str
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> 'SalesOrder':
        """Create from CSV row"""
        def parse_ordered_quantity(value):
            if pd.isna(value) or value == '':
                return 0
            # Handle comma-separated numbers
            return int(str(value).replace(',', '').strip())
        
        return cls(
            status=str(row.get('Status', '')),
            csr=str(row.get('CSR', '')),
            unit_price=str(row.get('Unit Price', '')),
            quoted_date=str(row.get('Quoted Date', '')),
            cf_version=str(row.get('cFVersion', '')),
            f_base=str(row.get('fBase', '')),
            on_hold=str(row.get('On Hold', '')),
            ordered=parse_ordered_quantity(row.get('Ordered', 0)),
            uom=str(row.get('UOM', '')),
            sop=str(row.get('SOP', '')),
            po_number=str(row.get('PO #', '')),
            sold_to=str(row.get('Sold To', '')),
            ship_to=str(row.get('Ship To', '')),
            ship_date=str(row.get('Ship Date', ''))
        )
    
    def is_on_hold(self) -> bool:
        """Check if order is on hold based on HTML toggle"""
        return 'toggle-on' in self.on_hold
    
    def get_unit_price_value(self) -> float:
        """Extract numeric price from formatted string like '$5.95 (yds)'"""
        try:
            # Extract price using regex
            price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', self.unit_price)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                return float(price_str)
        except:
            pass
        return 0.0


@dataclass
class StyleBOM:
    """Model for Style_BOM.csv"""
    style_id: str
    yarn_id: str
    bom_percentage: float  # 0-1 scale in live data
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> 'StyleBOM':
        """Create from CSV row"""
        return cls(
            style_id=str(row['Style_ID']),
            yarn_id=str(row['Yarn_ID']),
            bom_percentage=float(row['BOM_Percentage'])
        )


@dataclass
class InventoryItem:
    """Model for Inventory.csv"""
    style_id: str
    yds: float
    lbs: float
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> 'InventoryItem':
        """Create from CSV row, handling comma-separated numbers"""
        def parse_number(value):
            if pd.isna(value) or value == '':
                return 0.0
            return float(str(value).replace(',', '').strip())
        
        return cls(
            style_id=str(row['style_id']),
            yds=parse_number(row.get('yds', 0)),
            lbs=parse_number(row.get('lbs', 0))
        )


@dataclass
class SupplierInfo:
    """Model for Supplier_ID.csv"""
    supplier_id: int
    supplier: str
    lead_time: str  # Can be "Remove" or numeric
    moq: str  # Can be "Remove" or numeric
    type: str  # "Import", "Domestic", or "Remove"
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> 'SupplierInfo':
        """Create from CSV row"""
        return cls(
            supplier_id=int(row['Supplier_ID']),
            supplier=str(row['Supplier']),
            lead_time=str(row['Lead_time']),
            moq=str(row['MOQ']),
            type=str(row['Type'])
        )
    
    def is_active(self) -> bool:
        """Check if supplier is active (not marked as Remove)"""
        return self.type != "Remove"
    
    def get_lead_time_days(self) -> int:
        """Get lead time as integer days"""
        if self.lead_time == "Remove":
            return 0
        try:
            return int(self.lead_time)
        except:
            return 14  # Default


@dataclass
class YarnMaster:
    """Model for Yarn_ID.csv"""
    yarn_id: str
    supplier: str
    description: str
    blend: str
    type: str
    color: str
    desc_1: str
    desc_2: str
    desc_3: str
    on_order: float
    allocated: float
    planning_balance: float
    cost_pound: str  # Formatted like "$5.09 "
    total_cost: str  # Formatted like "($2,183.40)" for negatives
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> 'YarnMaster':
        """Create from CSV row"""
        return cls(
            yarn_id=str(row['Yarn_ID']),
            supplier=str(row['Supplier']),
            description=str(row['Description']),
            blend=str(row['Blend']),
            type=str(row['Type']),
            color=str(row['Color']),
            desc_1=str(row['Desc_1']),
            desc_2=str(row['Desc_2']),
            desc_3=str(row['Desc_3']),
            on_order=float(row.get('On_Order', 0)) if pd.notna(row.get('On_Order')) else 0.0,
            allocated=float(row.get('Allocated', 0)) if pd.notna(row.get('Allocated')) else 0.0,
            planning_balance=float(row.get('Planning_Ballance', 0)) if pd.notna(row.get('Planning_Ballance')) else 0.0,
            cost_pound=str(row.get('Cost_Pound', '')),
            total_cost=str(row.get('Total_Cast', ''))  # Note: likely a typo in original CSV
        )
    
    def get_cost_per_pound(self) -> float:
        """Extract numeric cost from formatted string like '$5.09 '"""
        try:
            # Remove $ and spaces, convert to float
            cost_str = self.cost_pound.replace('$', '').replace(' ', '').strip()
            if cost_str:
                return float(cost_str)
        except:
            pass
        return 0.0
    
    def get_total_cost_value(self) -> float:
        """Extract numeric total cost, handling negative values in parentheses"""
        try:
            cost_str = self.total_cost.replace('$', '').replace(',', '').strip()
            # Handle negative values in parentheses
            if cost_str.startswith('(') and cost_str.endswith(')'):
                cost_str = cost_str[1:-1]  # Remove parentheses
                return -float(cost_str)
            elif cost_str:
                return float(cost_str)
        except:
            pass
        return 0.0


class LiveDataValidator:
    """Validates live data files and provides quality reports"""
    
    @staticmethod
    def validate_yarn_demand_by_style(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate cfab_Yarn_Demand_By_Style.csv"""
        validation_results = {
            'total_records': len(df),
            'unique_styles': df['Style'].nunique(),
            'unique_yarns': df['Yarn'].nunique(),
            'issues': []
        }
        
        # Check for missing percentages
        missing_percentages = df['Percentage'].isna().sum()
        if missing_percentages > 0:
            validation_results['issues'].append(f"{missing_percentages} records missing percentages")
        
        # Check percentage totals by style
        style_totals = df.groupby('Style')['Percentage'].sum()
        incorrect_totals = style_totals[abs(style_totals - 100) > 1].index.tolist()
        if incorrect_totals:
            validation_results['issues'].append(f"{len(incorrect_totals)} styles with incorrect percentage totals")
        
        return validation_results
    
    @staticmethod
    def validate_style_bom(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate Style_BOM.csv"""
        validation_results = {
            'total_records': len(df),
            'unique_styles': df['Style_ID'].nunique(),
            'unique_yarns': df['Yarn_ID'].nunique(),
            'issues': []
        }
        
        # Check percentage totals by style (should sum to 1.0)
        style_totals = df.groupby('Style_ID')['BOM_Percentage'].sum()
        incorrect_totals = style_totals[abs(style_totals - 1.0) > 0.01].index.tolist()
        if incorrect_totals:
            validation_results['issues'].append(f"{len(incorrect_totals)} styles with incorrect BOM percentage totals")
        
        return validation_results
    
    @staticmethod
    def validate_sales_orders(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate eFab_SO_List.csv"""
        validation_results = {
            'total_records': len(df),
            'unique_styles': df['cFVersion'].nunique(),
            'on_hold_orders': df['On Hold'].str.contains('toggle-on').sum(),
            'issues': []
        }
        
        # Check for missing quantities
        missing_qty = df['Ordered'].isna().sum()
        if missing_qty > 0:
            validation_results['issues'].append(f"{missing_qty} orders missing quantities")
        
        return validation_results
    
    @staticmethod
    def cross_validate_bom_files(yarn_demand_df: pd.DataFrame, style_bom_df: pd.DataFrame) -> Dict[str, Any]:
        """Cross-validate BOM files for consistency"""
        validation_results = {
            'yarn_demand_styles': set(yarn_demand_df['Style'].unique()),
            'style_bom_styles': set(style_bom_df['Style_ID'].unique()),
            'yarn_demand_yarns': set(yarn_demand_df['Yarn'].unique()),
            'style_bom_yarns': set(style_bom_df['Yarn_ID'].unique()),
            'issues': []
        }
        
        # Check for style mismatches
        style_only_in_demand = validation_results['yarn_demand_styles'] - validation_results['style_bom_styles']
        style_only_in_bom = validation_results['style_bom_styles'] - validation_results['yarn_demand_styles']
        
        if style_only_in_demand:
            validation_results['issues'].append(f"{len(style_only_in_demand)} styles only in yarn demand file")
        if style_only_in_bom:
            validation_results['issues'].append(f"{len(style_only_in_bom)} styles only in BOM file")
        
        # Check for yarn mismatches
        yarn_only_in_demand = validation_results['yarn_demand_yarns'] - validation_results['style_bom_yarns']
        yarn_only_in_bom = validation_results['style_bom_yarns'] - validation_results['yarn_demand_yarns']
        
        if yarn_only_in_demand:
            validation_results['issues'].append(f"{len(yarn_only_in_demand)} yarns only in yarn demand file")
        if yarn_only_in_bom:
            validation_results['issues'].append(f"{len(yarn_only_in_bom)} yarns only in BOM file")
        
        return validation_results