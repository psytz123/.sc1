"""
Supplier Integration Module
Handles supplier data integration, validation, and optimization
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SupplierIntegrationError(Exception):
    """Base exception for supplier integration errors"""
    pass

class SupplierDataError(SupplierIntegrationError):
    """Exception for supplier data issues"""
    pass

class SupplierValidationError(SupplierIntegrationError):
    """Exception for supplier validation failures"""
    pass

class SupplierIntegration:
    """Handles supplier data integration and optimization"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize supplier integration"""
        self.config = config or {}
        self.data_dir = self.config.get('data_directory', 'data')
        self.supplier_dir = os.path.join('integrations', 'suppliers')
        self.errors = []
        self.warnings = []
        
        # Supplier evaluation criteria weights
        self.evaluation_weights = self.config.get('supplier_evaluation_weights', {
            'price': 0.3,
            'lead_time': 0.25,
            'reliability': 0.25,
            'quality': 0.15,
            'payment_terms': 0.05
        })
        
    def load_supplier_data(self) -> pd.DataFrame:
        """
        Load supplier data from multiple sources
        
        Returns:
            DataFrame with consolidated supplier information
            
        Raises:
            SupplierDataError: If no supplier data can be loaded
        """
        logger.info("Loading supplier data from multiple sources...")
        
        supplier_sources = [
            os.path.join(self.supplier_dir, 'supplier_master.csv'),
            os.path.join(self.supplier_dir, 'supplier_list.csv'),
            os.path.join(self.data_dir, 'suppliers.csv'),
            os.path.join(self.data_dir, 'supplier_data.csv')
        ]
        
        supplier_dfs = []
        
        for source in supplier_sources:
            if os.path.exists(source):
                try:
                    df = pd.read_csv(source)
                    df['source_file'] = os.path.basename(source)
                    supplier_dfs.append(df)
                    logger.info(f"Loaded {len(df)} suppliers from {source}")
                except Exception as e:
                    logger.error(f"Failed to load {source}: {str(e)}")
                    self.errors.append(f"Failed to load {source}: {str(e)}")
        
        if not supplier_dfs:
            raise SupplierDataError("No supplier data files found")
        
        # Combine all supplier data
        combined_df = pd.concat(supplier_dfs, ignore_index=True)
        
        # Standardize column names
        column_mapping = {
            'Supplier ID': 'supplier_id',
            'Supplier_ID': 'supplier_id',
            'Supplier Name': 'supplier_name',
            'Supplier_Name': 'supplier_name',
            'Name': 'supplier_name',
            'Lead Time Days': 'lead_time_days',
            'Lead_Time_Days': 'lead_time_days',
            'Lead Time': 'lead_time_days',
            'MOQ': 'min_order_qty',
            'Min Order Qty': 'min_order_qty',
            'Min_Order_Qty': 'min_order_qty',
            'Price': 'price_per_unit',
            'Price Per Unit': 'price_per_unit',
            'Price_Per_Unit': 'price_per_unit',
            'Reliability': 'reliability_score',
            'Reliability Score': 'reliability_score',
            'Reliability_Score': 'reliability_score',
            'Payment Terms': 'payment_terms',
            'Payment_Terms': 'payment_terms',
            'Quality Score': 'quality_score',
            'Quality_Score': 'quality_score',
            'Materials': 'materials',
            'Material_List': 'materials',
            'Yarn_Types': 'materials'
        }
        
        combined_df.rename(columns=column_mapping, inplace=True)
        
        # Remove duplicates based on supplier_id
        if 'supplier_id' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=['supplier_id'], keep='first')
        
        logger.info(f"Loaded total of {len(combined_df)} unique suppliers")
        
        return combined_df
    
    def validate_supplier_data(self, supplier_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Validate supplier data for completeness and consistency
        
        Args:
            supplier_df: DataFrame with supplier data
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        # Check required columns
        required_columns = ['supplier_id', 'supplier_name', 'lead_time_days', 'price_per_unit']
        missing_columns = [col for col in required_columns if col not in supplier_df.columns]
        
        if missing_columns:
            validation_results['errors'].append(f"Missing required columns: {missing_columns}")
        
        # Validate data types and ranges
        if 'lead_time_days' in supplier_df.columns:
            invalid_lead_times = supplier_df[
                (supplier_df['lead_time_days'] < 0) | 
                (supplier_df['lead_time_days'] > 365)
            ]
            if len(invalid_lead_times) > 0:
                validation_results['warnings'].append(
                    f"{len(invalid_lead_times)} suppliers have invalid lead times"
                )
        
        if 'price_per_unit' in supplier_df.columns:
            invalid_prices = supplier_df[supplier_df['price_per_unit'] <= 0]
            if len(invalid_prices) > 0:
                validation_results['errors'].append(
                    f"{len(invalid_prices)} suppliers have invalid prices"
                )
        
        if 'reliability_score' in supplier_df.columns:
            invalid_reliability = supplier_df[
                (supplier_df['reliability_score'] < 0) | 
                (supplier_df['reliability_score'] > 1)
            ]
            if len(invalid_reliability) > 0:
                validation_results['warnings'].append(
                    f"{len(invalid_reliability)} suppliers have invalid reliability scores"
                )
        
        # Check for missing supplier names
        if 'supplier_name' in supplier_df.columns:
            missing_names = supplier_df[supplier_df['supplier_name'].isna()]
            if len(missing_names) > 0:
                validation_results['errors'].append(
                    f"{len(missing_names)} suppliers have missing names"
                )
        
        # Info about data coverage
        validation_results['info'].append(f"Total suppliers: {len(supplier_df)}")
        
        if 'materials' in supplier_df.columns:
            suppliers_with_materials = supplier_df[supplier_df['materials'].notna()]
            validation_results['info'].append(
                f"Suppliers with material info: {len(suppliers_with_materials)}"
            )
        
        return validation_results
    
    def enrich_supplier_data(self, supplier_df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich supplier data with calculated fields and defaults
        
        Args:
            supplier_df: DataFrame with supplier data
            
        Returns:
            Enriched DataFrame
        """
        logger.info("Enriching supplier data...")
        
        # Add default values for missing fields
        if 'reliability_score' not in supplier_df.columns:
            supplier_df['reliability_score'] = 0.8  # Default reliability
        else:
            supplier_df['reliability_score'].fillna(0.8, inplace=True)
        
        if 'quality_score' not in supplier_df.columns:
            supplier_df['quality_score'] = 0.85  # Default quality
        else:
            supplier_df['quality_score'].fillna(0.85, inplace=True)
        
        if 'payment_terms' not in supplier_df.columns:
            supplier_df['payment_terms'] = 'Net 30'
        else:
            supplier_df['payment_terms'].fillna('Net 30', inplace=True)
        
        if 'min_order_qty' not in supplier_df.columns:
            supplier_df['min_order_qty'] = 0
        else:
            supplier_df['min_order_qty'].fillna(0, inplace=True)
        
        # Calculate payment term days
        payment_term_mapping = {
            'Net 30': 30,
            'Net 60': 60,
            'Net 90': 90,
            'COD': 0,
            'Net 15': 15,
            'Net 45': 45
        }
        
        supplier_df['payment_term_days'] = supplier_df['payment_terms'].map(
            payment_term_mapping
        ).fillna(30)
        
        # Calculate composite score
        supplier_df['composite_score'] = self.calculate_supplier_scores(supplier_df)
        
        # Add supplier tier based on composite score
        supplier_df['tier'] = pd.cut(
            supplier_df['composite_score'],
            bins=[0, 0.6, 0.75, 0.85, 1.0],
            labels=['D', 'C', 'B', 'A']
        )
        
        # Calculate effective lead time (lead time + buffer based on reliability)
        supplier_df['effective_lead_time'] = supplier_df['lead_time_days'] * (
            1 + (1 - supplier_df['reliability_score']) * 0.2
        )
        
        logger.info(f"Enriched {len(supplier_df)} supplier records")
        
        return supplier_df
    
    def calculate_supplier_scores(self, supplier_df: pd.DataFrame) -> pd.Series:
        """
        Calculate composite scores for suppliers based on multiple criteria
        
        Args:
            supplier_df: DataFrame with supplier data
            
        Returns:
            Series with composite scores
        """
        scores = pd.Series(index=supplier_df.index, dtype=float)
        
        # Normalize each criterion to 0-1 scale
        # Price (lower is better)
        if 'price_per_unit' in supplier_df.columns:
            min_price = supplier_df['price_per_unit'].min()
            max_price = supplier_df['price_per_unit'].max()
            if max_price > min_price:
                price_score = 1 - (supplier_df['price_per_unit'] - min_price) / (max_price - min_price)
            else:
                price_score = 1.0
        else:
            price_score = 0.5
        
        # Lead time (lower is better)
        if 'lead_time_days' in supplier_df.columns:
            min_lead = supplier_df['lead_time_days'].min()
            max_lead = supplier_df['lead_time_days'].max()
            if max_lead > min_lead:
                lead_score = 1 - (supplier_df['lead_time_days'] - min_lead) / (max_lead - min_lead)
            else:
                lead_score = 1.0
        else:
            lead_score = 0.5
        
        # Reliability (higher is better)
        reliability_score = supplier_df.get('reliability_score', 0.8)
        
        # Quality (higher is better)
        quality_score = supplier_df.get('quality_score', 0.85)
        
        # Payment terms (longer is better for cash flow)
        if 'payment_term_days' in supplier_df.columns:
            payment_score = supplier_df['payment_term_days'] / 90  # Normalize to 90 days max
            payment_score = payment_score.clip(0, 1)
        else:
            payment_score = 0.5
        
        # Calculate weighted composite score
        scores = (
            self.evaluation_weights['price'] * price_score +
            self.evaluation_weights['lead_time'] * lead_score +
            self.evaluation_weights['reliability'] * reliability_score +
            self.evaluation_weights['quality'] * quality_score +
            self.evaluation_weights['payment_terms'] * payment_score
        )
        
        return scores
    
    def match_suppliers_to_materials(self, supplier_df: pd.DataFrame, 
                                   material_requirements: pd.DataFrame) -> pd.DataFrame:
        """
        Match suppliers to material requirements
        
        Args:
            supplier_df: DataFrame with supplier data
            material_requirements: DataFrame with material requirements
            
        Returns:
            DataFrame with supplier-material matches
        """
        logger.info("Matching suppliers to material requirements...")
        
        matches = []
        
        for _, req in material_requirements.iterrows():
            material_id = req.get('material_id', req.get('Material_ID', ''))
            
            # Find suppliers that can provide this material
            if 'materials' in supplier_df.columns:
                # Check if material is in supplier's material list
                material_suppliers = supplier_df[
                    supplier_df['materials'].str.contains(material_id, na=False, case=False)
                ]
            else:
                # If no material info, assume all suppliers can provide all materials
                material_suppliers = supplier_df
            
            if len(material_suppliers) == 0:
                self.warnings.append(f"No suppliers found for material {material_id}")
                continue
            
            # Sort by composite score
            material_suppliers = material_suppliers.sort_values(
                'composite_score', ascending=False
            )
            
            # Add top 3 suppliers for each material
            for _, supplier in material_suppliers.head(3).iterrows():
                match = {
                    'material_id': material_id,
                    'supplier_id': supplier['supplier_id'],
                    'supplier_name': supplier['supplier_name'],
                    'price_per_unit': supplier['price_per_unit'],
                    'lead_time_days': supplier['lead_time_days'],
                    'min_order_qty': supplier['min_order_qty'],
                    'reliability_score': supplier['reliability_score'],
                    'composite_score': supplier['composite_score'],
                    'tier': supplier['tier'],
                    'required_qty': req.get('required_qty', 0)
                }
                matches.append(match)
        
        matches_df = pd.DataFrame(matches)
        logger.info(f"Created {len(matches_df)} supplier-material matches")
        
        return matches_df
    
    def optimize_supplier_selection(self, matches_df: pd.DataFrame, 
                                  constraints: Optional[Dict] = None) -> pd.DataFrame:
        """
        Optimize supplier selection based on constraints and objectives
        
        Args:
            matches_df: DataFrame with supplier-material matches
            constraints: Optional constraints (max suppliers, budget, etc.)
            
        Returns:
            DataFrame with optimized supplier selections
        """
        logger.info("Optimizing supplier selection...")
        
        constraints = constraints or {}
        max_suppliers_per_material = constraints.get('max_suppliers_per_material', 2)
        prefer_tier_a = constraints.get('prefer_tier_a', True)
        
        selections = []
        
        # Group by material
        for material_id, group in matches_df.groupby('material_id'):
            # Sort by composite score and tier
            if prefer_tier_a:
                group = group.sort_values(['tier', 'composite_score'], ascending=[True, False])
            else:
                group = group.sort_values('composite_score', ascending=False)
            
            # Select top suppliers based on constraints
            selected = group.head(max_suppliers_per_material)
            
            # Calculate allocation percentages
            if len(selected) == 1:
                selected['allocation_pct'] = 100
            else:
                # Allocate based on composite scores
                score_sum = selected['composite_score'].sum()
                selected['allocation_pct'] = (
                    selected['composite_score'] / score_sum * 100
                ).round(1)
            
            selections.append(selected)
        
        optimized_df = pd.concat(selections, ignore_index=True)
        
        # Add risk assessment
        optimized_df['risk_level'] = optimized_df.apply(
            lambda row: self._assess_supplier_risk(row), axis=1
        )
        
        logger.info(f"Optimized selection: {len(optimized_df)} supplier-material pairs")
        
        return optimized_df
    
    def _assess_supplier_risk(self, supplier_row: pd.Series) -> str:
        """Assess risk level for a supplier"""
        risk_score = 0
        
        # Lead time risk
        if supplier_row['lead_time_days'] > 60:
            risk_score += 2
        elif supplier_row['lead_time_days'] > 30:
            risk_score += 1
        
        # Reliability risk
        if supplier_row['reliability_score'] < 0.7:
            risk_score += 2
        elif supplier_row['reliability_score'] < 0.85:
            risk_score += 1
        
        # Tier risk
        if supplier_row['tier'] == 'D':
            risk_score += 2
        elif supplier_row['tier'] == 'C':
            risk_score += 1
        
        # Map to risk level
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def generate_supplier_report(self, supplier_df: pd.DataFrame, 
                               selections_df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Generate comprehensive supplier analysis report
        
        Args:
            supplier_df: DataFrame with all supplier data
            selections_df: Optional DataFrame with selected suppliers
            
        Returns:
            Dictionary with report data
        """
        report = {
            'summary': {
                'total_suppliers': len(supplier_df),
                'active_suppliers': len(supplier_df[supplier_df['composite_score'] > 0.6]),
                'avg_lead_time': supplier_df['lead_time_days'].mean(),
                'avg_reliability': supplier_df['reliability_score'].mean(),
                'tier_distribution': supplier_df['tier'].value_counts().to_dict()
            },
            'top_suppliers': supplier_df.nlargest(10, 'composite_score')[
                ['supplier_id', 'supplier_name', 'composite_score', 'tier']
            ].to_dict('records'),
            'warnings': self.warnings,
            'errors': self.errors
        }
        
        if selections_df is not None and not selections_df.empty:
            report['selections'] = {
                'total_selections': len(selections_df),
                'unique_materials': selections_df['material_id'].nunique(),
                'risk_distribution': selections_df['risk_level'].value_counts().to_dict(),
                'total_value': (
                    selections_df['required_qty'] * selections_df['price_per_unit']
                ).sum() if 'required_qty' in selections_df.columns else 0
            }
        
        return report
    
    def export_supplier_data(self, supplier_df: pd.DataFrame, output_path: str):
        """Export enriched supplier data"""
        try:
            supplier_df.to_csv(output_path, index=False)
            logger.info(f"Exported supplier data to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export supplier data: {str(e)}")
            raise SupplierDataError(f"Export failed: {str(e)}")