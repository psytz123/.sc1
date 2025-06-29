# Beverly Knits Code Management Client

## Overview

The `BeverlyKnitsCodeManager` is a sophisticated code management client designed specifically for the Beverly Knits Raw Material Planner project. It provides automated code analysis, generation, refactoring, and documentation capabilities tailored for textile manufacturing systems.

## Features

### 🔍 Code Analysis
- **Textile-Specific Code Quality Analysis**: Analyzes code with focus on BOM processing, inventory calculations, and supplier integrations
- **Complexity Metrics**: Measures cyclomatic, cognitive, and Halstead complexity
- **Pattern Validation**: Validates code against textile industry best practices

### 🛠️ Code Generation
- **Material Handlers**: Generates code for handling new yarn/fabric types
- **Supplier Connectors**: Creates API integration modules for new suppliers
- **Documentation**: Auto-generates comprehensive documentation

### 🔧 Code Refactoring
- **Performance Optimization**: Refactors algorithms for better performance
- **Modular Architecture**: Breaks down monolithic functions
- **Error Handling Enhancement**: Improves error handling patterns

### 🔄 Connection Management
- **Connection Pooling**: Efficient management of zen-mcp-server connections
- **Automatic Retry Logic**: Handles transient failures gracefully
- **Resource Cleanup**: Proper cleanup of all connections

## Installation

1. Ensure you have Python 3.8+ installed
2. Install zen-mcp-server (follow zen-mcp-server documentation)
3. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The client uses a JSON configuration file located at `config/zen_code_config.json`:

```json
{
  "code_management": {
    "analysis": {
      "languages": ["python"],
      "quality_thresholds": {
        "complexity": 10,
        "maintainability": 0.7
      }
    },
    "generation": {
      "templates_path": "templates/",
      "output_path": "generated/"
    }
  }
}
```

### Configuration Parameters

- **languages**: List of programming languages to analyze (currently supports Python)
- **quality_thresholds**:
  - **complexity**: Maximum acceptable cyclomatic complexity (default: 10)
  - **maintainability**: Minimum maintainability index (0-1, default: 0.7)
- **templates_path**: Directory containing code generation templates
- **output_path**: Directory for generated code output

## Usage

### Basic Usage

```python
import asyncio
from src.core.code_management_client import BeverlyKnitsCodeManager

async def main():
    # Initialize the manager
    manager = BeverlyKnitsCodeManager()
    
    try:
        # Initialize connections
        await manager.initialize()
        
        # Analyze code quality
        quality_report = await manager.analyze_textile_code_quality("src/module.py")
        print(f"Quality Report: {quality_report}")
        
    finally:
        # Always cleanup connections
        await manager.cleanup()

asyncio.run(main())
```

### Analyzing Code Quality

```python
# Analyze textile-specific code quality
quality_report = await manager.analyze_textile_code_quality("engine/bom_explosion.py")

# Analyze code complexity
complexity_report = await manager.analyze_code_complexity("src/planner.py")

# Validate against textile patterns
validation_result = await manager.validate_textile_patterns("src/inventory.py")
```

### Generating Code

```python
# Generate material handler
material_path = await manager.generate_material_handler(
    "CottonBlend",
    ["weight", "thread_count", "shrinkage_rate", "color_fastness"]
)

# Generate supplier connector
api_spec = {
    "base_url": "https://api.supplier.com",
    "auth_type": "bearer",
    "endpoints": {
        "inventory": "/inventory",
        "orders": "/orders"
    }
}
connector_path = await manager.generate_supplier_connector("SupplierA", api_spec)
```

### Refactoring Code

```python
# Refactor for performance
result = await manager.refactor_planning_algorithm(
    "engine/planning_algorithm.py",
    "performance"
)

print(f"Backup saved at: {result['backup_file']}")
print(f"Improvements: {result['improvements']}")
```

### Generating Documentation

```python
# Generate markdown documentation
doc_path = await manager.generate_documentation(
    "src/core/ml_integration_client.py",
    "markdown"
)
```

## API Reference

