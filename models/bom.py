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
        """Create BOM objects from DataFrame"""
        boms = []
        for _, row in df.iterrows():
            # Check if this is a percentage-based BOM
            percentage = row.get('percentage', None)
            if percentage is not None:
                bom = BillOfMaterials(
                    sku_id=str(row['sku_id']),
                    material_id=str(row['material_id']),
                    qty_per_unit=0,  # Will be calculated from percentage
                    unit=str(row.get('unit', 'yards')),
                    percentage=float(percentage)
                )
            else:
                bom = BillOfMaterials(
                    sku_id=str(row['sku_id']),
                    material_id=str(row['material_id']),
                    qty_per_unit=float(row['qty_per_unit']),
                    unit=str(row['unit'])
                )
            boms.append(bom)
        return boms
    
    @classmethod
    def from_style_yarn_dataframe(cls, df: pd.DataFrame) -> List[StyleYarnBOM]:
        """
        Create StyleYarnBOM objects from style-to-yarn DataFrame
        Enhanced to handle cfab_Yarn_Demand_By_Style.csv format
        """
        style_yarn_boms = []
        
        # Handle different possible column names
        style_col = 'Style' if 'Style' in df.columns else 'style_id'
        yarn_col = 'Yarn' if 'Yarn' in df.columns else ('Yarn ID' if 'Yarn ID' in df.columns else 'yarn_id')
        
        for _, row in df.iterrows():
            # Extract percentage from various possible formats
            percentage = cls._extract_percentage(row)
            if percentage > 0:
                style_yarn_bom = StyleYarnBOM(
                    style_id=str(row[style_col]),
                    yarn_id=str(row[yarn_col]),
                    percentage=percentage,
                    yarn_name=str(row.get('Yarn Name', '')) if 'Yarn Name' in row else None
                )
                style_yarn_boms.append(style_yarn_bom)
        
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