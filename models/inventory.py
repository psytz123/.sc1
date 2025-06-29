"""
Inventory Data Model
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class Inventory:
    """Represents current inventory status for a material"""
    material_id: str
    on_hand_qty: float
    unit: str
    open_po_qty: float = 0.0
    po_expected_date: Optional[date] = None
    
    def __post_init__(self):
        """Validate inventory data"""
        if self.on_hand_qty < 0:
            raise ValueError("On-hand quantity cannot be negative")
        if self.open_po_qty < 0:
            raise ValueError("Open PO quantity cannot be negative")


class InventoryNetter:
    """Handles inventory netting calculations"""
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> List[Inventory]:
        """Create inventory objects from DataFrame"""
        inventories = []
        for _, row in df.iterrows():
            po_date = None
            if pd.notna(row.get('po_expected_date')):
                po_date = pd.to_datetime(row['po_expected_date']).date()
            
            inventory = Inventory(
                material_id=str(row['material_id']),
                on_hand_qty=float(row['on_hand_qty']),
                unit=str(row['unit']),
                open_po_qty=float(row.get('open_po_qty', 0.0)),
                po_expected_date=po_date
            )
            inventories.append(inventory)
        return inventories
    
    @classmethod
    def calculate_net_requirements(cls, 
                                 material_requirements: Dict[str, Dict],
                                 inventories: List[Inventory]) -> Dict[str, Dict]:
        """
        Calculate net material requirements after inventory netting
        
        Args:
            material_requirements: From BOM explosion
            inventories: Current inventory status
            
        Returns:
            {material_id: {
                'gross_requirement': float,
                'on_hand_qty': float,
                'open_po_qty': float,
                'net_requirement': float,
                'unit': str,
                'inventory_status': str
            }}
        """
        # Create inventory lookup
        inventory_lookup = {inv.material_id: inv for inv in inventories}
        
        net_requirements = {}
        
        for material_id, req_data in material_requirements.items():
            gross_requirement = req_data['total_qty']
            unit = req_data['unit']
            
            # Get inventory data
            inventory = inventory_lookup.get(material_id)
            on_hand = inventory.on_hand_qty if inventory else 0.0
            open_po = inventory.open_po_qty if inventory else 0.0
            
            # Calculate net requirement
            available_qty = on_hand + open_po
            net_requirement = max(0.0, gross_requirement - available_qty)
            
            # Determine inventory status
            if net_requirement == 0:
                status = "sufficient"
            elif on_hand >= gross_requirement:
                status = "on_hand_sufficient"
            elif available_qty >= gross_requirement:
                status = "with_po_sufficient"
            else:
                status = "shortage"
            
            net_requirements[material_id] = {
                'gross_requirement': gross_requirement,
                'on_hand_qty': on_hand,
                'open_po_qty': open_po,
                'available_qty': available_qty,
                'net_requirement': net_requirement,
                'unit': unit,
                'inventory_status': status,
                'sources': req_data.get('sources', [])
            }
        
        return net_requirements
    
    @classmethod
    def get_inventory_summary(cls, inventories: List[Inventory]) -> pd.DataFrame:
        """Generate inventory summary for analysis"""
        data = []
        for inv in inventories:
            total_available = inv.on_hand_qty + inv.open_po_qty
            data.append({
                'material_id': inv.material_id,
                'on_hand_qty': inv.on_hand_qty,
                'open_po_qty': inv.open_po_qty,
                'total_available': total_available,
                'unit': inv.unit,
                'po_expected_date': inv.po_expected_date
            })
        
        return pd.DataFrame(data)
    
    @classmethod
    def identify_critical_materials(cls, 
                                  net_requirements: Dict[str, Dict],
                                  threshold_days: int = 30) -> List[str]:
        """Identify materials with critical shortage"""
        critical_materials = []
        
        for material_id, req_data in net_requirements.items():
            if (req_data['net_requirement'] > 0 and 
                req_data['inventory_status'] == 'shortage'):
                critical_materials.append(material_id)
        
        return critical_materials