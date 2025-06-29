"""
Supplier Data Model with EOQ Optimization and Multi-Supplier Sourcing
"""

import math
from dataclasses import dataclass
from typing import Dict, List, NamedTuple, Optional

import pandas as pd


@dataclass
class Supplier:
    """Represents supplier information for a material"""
    material_id: str
    supplier_id: str
    cost_per_unit: float
    lead_time_days: int
    moq: int  # Minimum Order Quantity
    contract_qty_limit: Optional[int] = None
    reliability_score: float = 1.0  # 0-1 scale
    # EOQ-related parameters
    ordering_cost: float = 100.0  # Cost per order (setup, admin, etc.)
    holding_cost_rate: float = 0.2  # Annual holding cost as % of unit cost
    
    def __post_init__(self):
        """Validate supplier data"""
        if self.cost_per_unit <= 0:
            raise ValueError("Cost per unit must be positive")
        if self.lead_time_days < 0:
            raise ValueError("Lead time cannot be negative")
        if self.reliability_score < 0 or self.reliability_score > 1:
            raise ValueError("Reliability score must be between 0 and 1")
        if self.ordering_cost < 0:
            raise ValueError("Ordering cost cannot be negative")
        if self.holding_cost_rate < 0:
            raise ValueError("Holding cost rate cannot be negative")


class EOQCalculator:
    """Economic Order Quantity Calculator"""
    
    @staticmethod
    def calculate_eoq(annual_demand: float, 
                      ordering_cost: float, 
                      unit_cost: float, 
                      holding_cost_rate: float) -> float:
        """
        Calculate Economic Order Quantity
        
        Args:
            annual_demand: Annual demand for the material
            ordering_cost: Cost per order (setup, admin, etc.)
            unit_cost: Cost per unit of material
            holding_cost_rate: Annual holding cost as % of unit cost
            
        Returns:
            Optimal order quantity
        """
        if annual_demand <= 0 or ordering_cost <= 0 or unit_cost <= 0 or holding_cost_rate <= 0:
            return 0
        
        holding_cost_per_unit = unit_cost * holding_cost_rate
        eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
        return eoq
    
    @staticmethod
    def calculate_total_cost(annual_demand: float,
                           order_quantity: float,
                           ordering_cost: float,
                           unit_cost: float,
                           holding_cost_rate: float) -> Dict[str, float]:
        """
        Calculate total cost components for given order quantity
        
        Returns:
            Dictionary with cost breakdown
        """
        if order_quantity <= 0:
            return {
                'ordering_cost': float('inf'),
                'holding_cost': float('inf'),
                'total_cost': float('inf')
            }
        
        # Annual ordering cost
        annual_ordering_cost = (annual_demand / order_quantity) * ordering_cost
        
        # Annual holding cost
        holding_cost_per_unit = unit_cost * holding_cost_rate
        annual_holding_cost = (order_quantity / 2) * holding_cost_per_unit
        
        # Total cost (excluding material cost which is constant)
        total_cost = annual_ordering_cost + annual_holding_cost
        
        return {
            'ordering_cost': annual_ordering_cost,
            'holding_cost': annual_holding_cost,
            'total_cost': total_cost
        }


class SupplierAllocation(NamedTuple):
    """Represents allocation of quantity to a supplier"""
    supplier: Supplier
    quantity: float
    cost: float
    reasoning: str
    eoq: Optional[float] = None
    percentage: float = 0.0


