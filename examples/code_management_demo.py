"""
Example usage of BeverlyKnitsCodeManager

This script demonstrates how to use the code management client
for various textile manufacturing code management tasks.
"""

import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)
import json
from pathlib import Path

from src.core.code_management_client import BeverlyKnitsCodeManager


async def demonstrate_code_management():
    """Demonstrate various code management capabilities"""
    
    # Initialize the code manager
    manager = BeverlyKnitsCodeManager()
    
    try:
        logger.info("🚀 Initializing Beverly Knits Code Manager...")
        await manager.initialize()
        logger.info("✅ Code Manager initialized successfully\n")
        
        # Example 1: Analyze code quality
        logger.info("📊 Example 1: Analyzing Code Quality")
        logger.info("-" * 50)
        
        # Analyze the ML integration client
        ml_client_path = "src/core/ml_integration_client.py"
        if Path(ml_client_path).exists():
            logger.info(f"Analyzing: {ml_client_path}")
            quality_report = await manager.analyze_textile_code_quality(ml_client_path)
            logger.info(f"Quality Report: {json.dumps(quality_report, indent=2)}\n")
        else:
            logger.info(f"File not found: {ml_client_path}\n")
        
        # Example 2: Generate a material handler
        logger.info("🧵 Example 2: Generating Material Handler")
        logger.info("-" * 50)
        
        material_properties = [
            "fiber_content",
            "weight_per_yard",
            "width",
            "shrinkage_rate",
            "color_fastness",
            "tensile_strength"
        ]
        
        logger.info(f"Generating handler for: Polyester Blend")
        logger.info(f"Properties: {', '.join(material_properties)}")
        
        handler_path = await manager.generate_material_handler(
            "PolyesterBlend",
            material_properties
        )
        logger.info(f"✅ Generated handler at: {handler_path}\n")
        
        # Example 3: Generate supplier connector
        logger.info("🔌 Example 3: Generating Supplier Connector")
        logger.info("-" * 50)
        
        supplier_api_spec = {
            "base_url": "https://api.textilesupplier.com/v2",
            "auth_type": "api_key",
            "endpoints": {
                "inventory": "/inventory",
                "orders": "/orders",
                "pricing": "/pricing"
            },
            "rate_limit": "100/hour"
        }
        
        logger.info("Generating connector for: Global Textile Supplier")
        connector_path = await manager.generate_supplier_connector(
            "GlobalTextileSupplier",
            supplier_api_spec
        )
        logger.info(f"✅ Generated connector at: {connector_path}\n")
        
        # Example 4: Analyze code complexity
        logger.info("🔍 Example 4: Analyzing Code Complexity")
        logger.info("-" * 50)
        
        # Analyze a specific file
        target_file = "engine/planner.py"
        if Path(target_file).exists():
            logger.info(f"Analyzing complexity of: {target_file}")
            complexity_report = await manager.analyze_code_complexity(target_file)
            logger.info(f"Complexity Report: {json.dumps(complexity_report, indent=2)}\n")
        else:
            logger.info(f"File not found: {target_file}\n")
        
        # Example 5: Generate documentation
        logger.info("📚 Example 5: Generating Documentation")
        logger.info("-" * 50)
        
        doc_target = "src/core/data_processing_client.py"
        if Path(doc_target).exists():
            logger.info(f"Generating documentation for: {doc_target}")
            doc_path = await manager.generate_documentation(doc_target, "markdown")
            logger.info(f"✅ Generated documentation at: {doc_path}\n")
        else:
            logger.info(f"File not found: {doc_target}\n")
        
        # Example 6: Validate textile patterns
        logger.info("✔️ Example 6: Validating Textile Patterns")
        logger.info("-" * 50)
        
        validation_target = "engine/bom_explosion.py"
        if Path(validation_target).exists():
            logger.info(f"Validating patterns in: {validation_target}")
            validation_result = await manager.validate_textile_patterns(validation_target)
            logger.info(f"Validation Result: {json.dumps(validation_result, indent=2)}\n")
        else:
            logger.info(f"File not found: {validation_target}\n")
        
    except Exception as e:
        logger.info(f"❌ Error: {e}")
    
    finally:
        # Clean up
        logger.info("🧹 Cleaning up connections...")
        await manager.cleanup()
        logger.info("✅ Cleanup complete")


async def demonstrate_refactoring():
    """Demonstrate code refactoring capabilities"""
    
    manager = BeverlyKnitsCodeManager()
    
    try:
        await manager.initialize()
        
        logger.info("\n🔧 Code Refactoring Example")
        logger.info("=" * 50)
        
        # Create a sample algorithm file for demonstration
        sample_file = Path("temp/sample_algorithm.py")
        sample_file.parent.mkdir(exist_ok=True)
        
        sample_code = '''
def calculate_material_requirements(bom, forecast):
    """Calculate material requirements based on BOM and forecast"""
    requirements = {}
    
    # Inefficient nested loops
    for sku in forecast:
        for material in bom[sku]:
            if material not in requirements:
                requirements[material] = 0
            requirements[material] += forecast[sku] * bom[sku][material]
    
    return requirements
'''
        
        with open(sample_file, 'w') as f:
            f.write(sample_code)
        
        logger.info(f"Created sample file: {sample_file}")
        logger.info("Original code:")
        logger.info(sample_code)
        
        # Refactor for performance
        logger.info("\n🚀 Refactoring for performance...")
        result = await manager.refactor_planning_algorithm(
            str(sample_file),
            "performance"
        )
        
        logger.info(f"✅ Refactoring complete!")
        logger.info(f"Backup saved at: {result['backup_file']}")
        logger.info(f"Improvements: {', '.join(result['improvements'])}")
        logger.info(f"Performance gains: {json.dumps(result['performance_gain'], indent=2)}")
        
        # Show refactored code
        with open(sample_file, 'r') as f:
            logger.info("\nRefactored code:")
            logger.info(f.read())
        
    finally:
        await manager.cleanup()


async def main():
    """Main entry point"""
    logger.info("🧶 Beverly Knits Code Management Demo")
    logger.info("=" * 60)
    logger.info()
    
    # Run main demonstration
    await demonstrate_code_management()
    
    # Run refactoring demonstration
    await demonstrate_refactoring()


if __name__ == "__main__":
    asyncio.run(main())