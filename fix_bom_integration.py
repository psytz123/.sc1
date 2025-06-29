#!/usr/bin/env python3
"""
Fix BOM Integration Issues
Addresses the critical data quality problems identified in BOM_Discrepancy_Report.md
"""

import logging
from pathlib import Path

import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_original_bom_data():
    """Load the original Style_BOM.csv data"""
    try:
        # Try multiple possible locations
        possible_paths = [
            'data/Style_BOM.csv',
            'Style_BOM.csv',
            'data/raw/Style_BOM.csv'
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                logger.info(f"Loading Style_BOM from: {path}")
                return pd.read_csv(path)
        
        raise FileNotFoundError("Style_BOM.csv not found in expected locations")
    except Exception as e:
        logger.error(f"Error loading Style_BOM: {e}")
        raise

def validate_bom_completeness(bom_df):
    """Validate that BOMs sum to approximately 100%"""
    issues = []
    
    # Group by SKU and sum percentages
    sku_totals = bom_df.groupby('sku')['percentage'].sum()
    
    # Find SKUs that don't sum to ~100%
    tolerance = 0.01  # 1% tolerance
    incomplete_skus = sku_totals[(sku_totals < (1.0 - tolerance)) | (sku_totals > (1.0 + tolerance))]
    
    for sku, total in incomplete_skus.items():
        issues.append({
            'sku': sku,
            'total_percentage': total,
            'issue': 'incomplete' if total < 1.0 else 'exceeds_100'
        })
    
    return issues

def fix_bom_data(bom_df):
    """Fix BOM data issues while preserving all materials"""
    fixed_df = bom_df.copy()
    
    # 1. Handle floating point precision
    fixed_df['percentage'] = fixed_df['percentage'].round(6)
    
    # 2. Group by SKU to handle completeness
    sku_groups = fixed_df.groupby('sku')
    fixed_rows = []
    
    for sku, group in sku_groups:
        total = group['percentage'].sum()
        
        if abs(total - 1.0) < 0.001:  # Already sums to ~100%
            fixed_rows.extend(group.to_dict('records'))
        elif total > 0.99 and total < 1.01:  # Very close to 100%, just normalize
            group_copy = group.copy()
            group_copy['percentage'] = group_copy['percentage'] / total
            fixed_rows.extend(group_copy.to_dict('records'))
        else:
            # Log issue but keep original data
            logger.warning(f"SKU {sku} has total percentage of {total:.2%} - keeping original values")
            fixed_rows.extend(group.to_dict('records'))
    
    return pd.DataFrame(fixed_rows)

def create_corrected_bom_file(output_path='data/corrected_bom.csv'):
    """Create a corrected BOM file that preserves all materials"""
    logger.info("Starting BOM correction process...")
    
    # Load original data
    bom_df = load_original_bom_data()
    logger.info(f"Loaded {len(bom_df)} BOM entries for {bom_df['sku'].nunique()} SKUs")
    
    # Validate completeness
    issues = validate_bom_completeness(bom_df)
    if issues:
        logger.warning(f"Found {len(issues)} SKUs with completeness issues")
        issues_df = pd.DataFrame(issues)
        issues_df.to_csv('bom_completeness_issues.csv', index=False)
        logger.info("Saved completeness issues to bom_completeness_issues.csv")
    
    # Fix data
    fixed_df = fix_bom_data(bom_df)
    
    # Validate the fix
    fixed_issues = validate_bom_completeness(fixed_df)
    logger.info(f"After fixes: {len(fixed_issues)} SKUs still have issues")
    
    # Save corrected data
    fixed_df.to_csv(output_path, index=False)
    logger.info(f"Saved corrected BOM to {output_path}")
    
    # Generate summary report
    report = {
        'original_entries': len(bom_df),
        'fixed_entries': len(fixed_df),
        'original_skus': bom_df['sku'].nunique(),
        'fixed_skus': fixed_df['sku'].nunique(),
        'original_materials': bom_df['material_id'].nunique(),
        'fixed_materials': fixed_df['material_id'].nunique(),
        'completeness_issues_before': len(issues),
        'completeness_issues_after': len(fixed_issues)
    }
    
    return report

if __name__ == "__main__":
    report = create_corrected_bom_file()
    print("\nBOM Correction Report:")
    for key, value in report.items():
        print(f"  {key}: {value}")