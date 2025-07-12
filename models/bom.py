"""
Bill of Materials (BOM) Data Model
Enhanced to support style-to-yarn conversion with percentage-based composition
"""

from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class BillOfMaterials:
    """Represents a BOM entry linking SKU to raw materials"""
    sku_id: str
    material_id: str
    qty_per_unit: float
    unit: str
    percentage: Optional[float] = None  # For percentage-based BOMs (e.g., yarn composition)
    
    def __post_init__(self):
        """Validate BOM data"""
        if self.qty_per_unit <= 0 and (self.percentage is None or self.percentage <= 0):
            raise ValueError("Either quantity per unit or percentage must be positive")
        if self.percentage is not None and (self.percentage < 0 or self.percentage > 100):
            raise ValueError("Percentage must be between 0 and 100")


@dataclass
class StyleYarnBOM:
    """Represents style-to-yarn BOM with percentage composition"""
    style_id: str
    yarn_id: str
    percentage: float
    yarn_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate style-yarn BOM data"""
        if self.percentage <= 0 or self.percentage > 100:
            raise ValueError(f"Invalid percentage {self.percentage} for style {self.style_id}")


class BOMExploder:
    """Handles BOM explosion logic with enhanced style-to-yarn conversion"""
    
    # Unit conversion factors to yards
    UNIT_CONVERSIONS = {
        'yards': 1.0,
        'yds': 1.0,
        'meters': 1.0936,
        'm': 1.0936,
        'feet': 0.3333,
        'ft': 0.3333,
        'pounds': None,  # Requires density for conversion
        'lbs': None,
        'kilograms': None,
        'kg': None
    }
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> List[BillOfMaterials]:
        """Create BOM objects from DataFrame - optimized version"""
        boms = []

        # Validate required columns
        required_columns = ['sku_id', 'material_id', 'qty_per_unit']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Prepare data with proper types
        df = df.copy()
        df['sku_id'] = df['sku_id'].astype(str)
        df['material_id'] = df['material_id'].astype(str)
        df['qty_per_unit'] = pd.to_numeric(df['qty_per_unit'], errors='coerce')
        df['unit_of_measure'] = df.get('unit_of_measure', 'unit').astype(str)

        # Filter out invalid rows
        invalid_rows = df[df['qty_per_unit'].isna() | (df['qty_per_unit'] <= 0)]
        if not invalid_rows.empty:
            logger.warning(f"Filtering out {len(invalid_rows)} invalid BOM rows")
            df = df[~df['qty_per_unit'].isna() & (df['qty_per_unit'] > 0)]

        # Convert to list of dictionaries for faster iteration
        bom_data = df.to_dict('records')

        for row in bom_data:
            try:
                bom = BillOfMaterials(
                    sku_id=row['sku_id'],
                    material_id=row['material_id'],
                    qty_per_unit=float(row['qty_per_unit']),
                    unit_of_measure=row['unit_of_measure']
                )
                boms.append(bom)
            except Exception as e:
                logger.error(f"Error creating BOM from row: {e}")
                continue

        logger.info(f"Successfully created {len(boms)} BOM entries from {len(df)} rows")
        return boms

    @classmethod
    def from_style_yarn_dataframe(cls, df: pd.DataFrame) -> List[StyleYarnBOM]:
        """
        Create StyleYarnBOM objects from style-to-yarn DataFrame - optimized version
        Enhanced to handle cfab_Yarn_Demand_By_Style.csv format
        """
        style_yarn_boms = []

        # Handle different possible column names
        style_col = 'Style' if 'Style' in df.columns else 'style_id'
        yarn_col = 'Yarn' if 'Yarn' in df.columns else ('Yarn ID' if 'Yarn ID' in df.columns else 'yarn_id')

        # Validate required columns
        if style_col not in df.columns:
            raise ValueError(f"Style column not found. Available columns: {list(df.columns)}")
        if yarn_col not in df.columns:
            raise ValueError(f"Yarn column not found. Available columns: {list(df.columns)}")

        # Prepare data
        df = df.copy()
        df[style_col] = df[style_col].astype(str)
        df[yarn_col] = df[yarn_col].astype(str)

        # Extract percentages for all rows at once
        df['percentage'] = df.apply(cls._extract_percentage, axis=1)

        # Filter out zero percentages
        valid_df = df[df['percentage'] > 0]

        # Convert to list of dictionaries for faster iteration
        style_yarn_data = valid_df.to_dict('records')

        for row in style_yarn_data:
            try:
                style_yarn_bom = StyleYarnBOM(
                    style_id=row[style_col],
                    yarn_id=row[yarn_col],
                    percentage=row['percentage'],
                    yarn_name=str(row.get('Yarn Name', '')) if 'Yarn Name' in row else None
                )
                style_yarn_boms.append(style_yarn_bom)
            except Exception as e:
                logger.error(f"Error creating StyleYarnBOM from row: {e}")
                continue

        logger.info(f"Successfully created {len(style_yarn_boms)} style-yarn BOM entries from {len(df)} rows")
        return style_yarn_boms
    
    @classmethod
    def _extract_percentage(cls, row: pd.Series) -> float:
        """Extract percentage from various column formats"""
        # Try different percentage column names
        percentage_cols = ['Percentage', 'percentage', '%', 'Percent', 'percent']
        
        for col in percentage_cols:
            if col in row and pd.notna(row[col]):
                val = str(row[col]).strip()
                # Remove % sign if present
                val = val.replace('%', '').strip()
                try:
                    return float(val)
                except ValueError:
                    continue
        
        # If no percentage column found, check if there are yarn-specific columns
        # e.g., "Yarn 1 %", "Yarn 2 %", etc.
        for col in row.index:
            if '%' in str(col) and pd.notna(row[col]):
                val = str(row[col]).strip().replace('%', '')
                try:
                    return float(val)
                except ValueError:
                    continue
        
        return 0.0
    
    @classmethod
    def explode_requirements(cls,
                           sku_forecasts: Dict[str, float],
                           boms: List[BillOfMaterials]) -> Dict[str, Dict]:
        """
        Explode SKU forecasts into material requirements
        
        Args:
            sku_forecasts: {sku_id: forecast_qty}
            boms: List of BOM entries
            
        Returns:
            {material_id: {'total_qty': float, 'unit': str, 'sources': [...]}}
        """
        material_requirements = {}
        
        # Create BOM lookup for efficiency
        bom_lookup = {}
        for bom in boms:
            if bom.sku_id not in bom_lookup:
                bom_lookup[bom.sku_id] = []
            bom_lookup[bom.sku_id].append(bom)
        
        # Explode each SKU forecast
        for sku_id, forecast_qty in sku_forecasts.items():
            if sku_id in bom_lookup:
                for bom in bom_lookup[sku_id]:
                    # Calculate material quantity
                    if bom.percentage is not None:
                        # For percentage-based BOMs, calculate based on percentage
                        material_qty = forecast_qty * (bom.percentage / 100.0)
                    else:
                        material_qty = forecast_qty * bom.qty_per_unit
                    
                    if bom.material_id not in material_requirements:
                        material_requirements[bom.material_id] = {
                            'total_qty': 0.0,
                            'unit': bom.unit,
                            'sources': []
                        }
                    
                    material_requirements[bom.material_id]['total_qty'] += material_qty
                    material_requirements[bom.material_id]['sources'].append({
                        'sku_id': sku_id,
                        'forecast_qty': forecast_qty,
                        'qty_per_unit': bom.qty_per_unit if bom.percentage is None else bom.percentage / 100.0,
                        'material_qty': material_qty,
                        'is_percentage': bom.percentage is not None
                    })
        
        return material_requirements
    
    @classmethod
    def explode_style_to_yarn_requirements(cls,
                                         style_forecasts: Dict[str, float],
                                         style_yarn_boms: List[StyleYarnBOM],
                                         unit: str = 'yards') -> Dict[str, Dict]:
        """
        Explode style forecasts into yarn requirements using percentage-based BOMs
        Enhanced to handle unit conversions and validation
        
        Args:
            style_forecasts: {style_id: forecast_qty_in_yards}
            style_yarn_boms: List of style-to-yarn BOM entries
            unit: Unit of the style forecast (default: yards)
            
        Returns:
            {yarn_id: {'total_qty': float, 'unit': str, 'sources': [...], 'yarn_name': str}}
        """
        yarn_requirements = {}
        
        # Create style-yarn lookup
        style_yarn_lookup = {}
        for bom in style_yarn_boms:
            if bom.style_id not in style_yarn_lookup:
                style_yarn_lookup[bom.style_id] = []
            style_yarn_lookup[bom.style_id].append(bom)
        
        # Validate that percentages sum to 100% for each style
        validation_warnings = []
        for style_id, yarn_boms in style_yarn_lookup.items():
            total_percentage = sum(bom.percentage for bom in yarn_boms)
            if abs(total_percentage - 100.0) > 0.1:  # Allow small rounding errors
                warning = f"Style {style_id} yarn percentages sum to {total_percentage:.2f}%, not 100%"
                validation_warnings.append(warning)
                logger.info(f"Warning: {warning}")
        
        # Explode each style forecast
        for style_id, forecast_qty in style_forecasts.items():
            if style_id in style_yarn_lookup:
                for bom in style_yarn_lookup[style_id]:
                    # Calculate yarn quantity based on percentage
                    yarn_qty = forecast_qty * (bom.percentage / 100.0)
                    
                    if bom.yarn_id not in yarn_requirements:
                        yarn_requirements[bom.yarn_id] = {
                            'total_qty': 0.0,
                            'unit': unit,
                            'sources': [],
                            'yarn_name': bom.yarn_name or bom.yarn_id
                        }
                    
                    yarn_requirements[bom.yarn_id]['total_qty'] += yarn_qty
                    yarn_requirements[bom.yarn_id]['sources'].append({
                        'style_id': style_id,
                        'style_forecast_qty': forecast_qty,
                        'percentage': bom.percentage,
                        'yarn_qty': yarn_qty
                    })
            else:
                # Log styles without BOM data
                logger.info(f"Info: No BOM data found for style {style_id}")
        
        # Add validation warnings to the result
        if validation_warnings:
            yarn_requirements['_validation_warnings'] = validation_warnings
        
        return yarn_requirements
    
    @classmethod
    def convert_units(cls, quantity: float, from_unit: str, to_unit: str, 
                     density: Optional[float] = None) -> Tuple[float, bool]:
        """
        Convert quantity between units
        
        Args:
            quantity: Quantity to convert
            from_unit: Source unit
            to_unit: Target unit
            density: Material density (required for weight<->length conversions)
            
        Returns:
            (converted_quantity, success)
        """
        # Normalize units
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()
        
        # Same unit, no conversion needed
        if from_unit == to_unit:
            return quantity, True
        
        # Check if conversion factor exists
        if from_unit in cls.UNIT_CONVERSIONS and to_unit == 'yards':
            factor = cls.UNIT_CONVERSIONS[from_unit]
            if factor is not None:
                return quantity * factor, True
        elif to_unit in cls.UNIT_CONVERSIONS and from_unit == 'yards':
            factor = cls.UNIT_CONVERSIONS[to_unit]
            if factor is not None:
                return quantity / factor, True
        
        # Handle weight-to-length conversions (requires density)
        if density and from_unit in ['pounds', 'lbs', 'kilograms', 'kg']:
            # Convert to standard weight unit (kg)
            weight_kg = quantity
            if from_unit in ['pounds', 'lbs']:
                weight_kg = quantity * 0.453592
            
            # Convert to length using density (assuming density is in kg/yard)
            if to_unit in ['yards', 'yds']:
                return weight_kg / density, True
            elif to_unit in ['meters', 'm']:
                yards = weight_kg / density
                return yards * 0.9144, True
        
        return quantity, False
    
    @classmethod
    def validate_bom_data(cls, boms: List[BillOfMaterials]) -> List[str]:
        """Validate BOM data and return list of issues"""
        issues = []
        
        # Check for duplicate entries
        seen = set()
        for bom in boms:
            key = (bom.sku_id, bom.material_id)
            if key in seen:
                issues.append(f"Duplicate BOM entry for SKU {bom.sku_id} and material {bom.material_id}")
            seen.add(key)
        
        # Check for invalid quantities
        for bom in boms:
            if bom.qty_per_unit <= 0 and (bom.percentage is None or bom.percentage <= 0):
                issues.append(f"Invalid quantity for BOM: SKU {bom.sku_id}, material {bom.material_id}")
        
        return issues
    
    @classmethod
    def merge_requirements(cls, *requirement_dicts: Dict[str, Dict]) -> Dict[str, Dict]:
        """Merge multiple requirement dictionaries"""
        merged = {}
        
        for req_dict in requirement_dicts:
            for material_id, req_data in req_dict.items():
                if material_id == '_validation_warnings':
                    continue
                    
                if material_id not in merged:
                    merged[material_id] = {
                        'total_qty': 0.0,
                        'unit': req_data['unit'],
                        'sources': []
                    }
                
                merged[material_id]['total_qty'] += req_data['total_qty']
                merged[material_id]['sources'].extend(req_data['sources'])
        
        return merged

    @classmethod
    def from_live_data_format(cls, df: pd.DataFrame) -> List[BillOfMaterials]:
        """Create BOM objects from live data format (Style_ID, Yarn_ID, BOM_Percentage)"""
        boms = []

        # Validate required columns for live data format
        required_columns = ['Style_ID', 'Yarn_ID', 'BOM_Percentage']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns for live data: {missing_columns}")

        # Prepare data with proper types
        df = df.copy()
        df['Style_ID'] = df['Style_ID'].astype(str)
        df['Yarn_ID'] = df['Yarn_ID'].astype(str)
        df['BOM_Percentage'] = pd.to_numeric(df['BOM_Percentage'], errors='coerce')

        # Filter out invalid rows
        invalid_rows = df[df['BOM_Percentage'].isna() | (df['BOM_Percentage'] <= 0)]
        if not invalid_rows.empty:
            logger.warning(f"Filtering out {len(invalid_rows)} invalid BOM rows")
            df = df[~df['BOM_Percentage'].isna() & (df['BOM_Percentage'] > 0)]

        # Convert to list of dictionaries for faster iteration
        bom_data = df.to_dict('records')

        for row in bom_data:
            try:
                bom = BillOfMaterials(
                    sku_id=row['Style_ID'],
                    material_id=row['Yarn_ID'],
                    qty_per_unit=float(row['BOM_Percentage']),
                    unit="percentage",
                    percentage=float(row['BOM_Percentage']) * 100  # Convert to 0-100 scale
                )
                boms.append(bom)
            except Exception as e:
                logger.error(f"Error creating BOM from live data row: {e}")
                continue

        logger.info(f"Successfully created {len(boms)} BOM entries from live data format")
        return boms

    @classmethod
    def from_yarn_demand_by_style(cls, df: pd.DataFrame) -> List[StyleYarnBOM]:
        """
        Create StyleYarnBOM objects from cfab_Yarn_Demand_By_Style.csv format
        Enhanced to handle live data format exactly
        """
        style_yarn_boms = []

        # Validate required columns for yarn demand format
        required_columns = ['Style', 'Yarn', 'Percentage']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns for yarn demand: {missing_columns}")

        # Prepare data
        df = df.copy()
        df['Style'] = df['Style'].astype(str)
        df['Yarn'] = df['Yarn'].astype(str)
        df['Percentage'] = pd.to_numeric(df['Percentage'], errors='coerce')

        # Filter out invalid rows
        valid_df = df[df['Percentage'] > 0]

        # Convert to list of dictionaries for faster iteration
        style_yarn_data = valid_df.to_dict('records')

        for row in style_yarn_data:
            try:
                style_yarn_bom = StyleYarnBOM(
                    style_id=row['Style'],
                    yarn_id=row['Yarn'],
                    percentage=row['Percentage']  # Already in 0-100 scale in live data
                )
                style_yarn_boms.append(style_yarn_bom)
            except Exception as e:
                logger.error(f"Error creating StyleYarnBOM from yarn demand row: {e}")
                continue

        logger.info(f"Successfully created {len(style_yarn_boms)} style-yarn BOM entries from yarn demand format")
        return style_yarn_boms

    @classmethod
    def validate_live_data_boms(cls, style_bom_df: pd.DataFrame, yarn_demand_df: pd.DataFrame = None) -> Dict[str, any]:
        """Validate BOM data from live data format"""
        validation_results = {
            'style_bom_validation': {},
            'yarn_demand_validation': {},
            'cross_validation': {}
        }
        
        # Validate Style_BOM.csv format
        if not style_bom_df.empty:
            # Group by style and check percentage totals
            style_totals = style_bom_df.groupby('Style_ID')['BOM_Percentage'].sum()
            
            # Find styles with incorrect totals (should sum to 1.0)
            incorrect_totals = {
                style: total for style, total in style_totals.items()
                if abs(total - 1.0) > 0.01  # Allow small rounding errors
            }
            
            validation_results['style_bom_validation'] = {
                'total_bom_lines': len(style_bom_df),
                'unique_styles': len(style_totals),
                'styles_with_incorrect_totals': len(incorrect_totals),
                'incorrect_total_details': incorrect_totals,
                'average_total': style_totals.mean(),
                'min_total': style_totals.min(),
                'max_total': style_totals.max()
            }
        
        # Validate yarn demand format if provided
        if yarn_demand_df is not None and not yarn_demand_df.empty:
            # Group by style and check percentage totals
            style_percentages = yarn_demand_df.groupby('Style')['Percentage'].sum()
            
            # Find styles with incorrect percentage totals (should sum to 100.0)
            incorrect_percentages = {
                style: total for style, total in style_percentages.items()
                if abs(total - 100.0) > 0.1
            }
            
            validation_results['yarn_demand_validation'] = {
                'total_records': len(yarn_demand_df),
                'unique_styles': len(style_percentages),
                'styles_with_incorrect_percentages': len(incorrect_percentages),
                'incorrect_percentage_details': incorrect_percentages,
                'average_percentage': style_percentages.mean(),
                'min_percentage': style_percentages.min(),
                'max_percentage': style_percentages.max()
            }
            
            # Cross-validation between the two formats
            style_bom_styles = set(style_bom_df['Style_ID'].unique())
            yarn_demand_styles = set(yarn_demand_df['Style'].unique())
            
            validation_results['cross_validation'] = {
                'styles_in_both': len(style_bom_styles & yarn_demand_styles),
                'styles_only_in_bom': len(style_bom_styles - yarn_demand_styles),
                'styles_only_in_demand': len(yarn_demand_styles - style_bom_styles),
                'styles_only_in_bom_list': list(style_bom_styles - yarn_demand_styles),
                'styles_only_in_demand_list': list(yarn_demand_styles - style_bom_styles)
            }
        
        return validation_results