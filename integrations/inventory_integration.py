"""
Inventory Integration Module
Handles inventory data integration, validation, and optimization
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InventoryIntegrationError(Exception):
    """Base exception for inventory integration errors"""
    pass

class InventoryDataError(InventoryIntegrationError):
    """Exception for inventory data issues"""
    pass

class InventoryValidationError(InventoryIntegrationError):
    """Exception for inventory validation failures"""
    pass

class InventoryIntegration:
    """Handles inventory data integration and optimization"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize inventory integration"""
        self.config = config or {}
        self.data_dir = self.config.get('data_directory', 'data')
        self.errors = []
        self.warnings = []
        
        # Inventory thresholds
        self.thresholds = self.config.get('inventory_thresholds', {
            'critical_stock_days': 7,
            'low_stock_days': 14,
            'excess_stock_days': 180,
            'obsolete_stock_days': 365
        })
        
    def load_inventory_data(self) -> pd.DataFrame:
        """
        Load inventory data from multiple sources
        
        Returns:
            DataFrame with consolidated inventory information
            
        Raises:
            InventoryDataError: If no inventory data can be loaded
        """
        logger.info("Loading inventory data from multiple sources...")
        
        inventory_sources = [
            os.path.join(self.data_dir, 'integrated_inventory_v2.csv'),
            os.path.join(self.data_dir, 'integrated_inventory.csv'),
            os.path.join(self.data_dir, 'inventory_master.csv'),
            os.path.join(self.data_dir, 'current_inventory.csv')
        ]
        
        inventory_dfs = []
        
        for source in inventory_sources:
            if os.path.exists(source):
                try:
                    df = pd.read_csv(source)
                    df['source_file'] = os.path.basename(source)
                    inventory_dfs.append(df)
                    logger.info(f"Loaded {len(df)} inventory records from {source}")
                except Exception as e:
                    logger.error(f"Failed to load {source}: {str(e)}")
                    self.errors.append(f"Failed to load {source}: {str(e)}")
        
        if not inventory_dfs:
            raise InventoryDataError("No inventory data files found")
        
        # Combine all inventory data
        combined_df = pd.concat(inventory_dfs, ignore_index=True)
        
        # Standardize column names
        column_mapping = {
            'Material ID': 'material_id',
            'Material_ID': 'material_id',
            'Yarn ID': 'material_id',
            'Yarn_ID': 'material_id',
            'SKU': 'material_id',
            'On Hand': 'on_hand_qty',
            'On_Hand': 'on_hand_qty',
            'Current Stock': 'on_hand_qty',
            'current_stock': 'on_hand_qty',
            'Quantity_on_Hand': 'on_hand_qty',
            'Open PO': 'open_po_qty',
            'Open_PO': 'open_po_qty',
            'Incoming Stock': 'open_po_qty',
            'incoming_stock': 'open_po_qty',
            'Unit': 'unit',
            'UOM': 'unit',
            'Location': 'location',
            'Warehouse': 'location',
            'Last Updated': 'last_updated',
            'Last_Updated': 'last_updated'
        }
        
        combined_df.rename(columns=column_mapping, inplace=True)
        
        # Remove duplicates based on material_id and location
        if 'material_id' in combined_df.columns:
            if 'location' in combined_df.columns:
                combined_df = combined_df.drop_duplicates(
                    subset=['material_id', 'location'], keep='last'
                )
            else:
                combined_df = combined_df.drop_duplicates(
                    subset=['material_id'], keep='last'
                )
        
        logger.info(f"Loaded total of {len(combined_df)} unique inventory records")
        
        return combined_df
    
    def validate_inventory_data(self, inventory_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Validate inventory data for completeness and consistency
        
        Args:
            inventory_df: DataFrame with inventory data
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        # Check required columns
        required_columns = ['material_id', 'on_hand_qty']
        missing_columns = [col for col in required_columns if col not in inventory_df.columns]
        
        if missing_columns:
            validation_results['errors'].append(f"Missing required columns: {missing_columns}")
        
        # Validate data types and ranges
        if 'on_hand_qty' in inventory_df.columns:
            # Check for negative quantities
            negative_qty = inventory_df[inventory_df['on_hand_qty'] < 0]
            if len(negative_qty) > 0:
                validation_results['errors'].append(
                    f"{len(negative_qty)} items have negative on-hand quantities"
                )
                for _, item in negative_qty.head(5).iterrows():
                    validation_results['errors'].append(
                        f"  - {item['material_id']}: {item['on_hand_qty']}"
                    )
            
            # Check for unusually high quantities
            high_qty_threshold = inventory_df['on_hand_qty'].quantile(0.99)
            high_qty = inventory_df[inventory_df['on_hand_qty'] > high_qty_threshold * 10]
            if len(high_qty) > 0:
                validation_results['warnings'].append(
                    f"{len(high_qty)} items have unusually high quantities (>10x 99th percentile)"
                )
        
        # Check for missing material IDs
        if 'material_id' in inventory_df.columns:
            missing_ids = inventory_df[inventory_df['material_id'].isna()]
            if len(missing_ids) > 0:
                validation_results['errors'].append(
                    f"{len(missing_ids)} items have missing material IDs"
                )
        
        # Check unit consistency
        if 'unit' in inventory_df.columns:
            unit_counts = inventory_df['unit'].value_counts()
            validation_results['info'].append(f"Units found: {unit_counts.to_dict()}")
            
            # Check for missing units
            missing_units = inventory_df[inventory_df['unit'].isna()]
            if len(missing_units) > 0:
                validation_results['warnings'].append(
                    f"{len(missing_units)} items have missing units"
                )
        
        # Info about data coverage
        validation_results['info'].append(f"Total inventory items: {len(inventory_df)}")
        validation_results['info'].append(
            f"Total on-hand quantity: {inventory_df['on_hand_qty'].sum():,.2f}"
        )
        
        if 'open_po_qty' in inventory_df.columns:
            validation_results['info'].append(
                f"Total open PO quantity: {inventory_df['open_po_qty'].sum():,.2f}"
            )
        
        return validation_results
    
    def enrich_inventory_data(self, inventory_df: pd.DataFrame, 
                            usage_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Enrich inventory data with calculated fields and analytics
        
        Args:
            inventory_df: DataFrame with inventory data
            usage_data: Optional DataFrame with historical usage data
            
        Returns:
            Enriched DataFrame
        """
        logger.info("Enriching inventory data...")
        
        # Add default values for missing fields
        if 'open_po_qty' not in inventory_df.columns:
            inventory_df['open_po_qty'] = 0
        else:
            inventory_df['open_po_qty'].fillna(0, inplace=True)
        
        if 'unit' not in inventory_df.columns:
            inventory_df['unit'] = 'yards'  # Default for yarn
        else:
            inventory_df['unit'].fillna('yards', inplace=True)
        
        if 'location' not in inventory_df.columns:
            inventory_df['location'] = 'MAIN'
        else:
            inventory_df['location'].fillna('MAIN', inplace=True)
        
        # Calculate total available (on-hand + incoming)
        inventory_df['total_available'] = (
            inventory_df['on_hand_qty'] + inventory_df['open_po_qty']
        )
        
        # Add usage analytics if usage data is provided
        if usage_data is not None and not usage_data.empty:
            inventory_df = self._add_usage_analytics(inventory_df, usage_data)
        else:
            # Add default usage metrics
            inventory_df['avg_daily_usage'] = 0
            inventory_df['days_of_supply'] = np.inf
            inventory_df['stock_status'] = 'unknown'
        
        # Calculate inventory value if price data is available
        if 'unit_cost' in inventory_df.columns:
            inventory_df['inventory_value'] = (
                inventory_df['on_hand_qty'] * inventory_df['unit_cost']
            )
            inventory_df['total_value'] = (
                inventory_df['total_available'] * inventory_df['unit_cost']
            )
        
        # Add inventory age if last receipt date is available
        if 'last_receipt_date' in inventory_df.columns:
            try:
                inventory_df['last_receipt_date'] = pd.to_datetime(
                    inventory_df['last_receipt_date']
                )
                inventory_df['days_since_receipt'] = (
                    datetime.now() - inventory_df['last_receipt_date']
                ).dt.days
                
                # Classify inventory age
                inventory_df['age_category'] = pd.cut(
                    inventory_df['days_since_receipt'],
                    bins=[0, 30, 90, 180, 365, np.inf],
                    labels=['Fresh', 'Current', 'Aging', 'Old', 'Obsolete']
                )
            except Exception as e:
                logger.warning(f"Failed to process receipt dates: {str(e)}")
        
        # Add ABC classification based on value or quantity
        inventory_df = self._add_abc_classification(inventory_df)
        
        logger.info(f"Enriched {len(inventory_df)} inventory records")
        
        return inventory_df
    
    def _add_usage_analytics(self, inventory_df: pd.DataFrame, 
                           usage_data: pd.DataFrame) -> pd.DataFrame:
        """Add usage-based analytics to inventory data"""
        # Calculate average daily usage from historical data
        usage_summary = usage_data.groupby('material_id').agg({
            'quantity': ['mean', 'std', 'count'],
            'date': ['min', 'max']
        })
        
        usage_summary.columns = ['avg_usage', 'std_usage', 'usage_count', 
                                'first_usage', 'last_usage']
        usage_summary['days_active'] = (
            usage_summary['last_usage'] - usage_summary['first_usage']
        ).dt.days + 1
        
        usage_summary['avg_daily_usage'] = (
            usage_summary['avg_usage'] / usage_summary['days_active']
        )
        
        # Merge with inventory
        inventory_df = inventory_df.merge(
            usage_summary[['avg_daily_usage', 'std_usage']], 
            left_on='material_id', 
            right_index=True, 
            how='left'
        )
        
        # Fill missing values
        inventory_df['avg_daily_usage'].fillna(0, inplace=True)
        inventory_df['std_usage'].fillna(0, inplace=True)
        
        # Calculate days of supply
        inventory_df['days_of_supply'] = np.where(
            inventory_df['avg_daily_usage'] > 0,
            inventory_df['total_available'] / inventory_df['avg_daily_usage'],
            np.inf
        )
        
        # Determine stock status
        inventory_df['stock_status'] = inventory_df.apply(
            lambda row: self._determine_stock_status(row), axis=1
        )
        
        return inventory_df
    
    def _determine_stock_status(self, row: pd.Series) -> str:
        """Determine stock status based on days of supply"""
        if row['days_of_supply'] == np.inf:
            if row['on_hand_qty'] > 0:
                return 'excess'
            else:
                return 'no_stock'
        elif row['days_of_supply'] <= self.thresholds['critical_stock_days']:
            return 'critical'
        elif row['days_of_supply'] <= self.thresholds['low_stock_days']:
            return 'low'
        elif row['days_of_supply'] >= self.thresholds['excess_stock_days']:
            return 'excess'
        else:
            return 'adequate'
    
    def _add_abc_classification(self, inventory_df: pd.DataFrame) -> pd.DataFrame:
        """Add ABC classification to inventory items"""
        # Use inventory value if available, otherwise use quantity
        if 'inventory_value' in inventory_df.columns:
            sort_column = 'inventory_value'
        else:
            sort_column = 'on_hand_qty'
        
        # Sort by value/quantity descending
        inventory_df = inventory_df.sort_values(sort_column, ascending=False)
        
        # Calculate cumulative percentage
        total_value = inventory_df[sort_column].sum()
        inventory_df['cumulative_pct'] = (
            inventory_df[sort_column].cumsum() / total_value * 100
        )
        
        # Assign ABC categories (80-15-5 rule)
        inventory_df['abc_category'] = pd.cut(
            inventory_df['cumulative_pct'],
            bins=[0, 80, 95, 100],
            labels=['A', 'B', 'C']
        )
        
        return inventory_df
    
    def identify_inventory_issues(self, inventory_df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify inventory issues requiring attention
        
        Args:
            inventory_df: Enriched inventory DataFrame
            
        Returns:
            DataFrame with identified issues
        """
        logger.info("Identifying inventory issues...")
        
        issues = []
        
        # Critical stock items
        if 'stock_status' in inventory_df.columns:
            critical_items = inventory_df[inventory_df['stock_status'] == 'critical']
            for _, item in critical_items.iterrows():
                issues.append({
                    'material_id': item['material_id'],
                    'issue_type': 'critical_stock',
                    'severity': 'high',
                    'current_qty': item['on_hand_qty'],
                    'days_of_supply': item.get('days_of_supply', 0),
                    'recommendation': 'Immediate reorder required'
                })
        
        # Excess stock items
        if 'stock_status' in inventory_df.columns:
            excess_items = inventory_df[inventory_df['stock_status'] == 'excess']
            for _, item in excess_items.iterrows():
                if item['on_hand_qty'] > 0:  # Only flag actual excess, not no-movement items
                    issues.append({
                        'material_id': item['material_id'],
                        'issue_type': 'excess_stock',
                        'severity': 'medium',
                        'current_qty': item['on_hand_qty'],
                        'days_of_supply': item.get('days_of_supply', 999),
                        'recommendation': 'Review usage patterns and adjust ordering'
                    })
        
        # Obsolete items
        if 'age_category' in inventory_df.columns:
            obsolete_items = inventory_df[inventory_df['age_category'] == 'Obsolete']
            for _, item in obsolete_items.iterrows():
                issues.append({
                    'material_id': item['material_id'],
                    'issue_type': 'obsolete_stock',
                    'severity': 'medium',
                    'current_qty': item['on_hand_qty'],
                    'days_since_receipt': item.get('days_since_receipt', 365),
                    'recommendation': 'Consider liquidation or write-off'
                })
        
        # High-value items with no movement
        if 'abc_category' in inventory_df.columns and 'avg_daily_usage' in inventory_df.columns:
            high_value_no_movement = inventory_df[
                (inventory_df['abc_category'] == 'A') & 
                (inventory_df['avg_daily_usage'] == 0) &
                (inventory_df['on_hand_qty'] > 0)
            ]
            for _, item in high_value_no_movement.iterrows():
                issues.append({
                    'material_id': item['material_id'],
                    'issue_type': 'high_value_no_movement',
                    'severity': 'high',
                    'current_qty': item['on_hand_qty'],
                    'inventory_value': item.get('inventory_value', 0),
                    'recommendation': 'Review demand forecast and consider reduction'
                })
        
        issues_df = pd.DataFrame(issues)
        logger.info(f"Identified {len(issues_df)} inventory issues")
        
        return issues_df
    
    def calculate_reorder_points(self, inventory_df: pd.DataFrame, 
                               lead_times: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Calculate reorder points and quantities
        
        Args:
            inventory_df: Enriched inventory DataFrame
            lead_times: Optional DataFrame with supplier lead times
            
        Returns:
            DataFrame with reorder recommendations
        """
        logger.info("Calculating reorder points...")
        
        reorder_df = inventory_df.copy()
        
        # Default lead time if not provided
        default_lead_time = 30
        
        if lead_times is not None and not lead_times.empty:
            # Merge lead time data
            reorder_df = reorder_df.merge(
                lead_times[['material_id', 'lead_time_days']], 
                on='material_id', 
                how='left'
            )
            reorder_df['lead_time_days'].fillna(default_lead_time, inplace=True)
        else:
            reorder_df['lead_time_days'] = default_lead_time
        
        # Calculate safety stock (using standard deviation if available)
        if 'std_usage' in reorder_df.columns:
            # Safety stock = Z-score * std deviation * sqrt(lead time)
            z_score = 1.65  # 95% service level
            reorder_df['safety_stock'] = (
                z_score * reorder_df['std_usage'] * np.sqrt(reorder_df['lead_time_days'])
            )
        else:
            # Simple safety stock as percentage of average usage
            reorder_df['safety_stock'] = (
                reorder_df['avg_daily_usage'] * reorder_df['lead_time_days'] * 0.25
            )
        
        # Calculate reorder point
        reorder_df['reorder_point'] = (
            reorder_df['avg_daily_usage'] * reorder_df['lead_time_days'] + 
            reorder_df['safety_stock']
        )
        
        # Calculate economic order quantity (simplified)
        # EOQ = sqrt(2 * annual demand * ordering cost / holding cost)
        # Using simplified assumptions
        ordering_cost = 100  # Per order
        holding_cost_pct = 0.25  # 25% of unit cost per year
        
        if 'unit_cost' in reorder_df.columns:
            annual_demand = reorder_df['avg_daily_usage'] * 365
            holding_cost = reorder_df['unit_cost'] * holding_cost_pct
            
            reorder_df['eoq'] = np.sqrt(
                2 * annual_demand * ordering_cost / holding_cost
            ).fillna(0)
        else:
            # Default EOQ as multiple of monthly usage
            reorder_df['eoq'] = reorder_df['avg_daily_usage'] * 30
        
        # Determine if reorder is needed
        reorder_df['reorder_needed'] = (
            reorder_df['total_available'] <= reorder_df['reorder_point']
        )
        
        # Calculate reorder quantity
        reorder_df['reorder_qty'] = np.where(
            reorder_df['reorder_needed'],
            np.maximum(
                reorder_df['eoq'],
                reorder_df['reorder_point'] - reorder_df['total_available']
            ),
            0
        )
        
        # Filter to items needing reorder
        reorder_recommendations = reorder_df[reorder_df['reorder_needed']][
            ['material_id', 'on_hand_qty', 'open_po_qty', 'total_available',
             'avg_daily_usage', 'reorder_point', 'reorder_qty', 'lead_time_days',
             'stock_status', 'abc_category']
        ].copy()
        
        logger.info(f"Generated {len(reorder_recommendations)} reorder recommendations")
        
        return reorder_recommendations
    
    def generate_inventory_report(self, inventory_df: pd.DataFrame, 
                                issues_df: Optional[pd.DataFrame] = None,
                                reorder_df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Generate comprehensive inventory analysis report
        
        Args:
            inventory_df: Enriched inventory DataFrame
            issues_df: Optional DataFrame with identified issues
            reorder_df: Optional DataFrame with reorder recommendations
            
        Returns:
            Dictionary with report data
        """
        report = {
            'summary': {
                'total_items': len(inventory_df),
                'total_on_hand_qty': inventory_df['on_hand_qty'].sum(),
                'total_open_po_qty': inventory_df['open_po_qty'].sum() if 'open_po_qty' in inventory_df.columns else 0,
                'total_available': inventory_df['total_available'].sum() if 'total_available' in inventory_df.columns else 0
            },
            'stock_status_distribution': {},
            'abc_distribution': {},
            'age_distribution': {},
            'top_items_by_value': [],
            'warnings': self.warnings,
            'errors': self.errors
        }
        
        # Stock status distribution
        if 'stock_status' in inventory_df.columns:
            report['stock_status_distribution'] = inventory_df['stock_status'].value_counts().to_dict()
        
        # ABC distribution
        if 'abc_category' in inventory_df.columns:
            report['abc_distribution'] = inventory_df['abc_category'].value_counts().to_dict()
        
        # Age distribution
        if 'age_category' in inventory_df.columns:
            report['age_distribution'] = inventory_df['age_category'].value_counts().to_dict()
        
        # Top items by value
        if 'inventory_value' in inventory_df.columns:
            top_items = inventory_df.nlargest(10, 'inventory_value')[
                ['material_id', 'on_hand_qty', 'inventory_value', 'abc_category']
            ]
            report['top_items_by_value'] = top_items.to_dict('records')
        
        # Add inventory value summary
        if 'inventory_value' in inventory_df.columns:
            report['summary']['total_inventory_value'] = inventory_df['inventory_value'].sum()
            report['summary']['avg_inventory_value'] = inventory_df['inventory_value'].mean()
        
        # Add issues summary
        if issues_df is not None and not issues_df.empty:
            report['issues'] = {
                'total_issues': len(issues_df),
                'by_type': issues_df['issue_type'].value_counts().to_dict(),
                'by_severity': issues_df['severity'].value_counts().to_dict(),
                'critical_items': issues_df[issues_df['severity'] == 'high']['material_id'].tolist()
            }
        
        # Add reorder summary
        if reorder_df is not None and not reorder_df.empty:
            report['reorders'] = {
                'items_to_reorder': len(reorder_df),
                'total_reorder_qty': reorder_df['reorder_qty'].sum(),
                'by_abc_category': reorder_df['abc_category'].value_counts().to_dict() if 'abc_category' in reorder_df.columns else {},
                'urgent_reorders': len(reorder_df[reorder_df['stock_status'] == 'critical']) if 'stock_status' in reorder_df.columns else 0
            }
        
        return report
    
    def export_inventory_data(self, inventory_df: pd.DataFrame, output_path: str):
        """Export enriched inventory data"""
        try:
            inventory_df.to_csv(output_path, index=False)
            logger.info(f"Exported inventory data to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export inventory data: {str(e)}")
            raise InventoryDataError(f"Export failed: {str(e)}")