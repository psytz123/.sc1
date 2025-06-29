"""
ML Improvement Automation Example

This example demonstrates how the zen-mcp automation system
continuously improves ML capabilities.
"""

import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np

# Import our automation system
from automation.zen_code_automation import ZenCodeAutomation


class MLImprovementAutomation(ZenCodeAutomation):
    """
    Extended automation specifically for ML improvements
    """
    
    def __init__(self):
        super().__init__()
        self.ml_metrics_file = Path("logs/ml_metrics.json")
        self.ml_models_dir = Path("models/ml_models")
        self.ml_models_dir.mkdir(parents=True, exist_ok=True)
    
    async def analyze_ml_performance(self) -> Dict[str, Any]:
        """Analyze current ML model performance"""
        logger.info("🔍 Analyzing ML model performance...")
        
        # Use zen-mcp to analyze ML code
        ml_files = list(Path(".").rglob("*ml*.py"))
        
        analysis_results = {
            "models_found": 0,
            "performance_issues": [],
            "optimization_opportunities": [],
            "documentation_gaps": []
        }
        
        for ml_file in ml_files[:5]:  # Limit to 5 files for demo
            # Analyze with zen-mcp
            result = await self._call_zen_tool("analyze", {
                "code": ml_file.read_text(),
                "focus": "machine learning optimization and best practices"
            })
            
            if result.get("status") != "error":
                analysis_results["models_found"] += 1
                
                # Extract insights
                if "issues" in result:
                    analysis_results["performance_issues"].extend(result["issues"])
                
                if "optimizations" in result:
                    analysis_results["optimization_opportunities"].extend(result["optimizations"])
        
        return analysis_results
    
    async def improve_ml_pipeline(self, pipeline_file: str) -> Dict[str, Any]:
        """Improve ML pipeline code"""
        logger.info(f"🔧 Improving ML pipeline: {pipeline_file}")
        
        # Read current pipeline
        with open(pipeline_file, 'r') as f:
            current_code = f.read()
        
        # Use zen-mcp to improve the pipeline
        improvements = []
        
        # 1. Optimize data preprocessing
        result = await self._call_zen_tool("refactor", {
            "code": current_code,
            "focus": "optimize data preprocessing for better performance",
            "filename": pipeline_file
        })
        
        if result.get("status") != "error" and "refactored_code" in result:
            improvements.append({
                "type": "preprocessing_optimization",
                "description": "Optimized data preprocessing pipeline",
                "code": result["refactored_code"]
            })
        
        # 2. Add error handling
        result = await self._call_zen_tool("debug", {
            "code": current_code,
            "error_description": "Add comprehensive error handling for ML pipeline",
            "filename": pipeline_file
        })
        
        if result.get("status") != "error" and "fixed_code" in result:
            improvements.append({
                "type": "error_handling",
                "description": "Added robust error handling",
                "code": result["fixed_code"]
            })
        
        # 3. Generate documentation
        result = await self._call_zen_tool("docgen", {
            "code": current_code,
            "style": "comprehensive",
            "filename": pipeline_file
        })
        
        if result.get("status") != "error" and "documented_code" in result:
            improvements.append({
                "type": "documentation",
                "description": "Generated comprehensive documentation",
                "code": result["documented_code"]
            })
        
        return {
            "file": pipeline_file,
            "improvements": improvements,
            "timestamp": datetime.now().isoformat()
        }
    
    async def generate_ml_tests(self, model_file: str) -> Dict[str, Any]:
        """Generate tests for ML models"""
        logger.info(f"🧪 Generating tests for: {model_file}")
        
        with open(model_file, 'r') as f:
            model_code = f.read()
        
        # Use zen-mcp to generate tests
        result = await self._call_zen_tool("testgen", {
            "code": model_code,
            "test_framework": "pytest",
            "focus": "machine learning model validation"
        })
        
        if result.get("status") != "error" and "tests" in result:
            # Save generated tests
            test_file = Path("tests") / f"test_{Path(model_file).stem}.py"
            test_file.parent.mkdir(exist_ok=True)
            
            with open(test_file, 'w') as f:
                f.write(result["tests"])
            
            return {
                "status": "success",
                "test_file": str(test_file),
                "test_count": result.get("test_count", 0)
            }
        
        return {"status": "error", "message": "Failed to generate tests"}
    
    async def optimize_model_architecture(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to suggest model architecture improvements"""
        logger.info("🏗️ Optimizing model architecture...")
        
        # Use zen-mcp consensus for architecture recommendations
        result = await self._call_zen_tool("consensus", {
            "question": f"Given this model configuration: {json.dumps(model_config, indent=2)}, "
                       f"what architectural improvements would enhance performance? "
                       f"Consider: layer optimization, regularization, activation functions, "
                       f"and modern best practices. Provide specific recommendations.",
            "require_agreement": True
        })
        
        if result.get("status") != "error":
            return {
                "status": "success",
                "recommendations": result.get("consensus_response", ""),
                "confidence": result.get("agreement_score", 0)
            }
        
        return {"status": "error", "message": "Failed to get architecture recommendations"}
    
    async def create_ml_improvement_plan(self) -> Dict[str, Any]:
        """Create a comprehensive ML improvement plan"""
        logger.info("📋 Creating ML improvement plan...")
        
        # Use zen-mcp planner
        result = await self._call_zen_tool("planner", {
            "goal": "Create a comprehensive plan to improve ML model performance, "
                   "code quality, and maintainability in the Beverly Knits project",
            "context": "The project uses demand forecasting, risk assessment, "
                      "inventory optimization, and price prediction models",
            "constraints": [
                "Maintain backward compatibility",
                "Improve model accuracy by at least 5%",
                "Reduce inference time",
                "Add comprehensive testing"
            ]
        })
        
        if result.get("status") != "error" and "plan" in result:
            # Save the plan
            plan_file = Path("reports") / f"ml_improvement_plan_{datetime.now().strftime('%Y%m%d')}.json"
            plan_file.parent.mkdir(exist_ok=True)
            
            with open(plan_file, 'w') as f:
                json.dump(result["plan"], f, indent=2)
            
            return {
                "status": "success",
                "plan_file": str(plan_file),
                "steps": len(result["plan"].get("steps", []))
            }
        
        return {"status": "error", "message": "Failed to create improvement plan"}
    
    def track_ml_metrics(self, metrics: Dict[str, Any]):
        """Track ML performance metrics over time"""
        # Load existing metrics
        if self.ml_metrics_file.exists():
            with open(self.ml_metrics_file, 'r') as f:
                all_metrics = json.load(f)
        else:
            all_metrics = {"history": []}
        
        # Add new metrics
        metrics["timestamp"] = datetime.now().isoformat()
        all_metrics["history"].append(metrics)
        
        # Keep only last 100 entries
        all_metrics["history"] = all_metrics["history"][-100:]
        
        # Calculate trends
        if len(all_metrics["history"]) > 1:
            recent = all_metrics["history"][-10:]
            old = all_metrics["history"][-20:-10] if len(all_metrics["history"]) > 20 else all_metrics["history"][:10]
            
            # Simple trend analysis
            recent_avg_accuracy = np.mean([m.get("accuracy", 0) for m in recent])
            old_avg_accuracy = np.mean([m.get("accuracy", 0) for m in old])
            
            all_metrics["trends"] = {
                "accuracy_trend": "improving" if recent_avg_accuracy > old_avg_accuracy else "declining",
                "accuracy_change": recent_avg_accuracy - old_avg_accuracy
            }
        
        # Save metrics
        with open(self.ml_metrics_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        
        return all_metrics.get("trends", {})


async def demonstrate_ml_improvements():
    """Demonstrate ML improvement automation"""
    logger.info("🚀 Demonstrating ML Improvement Automation")
    logger.info("=" * 50)
    
    automation = MLImprovementAutomation()
    
    try:
        # 1. Analyze current ML performance
        logger.info("\n1️⃣ Analyzing ML Performance...")
        analysis = await automation.analyze_ml_performance()
        logger.info(f"   Found {analysis['models_found']} ML models")
        logger.info(f"   Performance issues: {len(analysis['performance_issues'])}")
        logger.info(f"   Optimization opportunities: {len(analysis['optimization_opportunities'])}")
        
        # 2. Create improvement plan
        logger.info("\n2️⃣ Creating Improvement Plan...")
        plan = await automation.create_ml_improvement_plan()
        if plan["status"] == "success":
            logger.info(f"   ✅ Created plan with {plan['steps']} steps")
            logger.info(f"   📄 Saved to: {plan['plan_file']}")
        
        # 3. Optimize model architecture
        logger.info("\n3️⃣ Getting Architecture Recommendations...")
        sample_config = {
            "model_type": "neural_network",
            "layers": [
                {"type": "dense", "units": 128},
                {"type": "dense", "units": 64},
                {"type": "dense", "units": 1}
            ],
            "optimizer": "adam",
            "loss": "mse"
        }
        
        arch_result = await automation.optimize_model_architecture(sample_config)
        if arch_result["status"] == "success":
            logger.info(f"   ✅ Got recommendations (confidence: {arch_result['confidence']:.2f})")
            logger.info(f"   📝 {arch_result['recommendations'][:200]}...")
        
        # 4. Track metrics
        logger.info("\n4️⃣ Tracking ML Metrics...")
        sample_metrics = {
            "model": "demand_forecast",
            "accuracy": 0.92,
            "precision": 0.89,
            "recall": 0.91,
            "f1_score": 0.90,
            "inference_time_ms": 45
        }
        
        trends = automation.track_ml_metrics(sample_metrics)
        if trends:
            logger.info(f"   📈 Accuracy trend: {trends.get('accuracy_trend', 'unknown')}")
        
        # 5. Generate example improvement
        logger.info("\n5️⃣ Example: Improving ML Pipeline...")
        
        # Create a sample ML file for demonstration
        sample_ml_file = Path("temp/sample_ml_pipeline.py")
        sample_ml_file.parent.mkdir(exist_ok=True)
        
        sample_code = '''
def train_model(data):
    # Simple model training
    X = data.drop('target', axis=1)
    y = data['target']
    
    model = RandomForestRegressor()
    model.fit(X, y)
    
    return model

def predict(model, features):
    predictions = model.predict(features)
    return predictions
'''
        
        with open(sample_ml_file, 'w') as f:
            f.write(sample_code)
        
        improvements = await automation.improve_ml_pipeline(str(sample_ml_file))
        logger.info(f"   ✅ Generated {len(improvements['improvements'])} improvements")
        
        for imp in improvements['improvements']:
            logger.info(f"      - {imp['type']}: {imp['description']}")
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ ML Improvement Automation Demo Complete!")
        logger.info("\nThe automation system can:")
        logger.info("  • Continuously monitor ML model performance")
        logger.info("  • Automatically improve code quality")
        logger.info("  • Generate tests for ML components")
        logger.info("  • Optimize model architectures")
        logger.info("  • Track metrics and identify trends")
        logger.info("  • Create comprehensive improvement plans")
        
    finally:
        await automation.close()


if __name__ == "__main__":
    asyncio.run(demonstrate_ml_improvements())