class MultiSupplierOptimizer:
    """Optimizes sourcing across multiple suppliers"""
    
    def __init__(self):
        self.eoq_calculator = EOQCalculator()
    
    def optimize_multi_supplier_sourcing(self,
                                       material_id: str,
                                       required_quantity: float,
                                       suppliers: List[Supplier],
                                       annual_demand: float = None,
                                       max_suppliers: int = 3,
                                       max_lead_time: int = None,
                                       cost_weight: float = 0.6,
                                       reliability_weight: float = 0.4) -> List[SupplierAllocation]:
        """
        Optimize sourcing across multiple suppliers
        
        Args:
            material_id: Material identifier
            required_quantity: Total quantity needed
            suppliers: List of available suppliers
            annual_demand: Annual demand for EOQ calculation
            max_suppliers: Maximum number of suppliers to use
            max_lead_time: Maximum acceptable lead time
            cost_weight: Weight for cost in optimization (0-1)
            reliability_weight: Weight for reliability in optimization (0-1)
            
        Returns:
            List of supplier allocations
        """
        # Filter suppliers for this material
        material_suppliers = [s for s in suppliers if s.material_id == material_id]
        
        if not material_suppliers:
            return []
        
        # Filter by lead time if specified
        if max_lead_time:
            material_suppliers = [s for s in material_suppliers if s.lead_time_days <= max_lead_time]
        
        if not material_suppliers:
            return []
        
        # Calculate supplier scores
        scored_suppliers = []
        for supplier in material_suppliers:
            # Calculate EOQ if annual demand is provided
            eoq = None
            if annual_demand:
                eoq = self.eoq_calculator.calculate_eoq(
                    annual_demand, 
                    supplier.ordering_cost,
                    supplier.cost_per_unit,
                    supplier.holding_cost_rate
                )
            
            # Calculate composite score
            cost_score = 1 / supplier.cost_per_unit if supplier.cost_per_unit > 0 else 0
            reliability_score = supplier.reliability_score
            composite_score = (cost_weight * cost_score) + (reliability_weight * reliability_score)
            
            scored_suppliers.append({
                'supplier': supplier,
                'score': composite_score,
                'eoq': eoq
            })
        
        # Sort by score (descending)
        scored_suppliers.sort(key=lambda x: x['score'], reverse=True)
        
        # Allocate quantities
        allocations = []
        remaining_quantity = required_quantity
        
        for i, supplier_info in enumerate(scored_suppliers[:max_suppliers]):
            if remaining_quantity <= 0:
                break
            
            supplier = supplier_info['supplier']
            eoq = supplier_info['eoq']
            
            # Determine allocation quantity
            if i == len(scored_suppliers[:max_suppliers]) - 1:
                # Last supplier gets remaining quantity
                allocation_qty = remaining_quantity
            else:
                # Allocate based on supplier capacity and EOQ
                max_allocation = min(
                    remaining_quantity,
                    supplier.contract_qty_limit or float('inf')
                )
                
                if eoq and eoq > supplier.moq:
                    # Use EOQ if it's above MOQ
                    allocation_qty = min(max_allocation, eoq)
                else:
                    # Use MOQ or proportional allocation
                    if remaining_quantity >= supplier.moq:
                        allocation_qty = max(supplier.moq, max_allocation * 0.4)
                    else:
                        allocation_qty = remaining_quantity
            
            # Ensure MOQ is met
            if allocation_qty < supplier.moq and remaining_quantity >= supplier.moq:
                allocation_qty = supplier.moq
            elif allocation_qty < supplier.moq:
                # Skip this supplier if we can't meet MOQ
                continue
            
            # Ensure we don't exceed contract limits
            if supplier.contract_qty_limit:
                allocation_qty = min(allocation_qty, supplier.contract_qty_limit)

            allocation_qty = min(allocation_qty, remaining_quantity)

            if allocation_qty > 0:
                cost = allocation_qty * supplier.cost_per_unit
                percentage = (allocation_qty / required_quantity) * 100
                reasoning = self._generate_allocation_reasoning(
                    supplier, allocation_qty, eoq, i == 0
                )

                allocations.append(SupplierAllocation(
                    supplier=supplier,
                    quantity=allocation_qty,
                    cost=cost,
                    reasoning=reasoning,
                    eoq=eoq,
                    percentage=percentage
                ))

                remaining_quantity -= allocation_qty
        
        return allocations
    
    def _generate_allocation_reasoning(self, supplier: Supplier, quantity: float, 
                                     eoq: Optional[float], is_primary: bool) -> str:
        """Generate reasoning for supplier allocation"""
        reasons = []
        
        if is_primary:
            reasons.append("Primary supplier")
        
        if eoq:
            if abs(quantity - eoq) / eoq < 0.1:
                reasons.append("Near-optimal EOQ")
            elif quantity > eoq * 1.2:
                reasons.append("Above EOQ for bulk savings")
            elif quantity < eoq * 0.8:
                reasons.append("Below EOQ due to constraints")
        
        if supplier.reliability_score >= 0.9:
            reasons.append("High reliability")
        elif supplier.reliability_score <= 0.7:
            reasons.append("Lower reliability, reduced allocation")
        
        if quantity == supplier.moq:
            reasons.append("MOQ requirement")
        
        if supplier.contract_qty_limit and quantity >= supplier.contract_qty_limit * 0.9:
            reasons.append("Near contract limit")
        
        return "; ".join(reasons) if reasons else "Standard allocation"


