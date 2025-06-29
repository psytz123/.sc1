"""
Procurement Recommendation Data Model
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import pandas as pd


class RiskFlag(Enum):
    """Risk levels for procurement recommendations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ProcurementRecommendation:
    """Represents a procurement recommendation for a material"""
    material_id: str
    order_quantity: float
    supplier_id: str
    cost_per_unit: float
    total_cost: float
    lead_time_days: int
    risk: RiskFlag
    reasoning: str
    
    # Additional analysis fields
    gross_requirement: float = 0.0
    net_requirement: float = 0.0
    safety_buffer: float = 0.0
    moq_adjustment: float = 0.0
    
    # EOQ-related fields
    eoq_quantity: Optional[float] = None
    cost_analysis: Optional[Dict[str, float]] = None
    
    # Legacy field mappings for compatibility
    @property
    def recommended_order_qty(self) -> float:
        """Legacy field mapping"""
        return self.order_quantity
    
    @property
    def unit(self) -> str:
        """Legacy field mapping - default unit"""
        return "units"
    
    @property
    def expected_lead_time(self) -> int:
        """Legacy field mapping"""
        return self.lead_time_days
    
    @property
    def risk_flag(self) -> RiskFlag:
        """Legacy field mapping"""
        return self.risk
    
    @property
    def safety_buffer_applied(self) -> float:
        """Legacy field mapping"""
        return self.safety_buffer
    
    def to_dict(self) -> Dict:
        """Convert recommendation to dictionary for JSON serialization"""
        result = {
            'material_id': self.material_id,
            'order_quantity': self.order_quantity,
            'recommended_order_qty': self.order_quantity,  # Legacy compatibility
            'supplier_id': self.supplier_id,
            'unit': self.unit,
            'cost_per_unit': self.cost_per_unit,
            'total_cost': self.total_cost,
            'lead_time_days': self.lead_time_days,
            'expected_lead_time': self.lead_time_days,  # Legacy compatibility
            'risk': self.risk.value,
            'risk_flag': self.risk.value,  # Legacy compatibility
            'reasoning': self.reasoning,
            'gross_requirement': self.gross_requirement,
            'net_requirement': self.net_requirement,
            'safety_buffer': self.safety_buffer,
            'safety_buffer_applied': self.safety_buffer,  # Legacy compatibility
            'moq_adjustment': self.moq_adjustment,
        }
        
        # Add EOQ fields if available
        if self.eoq_quantity is not None:
            result['eoq_quantity'] = self.eoq_quantity
        
        if self.cost_analysis:
            result['cost_analysis'] = self.cost_analysis
        
        return result


