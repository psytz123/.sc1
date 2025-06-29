"""
Enhanced Style-to-Yarn BOM Integration Module

This module provides improved integration with cfab_Yarn_Demand_By_Style.csv
for accurate BOM explosion from style-level forecasts to yarn requirements.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class StyleYarnMapping:
    """Represents a style-to-yarn mapping with percentage and demand data"""
    style_id: str
    yarn_id: str
    percentage: float
    weekly_demands: Dict[str, float]  # Week -> Demand quantity
    total_demand: float
    
    def get_yarn_requirement(self, style_quantity: float) -> float:
        """Calculate yarn requirement based on style quantity and percentage"""
        return style_quantity * (self.percentage / 100.0)


class StyleYarnBOMIntegrator:
    """Handles integration with cfab_Yarn_Demand_By_Style.csv for BOM explosion"""
    
    def __init__(self, bom_file_path: str = "data/cfab_Yarn_Demand_By_Style.csv"):
        self.bom_file_path = bom_file_path
        self.style_yarn_mappings = {}
        self.yarn_master = {}
        self._load_bom_data()
    
    def _load_bom_data(self):
        """Load and parse the cfab_Yarn_Demand_By_Style.csv file"""
        try:
            # Read the CSV file
            df = pd.read_csv(self.bom_file_path)
            logger.info(f"Loaded BOM data with {len(df)} rows")
            
            # Process each row
            for _, row in df.iterrows():
                style_id = str(row['Style']).strip()
                yarn_id = str(row['Yarn']).strip()
                percentage = float(row['Percentage'])
                
                # Extract weekly demands
                weekly_demands = {}
                week_columns = [col for col in df.columns if col.startswith('Week') or col == 'This Week']
                
                for week_col in week_columns:
                    if pd.notna(row[week_col]) and row[week_col] != '':
                        # Handle comma-separated numbers
                        demand_str = str(row[week_col]).replace(',', '')
                        try:
                            weekly_demands[week_col] = float(demand_str)
                        except ValueError:
                            continue
                
                # Get total demand
                total_demand = 0.0
                if 'Total' in row and pd.notna(row['Total']):
                    total_str = str(row['Total']).replace(',', '')
                    try:
                        total_demand = float(total_str)
                    except ValueError:
                        total_demand = sum(weekly_demands.values())
                else:
                    total_demand = sum(weekly_demands.values())
                
                # Create mapping
                mapping = StyleYarnMapping(
                    style_id=style_id,
                    yarn_id=yarn_id,
                    percentage=percentage,
                    weekly_demands=weekly_demands,
                    total_demand=total_demand
                )
                
                # Store in lookup structure
                if style_id not in self.style_yarn_mappings:
                    self.style_yarn_mappings[style_id] = []
                self.style_yarn_mappings[style_id].append(mapping)
                
                # Track yarn IDs
                if yarn_id not in self.yarn_master:
                    self.yarn_master[yarn_id] = {
                        'yarn_id': yarn_id,
                        'styles': set(),
                        'total_demand': 0.0
                    }
                self.yarn_master[yarn_id]['styles'].add(style_id)
                self.yarn_master[yarn_id]['total_demand'] += total_demand
            
            # Validate percentages for each style
            self._validate_percentages()
            
            logger.info(f"Processed {len(self.style_yarn_mappings)} unique styles")
            logger.info(f"Found {len(self.yarn_master)} unique yarns")
            
        except Exception as e:
            logger.error(f"Error loading BOM data: {e}")
            raise
    
    def _validate_percentages(self):
        """Validate that percentages sum to 100% for each style"""
        for style_id, mappings in self.style_yarn_mappings.items():
            total_percentage = sum(m.percentage for m in mappings)
            if abs(total_percentage - 100.0) > 0.1:  # Allow small rounding errors
                logger.warning(
                    f"Style {style_id} yarn percentages sum to {total_percentage:.2f}%, not 100%"
                )
    
    def explode_style_forecast_to_yarn(self, 
                                     style_forecasts: Dict[str, float],
                                     unit: str = 'yards') -> Dict[str, Dict]:
        """
        Explode style-level forecasts to yarn requirements
        
        Args:
            style_forecasts: {style_id: forecast_quantity}
            unit: Unit of measurement (default: yards)
            
        Returns:
            {yarn_id: {
                'total_qty': float,
                'unit': str,
                'sources': [{'style_id': str, 'style_qty': float, 'percentage': float, 'yarn_qty': float}],
                'weekly_breakdown': Dict[str, float]
            }}
        """
        yarn_requirements = {}
        
        for style_id, forecast_qty in style_forecasts.items():
            if style_id not in self.style_yarn_mappings:
                logger.warning(f"No BOM found for style {style_id}")
                continue
            
            # Get all yarn mappings for this style
            mappings = self.style_yarn_mappings[style_id]
            
            for mapping in mappings:
                yarn_id = mapping.yarn_id
                yarn_qty = mapping.get_yarn_requirement(forecast_qty)
                
                if yarn_id not in yarn_requirements:
                    yarn_requirements[yarn_id] = {
                        'total_qty': 0.0,
                        'unit': unit,
                        'sources': [],
                        'weekly_breakdown': {}
                    }
                
                # Add to total
                yarn_requirements[yarn_id]['total_qty'] += yarn_qty
                
                # Add source details
                yarn_requirements[yarn_id]['sources'].append({
                    'style_id': style_id,
                    'style_qty': forecast_qty,
                    'percentage': mapping.percentage,
                    'yarn_qty': yarn_qty
                })
                
                # Calculate weekly breakdown if available
                if mapping.total_demand > 0:
                    for week, demand in mapping.weekly_demands.items():
                        week_ratio = demand / mapping.total_demand
                        week_yarn_qty = yarn_qty * week_ratio
                        
                        if week not in yarn_requirements[yarn_id]['weekly_breakdown']:
                            yarn_requirements[yarn_id]['weekly_breakdown'][week] = 0.0
                        yarn_requirements[yarn_id]['weekly_breakdown'][week] += week_yarn_qty
        
        return yarn_requirements
    
    def get_yarn_composition_for_style(self, style_id: str) -> List[Tuple[str, float]]:
        """Get yarn composition (yarn_id, percentage) for a specific style"""
        if style_id not in self.style_yarn_mappings:
            return []
        
        return [(m.yarn_id, m.percentage) for m in self.style_yarn_mappings[style_id]]
    
    def get_styles_using_yarn(self, yarn_id: str) -> List[str]:
        """Get all styles that use a specific yarn"""
        if yarn_id not in self.yarn_master:
            return []
        
        return list(self.yarn_master[yarn_id]['styles'])
    
    def convert_units(self, quantity: float, from_unit: str, to_unit: str) -> float:
        """
        Convert between common textile units
        
        Supported conversions:
        - yards <-> meters
        - pounds <-> kilograms (requires density information)
        """
        # Normalize unit names
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()
        
        # If same unit, no conversion needed
        if from_unit == to_unit:
            return quantity
        
        # Length conversions
        length_conversions = {
            ('yards', 'meters'): 0.9144,
            ('meters', 'yards'): 1.0936,
            ('yards', 'feet'): 3.0,
            ('feet', 'yards'): 0.3333,
            ('meters', 'feet'): 3.2808,
            ('feet', 'meters'): 0.3048
        }
        
        conversion_key = (from_unit, to_unit)
        if conversion_key in length_conversions:
            return quantity * length_conversions[conversion_key]
        
        # Weight conversions
        weight_conversions = {
            ('pounds', 'kilograms'): 0.4536,
            ('kilograms', 'pounds'): 2.2046,
            ('lbs', 'kg'): 0.4536,
            ('kg', 'lbs'): 2.2046
        }
        
        if conversion_key in weight_conversions:
            return quantity * weight_conversions[conversion_key]
        
        logger.warning(f"No conversion available from {from_unit} to {to_unit}")
        return quantity
    
    def generate_bom_report(self) -> pd.DataFrame:
        """Generate a summary report of the BOM data"""
        report_data = []
        
        for style_id, mappings in self.style_yarn_mappings.items():
            for mapping in mappings:
                report_data.append({
                    'Style': style_id,
                    'Yarn': mapping.yarn_id,
                    'Percentage': mapping.percentage,
                    'Total Demand': mapping.total_demand,
                    'Num Weeks': len(mapping.weekly_demands)
                })
        
        return pd.DataFrame(report_data)


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize integrator
    integrator = StyleYarnBOMIntegrator()
    
    # Example style forecasts
    style_forecasts = {
        '1853/L': 5000.0,  # 5000 yards of style 1853/L
        '180001/20ST2': 3000.0,  # 3000 yards of style 180001/20ST2
    }
    
    # Explode to yarn requirements
    yarn_requirements = integrator.explode_style_forecast_to_yarn(style_forecasts)
    
    # Print results
    print("\nYarn Requirements:")
    for yarn_id, req_data in yarn_requirements.items():
        print(f"\nYarn {yarn_id}:")
        print(f"  Total Required: {req_data['total_qty']:.2f} {req_data['unit']}")
        print(f"  Sources:")
        for source in req_data['sources']:
            print(f"    - Style {source['style_id']}: {source['yarn_qty']:.2f} "
                  f"({source['percentage']:.1f}% of {source['style_qty']:.0f})")