class SupplierSelector:
    """Enhanced supplier selection with EOQ optimization"""

    def __init__(self, config=None):
        self.config = config
        self.eoq_calculator = EOQCalculator()
        self.multi_optimizer = MultiSupplierOptimizer()
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> List[Supplier]:
        """Create supplier objects from DataFrame - optimized version"""
        suppliers = []

        required_columns = ['material_id', 'supplier_id', 'cost_per_unit',
                          'lead_time_days', 'moq']

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Validate data types and handle missing values upfront
        df = df.copy()
        df['material_id'] = df['material_id'].astype(str)
        df['supplier_id'] = df['supplier_id'].astype(str)
        df['cost_per_unit'] = pd.to_numeric(df['cost_per_unit'], errors='coerce')
        df['lead_time_days'] = pd.to_numeric(df['lead_time_days'], errors='coerce').fillna(0).astype(int)
        df['moq'] = pd.to_numeric(df['moq'], errors='coerce').fillna(1).astype(int)

        # Handle optional columns with defaults
        if 'contract_qty_limit' in df.columns:
            df['contract_qty_limit'] = pd.to_numeric(df['contract_qty_limit'], errors='coerce')
        else:
            df['contract_qty_limit'] = None

        df['reliability_score'] = pd.to_numeric(df.get('reliability_score', 1.0), errors='coerce').fillna(1.0)
        df['ordering_cost'] = pd.to_numeric(df.get('ordering_cost', 100.0), errors='coerce').fillna(100.0)
        df['holding_cost_rate'] = pd.to_numeric(df.get('holding_cost_rate', 0.2), errors='coerce').fillna(0.2)

        # Check for invalid data
        invalid_rows = df[df['cost_per_unit'].isna() | (df['cost_per_unit'] <= 0)]
        if not invalid_rows.empty:
            logger.warning(f"Found {len(invalid_rows)} rows with invalid cost_per_unit values")
            df = df[~df['cost_per_unit'].isna() & (df['cost_per_unit'] > 0)]

        # Use vectorized operations to create supplier objects
        supplier_data = df.to_dict('records')

        for row in supplier_data:
            try:
                supplier = Supplier(
                    material_id=row['material_id'],
                    supplier_id=row['supplier_id'],
                    cost_per_unit=float(row['cost_per_unit']),
                    lead_time_days=int(row['lead_time_days']),
                    moq=int(row['moq']),
                    contract_qty_limit=int(row['contract_qty_limit']) if pd.notna(row['contract_qty_limit']) else None,
                    reliability_score=float(row['reliability_score']),
                    ordering_cost=float(row['ordering_cost']),
                    holding_cost_rate=float(row['holding_cost_rate'])
                )
                suppliers.append(supplier)
            except Exception as e:
                logger.error(f"Error creating supplier from row: {e}")
                continue

        logger.info(f"Successfully created {len(suppliers)} suppliers from {len(df)} rows")
        return suppliers
    
    def select_optimal_supplier(self,
                              material_id: str,
                              suppliers: List[Supplier],
                              required_quantity: float = None,
                              annual_demand: float = None,
                              max_lead_time: int = None,
                              use_eoq: bool = True) -> Optional[Supplier]:
        """
        Select optimal supplier with optional EOQ consideration
        
        Args:
            material_id: Material identifier
            suppliers: List of available suppliers
            required_quantity: Quantity needed for this order
            annual_demand: Annual demand for EOQ calculation
            max_lead_time: Maximum acceptable lead time
            use_eoq: Whether to consider EOQ in selection
            
        Returns:
            Optimal supplier or None if no suitable supplier found
        """
        # Filter suppliers for this material
        material_suppliers = [s for s in suppliers if s.material_id == material_id]
        
        if not material_suppliers:
            return None
        
        # Filter by lead time if specified
        if max_lead_time:
            material_suppliers = [s for s in material_suppliers if s.lead_time_days <= max_lead_time]
        
        if not material_suppliers:
            return None
        
        # Filter by quantity constraints
        if required_quantity:
            material_suppliers = [s for s in material_suppliers 
                                if s.moq <= required_quantity and 
                                (not s.contract_qty_limit or s.contract_qty_limit >= required_quantity)]
        
        if not material_suppliers:
            return None
        
        # Score suppliers
        best_supplier = None
        best_score = -1
        
        for supplier in material_suppliers:
            score = 0
            
            # Base score from cost and reliability
            cost_score = 1 / supplier.cost_per_unit if supplier.cost_per_unit > 0 else 0
            reliability_score = supplier.reliability_score
            base_score = (0.6 * cost_score) + (0.4 * reliability_score)
            
            # EOQ consideration
            if use_eoq and annual_demand:
                eoq = self.eoq_calculator.calculate_eoq(
                    annual_demand,
                    supplier.ordering_cost,
                    supplier.cost_per_unit,
                    supplier.holding_cost_rate
                )
                
                if required_quantity and eoq > 0:
                    # Bonus for being close to EOQ
                    eoq_ratio = min(required_quantity, eoq) / max(required_quantity, eoq)
                    eoq_bonus = eoq_ratio * 0.2  # Up to 20% bonus
                    score = base_score + eoq_bonus
                else:
                    score = base_score
            else:
                score = base_score
            
            # Lead time penalty
            lead_time_penalty = supplier.lead_time_days * 0.01
            score -= lead_time_penalty
            
            if score > best_score:
                best_score = score
                best_supplier = supplier
        
        return best_supplier
    
    def calculate_order_quantity(self,
                               supplier: Supplier,
                               required_quantity: float,
                               annual_demand: float = None,
                               safety_stock_days: int = 7) -> Dict[str, float]:
        """
        Calculate optimal order quantity considering EOQ, MOQ, and safety stock
        
        Returns:
            Dictionary with order details
        """
        result = {
            'required_quantity': required_quantity,
            'moq': supplier.moq,
            'safety_stock': 0,
            'recommended_quantity': required_quantity,
            'eoq': None,
            'total_cost_analysis': None
        }
        
        # Calculate safety stock
        if annual_demand:
            daily_demand = annual_demand / 365
            safety_stock = daily_demand * safety_stock_days
            result['safety_stock'] = safety_stock
        
        # Calculate EOQ if annual demand is available
        if annual_demand:
            eoq = self.eoq_calculator.calculate_eoq(
                annual_demand,
                supplier.ordering_cost,
                supplier.cost_per_unit,
                supplier.holding_cost_rate
            )
            result['eoq'] = eoq
            
            # Determine recommended quantity
            base_quantity = required_quantity + result['safety_stock']
            
            # Consider EOQ, MOQ, and contract limits
            recommended_qty = max(base_quantity, supplier.moq)
            
            if eoq > supplier.moq and eoq > base_quantity:
                # Use EOQ if it's beneficial
                recommended_qty = eoq
            
            # Respect contract limits
            if supplier.contract_qty_limit:
                recommended_qty = min(recommended_qty, supplier.contract_qty_limit)
            
            result['recommended_quantity'] = recommended_qty
            
            # Calculate cost analysis
            result['total_cost_analysis'] = self.eoq_calculator.calculate_total_cost(
                annual_demand,
                recommended_qty,
                supplier.ordering_cost,
                supplier.cost_per_unit,
                supplier.holding_cost_rate
            )
        else:
            # Without annual demand, just ensure MOQ is met
            result['recommended_quantity'] = max(required_quantity, supplier.moq)
        
        return result