class RecommendationGenerator:
    """Generates procurement recommendations based on net requirements and suppliers"""
    
    @staticmethod
    def generate_recommendations(net_requirements: Dict[str, Dict],
                               suppliers: List,
                               config: Dict) -> List[ProcurementRecommendation]:
        """
        Generate procurement recommendations
        
        Note: This method is kept for backward compatibility.
        The main logic is now in RawMaterialPlanner._generate_enhanced_recommendations()
        """
        from models.supplier import SupplierSelector
        
        recommendations = []
        supplier_selector = SupplierSelector()
        
        for material_id, req_data in net_requirements.items():
            net_requirement = req_data['net_requirement']
            
            if net_requirement <= 0:
                continue
            
            # Get suppliers for this material
            material_suppliers = [s for s in suppliers if s.material_id == material_id]
            
            if not material_suppliers:
                # Create recommendation for material without suppliers
                recommendations.append(ProcurementRecommendation(
                    material_id=material_id,
                    order_quantity=net_requirement,
                    supplier_id="NO_SUPPLIER",
                    cost_per_unit=0.0,
                    total_cost=0.0,
                    lead_time_days=999,
                    risk=RiskFlag.HIGH,
                    reasoning="No supplier available for this material",
                    gross_requirement=req_data['total_requirement'],
                    net_requirement=net_requirement,
                    safety_buffer=0,
                    moq_adjustment=0
                ))
                continue
            
            # Select optimal supplier (basic selection without EOQ)
            optimal_supplier = supplier_selector.select_optimal_supplier(
                material_id=material_id,
                suppliers=material_suppliers,
                required_quantity=net_requirement,
                max_lead_time=config.get('max_lead_time'),
                use_eoq=False
            )
            
            if optimal_supplier:
                # Apply safety buffer
                safety_buffer = net_requirement * config.get('safety_buffer', 0.1)
                order_qty = net_requirement + safety_buffer
                
                # Ensure MOQ is met
                if order_qty < optimal_supplier.moq:
                    moq_adjustment = optimal_supplier.moq - order_qty
                    order_qty = optimal_supplier.moq
                else:
                    moq_adjustment = 0
                
                # Assess risk
                if optimal_supplier.reliability_score < config.get('high_risk_threshold', 0.7):
                    risk = RiskFlag.HIGH
                elif optimal_supplier.reliability_score < config.get('medium_risk_threshold', 0.85):
                    risk = RiskFlag.MEDIUM
                else:
                    risk = RiskFlag.LOW
                
                # Generate reasoning
                reasoning_parts = []
                if moq_adjustment > 0:
                    reasoning_parts.append("MOQ adjustment applied")
                if safety_buffer > 0:
                    reasoning_parts.append(f"Safety buffer: {safety_buffer:.1f}")
                if optimal_supplier.reliability_score >= 0.9:
                    reasoning_parts.append("High reliability supplier")
                
                reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Standard procurement"
                
                recommendations.append(ProcurementRecommendation(
                    material_id=material_id,
                    order_quantity=order_qty,
                    supplier_id=optimal_supplier.supplier_id,
                    cost_per_unit=optimal_supplier.cost_per_unit,
                    total_cost=order_qty * optimal_supplier.cost_per_unit,
                    lead_time_days=optimal_supplier.lead_time_days,
                    risk=risk,
                    reasoning=reasoning,
                    gross_requirement=req_data['total_requirement'],
                    net_requirement=net_requirement,
                    safety_buffer=safety_buffer,
                    moq_adjustment=moq_adjustment
                ))
        
        return recommendations
    
    @staticmethod
    def to_dataframe(recommendations: List[ProcurementRecommendation]) -> pd.DataFrame:
        """Convert recommendations to DataFrame"""
        if not recommendations:
            return pd.DataFrame()
        
        data = [rec.to_dict() for rec in recommendations]
        return pd.DataFrame(data)
    
    @staticmethod
    def get_summary_stats(recommendations: List[ProcurementRecommendation]) -> Dict:
        """Generate summary statistics for recommendations"""
        if not recommendations:
            return {}
        
        total_cost = sum(rec.total_cost for rec in recommendations)
        avg_lead_time = sum(rec.lead_time_days for rec in recommendations) / len(recommendations)
        
        # Risk distribution
        risk_counts = {}
        for rec in recommendations:
            risk_level = rec.risk.value
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        # Materials without suppliers
        materials_without_suppliers = sum(1 for rec in recommendations if rec.supplier_id == "NO_SUPPLIER")
        
        # EOQ statistics
        eoq_optimized = sum(1 for rec in recommendations if rec.eoq_quantity is not None)
        
        return {
            'total_recommendations': len(recommendations),
            'total_estimated_cost': total_cost,
            'avg_lead_time': avg_lead_time,
            'risk_distribution': risk_counts,
            'materials_without_suppliers': materials_without_suppliers,
            'eoq_optimized_count': eoq_optimized,
            'unique_suppliers': len(set(rec.supplier_id for rec in recommendations if rec.supplier_id != "NO_SUPPLIER")),
            'avg_order_quantity': sum(rec.order_quantity for rec in recommendations) / len(recommendations)
        }