### Class: BeverlyKnitsCodeManager

#### Constructor

```python
BeverlyKnitsCodeManager(project_root: str = ".", config_path: str = None)
```

- **project_root**: Root directory of the project (default: current directory)
- **config_path**: Path to configuration file (default: `{project_root}/config/zen_code_config.json`)

#### Methods

##### async initialize()
Initialize zen-mcp-server connections and connection pool.

##### async analyze_textile_code_quality(module_path: str) -> Dict[str, Any]
Analyze code quality with textile manufacturing context.

##### async generate_material_handler(material_type: str, properties: List[str]) -> str
Generate code for handling new material types.

##### async refactor_planning_algorithm(algorithm_file: str, optimization_type: str) -> Dict[str, Any]
Refactor algorithms for better performance.

##### async generate_supplier_connector(supplier_name: str, api_spec: Dict) -> str
Generate supplier API connector code.

##### async analyze_code_complexity(file_path: str) -> Dict[str, Any]
Analyze code complexity metrics.

##### async generate_documentation(module_path: str, doc_format: str = "markdown") -> str
Generate documentation for a module.

##### async validate_textile_patterns(code_path: str) -> Dict[str, Any]
Validate code against textile industry patterns.

##### async optimize_data_processing(pipeline_file: str) -> Dict[str, Any]
Optimize data processing pipelines.

##### async cleanup()
Clean up all connections in the pool.

## Error Handling

The client implements comprehensive error handling:

- **Configuration Errors**: Validates configuration on initialization
- **Connection Errors**: Automatic retry with exponential backoff
- **Tool Call Errors**: Detailed error messages with context
- **Timeout Handling**: 30-second timeout for tool calls

## Best Practices

1. **Always use context managers or try/finally blocks** to ensure cleanup:
   ```python
   manager = BeverlyKnitsCodeManager()
   try:
       await manager.initialize()
       # Your code here
   finally:
       await manager.cleanup()
   ```

2. **Handle errors appropriately**:
   ```python
   try:
       result = await manager.analyze_textile_code_quality("module.py")
   except Exception as e:
       logger.error(f"Analysis failed: {e}")
   ```

3. **Use appropriate optimization types** for refactoring:
   - `"performance"`: Focus on speed optimization
   - `"memory"`: Focus on memory efficiency
   - `"readability"`: Focus on code clarity

4. **Validate generated code** before using in production

## Testing

Run the unit tests:

```bash
pytest tests/test_code_management_client.py -v
```

Run the example demonstration:

```bash
python examples/code_management_demo.py
```

## Troubleshooting

### Common Issues

1. **zen-mcp-server not found**
   - Ensure zen-mcp-server is installed and in PATH
   - Check installation with: `zen-mcp-server --version`

2. **Configuration errors**
   - Verify config file exists at expected location
   - Check JSON syntax is valid
   - Ensure all required keys are present

3. **Connection pool exhausted**
   - Increase `max_connections` if needed
   - Ensure proper cleanup after use
   - Check for connection leaks

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('src.core.code_management_client').setLevel(logging.DEBUG)
```

## Integration with Beverly Knits Planner

The code management client integrates seamlessly with other Beverly Knits components:

```python
from src.core.code_management_client import BeverlyKnitsCodeManager
from src.core.ml_integration_client import BeverlyKnitsMLClient

# Use together for comprehensive system management
code_manager = BeverlyKnitsCodeManager()
ml_client = BeverlyKnitsMLClient()

# Analyze ML code quality
quality = await code_manager.analyze_textile_code_quality("models/demand_forecast.py")

# Generate optimized code based on ML insights
if quality['maintainability'] < 0.7:
    await code_manager.refactor_planning_algorithm("models/demand_forecast.py", "readability")
```

## Future Enhancements

- Support for additional programming languages
- Real-time code monitoring
- Integration with CI/CD pipelines
- Advanced refactoring patterns
- Custom template creation UI

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example code in `examples/code_management_demo.py`
3. Check the unit tests for usage patterns
4. Consult the main project documentation