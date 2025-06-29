"""
Example usage of BeverlyKnitsCodeManager

This script demonstrates how to use the code management client
for various textile manufacturing code management tasks.
"""

import asyncio
import json
from pathlib import Path
from src.core.code_management_client import BeverlyKnitsCodeManager


async def demonstrate_code_management():
    """Demonstrate various code management capabilities"""
    
    # Initialize the code manager
    manager = BeverlyKnitsCodeManager()
    
    try:
        print("🚀 Initializing Beverly Knits Code Manager...")
        await manager.initialize()
        print("✅ Code Manager initialized successfully\n")
        
        # Example 1: Analyze code quality
        print("📊 Example 1: Analyzing Code Quality")
        print("-" * 50)
        
        # Analyze the ML integration client
        ml_client_path = "src/core/ml_integration_client.py"
        if Path(ml_client_path).exists():
            print(f"Analyzing: {ml_client_path}")
            quality_report = await manager.analyze_textile_code_quality(ml_client_path)
            print(f"Quality Report: {json.dumps(quality_report, indent=2)}\n")
        else:
            print(f"File not found: {ml_client_path}\n")
        
        # Example 2: Generate a material handler
        print("🧵 Example 2: Generating Material Handler")
        print("-" * 50)
        
        material_properties = [
            "fiber_content",
            "weight_per_yard",
            "width",
            "shrinkage_rate",
            "color_fastness",
            "tensile_strength"
        ]
        
        print(f"Generating handler for: Polyester Blend")
        print(f"Properties: {', '.join(material_properties)}")
        
        handler_path = await manager.generate_material_handler(
            "PolyesterBlend",
            material_properties
        )
        print(f"✅ Generated handler at: {handler_path}\n")
        
        # Example 3: Generate supplier connector
        print("🔌 Example 3: Generating Supplier Connector")
        print("-" * 50)
        
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
        
        print("Generating connector for: Global Textile Supplier")
        connector_path = await manager.generate_supplier_connector(
            "GlobalTextileSupplier",
            supplier_api_spec
        )
        print(f"✅ Generated connector at: {connector_path}\n")
        
        # Example 4: Analyze code complexity
        print("🔍 Example 4: Analyzing Code Complexity")
        print("-" * 50)
        
        # Analyze a specific file
        target_file = "engine/planner.py"
        if Path(target_file).exists():
            print(f"Analyzing complexity of: {target_file}")
            complexity_report = await manager.analyze_code_complexity(target_file)
            print(f"Complexity Report: {json.dumps(complexity_report, indent=2)}\n")
        else:
            print(f"File not found: {target_file}\n")
        
        # Example 5: Generate documentation
        print("📚 Example 5: Generating Documentation")
        print("-" * 50)
        
        doc_target = "src/core/data_processing_client.py"
        if Path(doc_target).exists():
            print(f"Generating documentation for: {doc_target}")
            doc_path = await manager.generate_documentation(doc_target, "markdown")
            print(f"✅ Generated documentation at: {doc_path}\n")
        else:
            print(f"File not found: {doc_target}\n")
        
        # Example 6: Validate textile patterns
        print("✔️ Example 6: Validating Textile Patterns")
        print("-" * 50)
        
        validation_target = "engine/bom_explosion.py"
        if Path(validation_target).exists():
            print(f"Validating patterns in: {validation_target}")
            validation_result = await manager.validate_textile_patterns(validation_target)
            print(f"Validation Result: {json.dumps(validation_result, indent=2)}\n")
        else:
            print(f"File not found: {validation_target}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up
        print("🧹 Cleaning up connections...")
        await manager.cleanup()
        print("✅ Cleanup complete")


async def demonstrate_refactoring():
    """Demonstrate code refactoring capabilities"""
    
    manager = BeverlyKnitsCodeManager()
    
    try:
        await manager.initialize()
        
        print("\n🔧 Code Refactoring Example")
        print("=" * 50)
        
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
        
        print(f"Created sample file: {sample_file}")
        print("Original code:")
        print(sample_code)
        
        # Refactor for performance
        print("\n🚀 Refactoring for performance...")
        result = await manager.refactor_planning_algorithm(
            str(sample_file),
            "performance"
        )
        
        print(f"✅ Refactoring complete!")
        print(f"Backup saved at: {result['backup_file']}")
        print(f"Improvements: {', '.join(result['improvements'])}")
        print(f"Performance gains: {json.dumps(result['performance_gain'], indent=2)}")
        
        # Show refactored code
        with open(sample_file, 'r') as f:
            print("\nRefactored code:")
            print(f.read())
        
    finally:
        await manager.cleanup()


async def main():
    """Main entry point"""
    print("🧶 Beverly Knits Code Management Demo")
    print("=" * 60)
    print()
    
    # Run main demonstration
    await demonstrate_code_management()
    
    # Run refactoring demonstration
    await demonstrate_refactoring()


if __name__ == "__main__":
    asyncio.run(main())