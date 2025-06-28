from engine.planner import RawMaterialPlanner
from core.code_management_client import BeverlyKnitsCodeManager
import logging
from typing import Dict, Any, List

class CodeEnhancedPlanner(RawMaterialPlanner):
    """Enhanced planner with code management capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.code_manager = BeverlyKnitsCodeManager()
        self.logger = logging.getLogger(__name__)
        
    async def initialize_code_capabilities(self):
        """Initialize code management features"""
        await self.code_manager.initialize()
        self.logger.info("Code management capabilities ready")
    
    async def analyze_planning_code_quality(self) -> Dict[str, Any]:
        """Analyze the quality of planning algorithm code"""
        modules_to_analyze = [
            "engine/planner.py",
            "models/procurement_recommendation.py", 
            "models/finished_goods_forecast.py",
            "utils/calculations.py"
        ]
        
        analysis_results = {}
        
        for module in modules_to_analyze:
            try:
                result = await self.code_manager.analyze_textile_code_quality(module)
                analysis_results[module] = result
            except Exception as e:
                self.logger.error(f"Failed to analyze {module}: {e}")
                analysis_results[module] = {"error": str(e)}
        
        return analysis_results
    
    async def generate_new_material_support(self, material_type: str, properties: List[str]) -> str:
        """Generate code to support new material types"""
        return await self.code_manager.generate_material_handler(material_type, properties)
    
    async def optimize_planning_performance(self) -> Dict[str, Any]:
        """Optimize planning algorithm performance through refactoring"""
        optimization_results = {}
        
        # Optimize core planning algorithm
        try:
            result = await self.code_manager.refactor_planning_algorithm(
                "engine/planner.py", 
                "performance_optimization"
            )
            optimization_results["planner"] = result
        except Exception as e:
            self.logger.error(f"Failed to optimize planner: {e}")
            
        return optimization_results