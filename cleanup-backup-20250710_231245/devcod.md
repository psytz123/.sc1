
# Development & Code Management Integration for Beverly Knits

## Overview
This document outlines the integration of zen-mcp-server for development and code management capabilities within the Beverly Knits AI Raw Material Planner project.

## Use Cases for Beverly Knits

### 1. Automated Code Analysis
- **BOM Processing Code Quality**: Analyze bill of materials processing logic
- **Inventory Management Code Review**: Review inventory calculation algorithms
- **Supplier Integration Code**: Validate supplier API integration code
- **Data Pipeline Code**: Ensure data processing pipeline reliability

### 2. Code Generation
- **New Material Type Handlers**: Generate code for new yarn/fabric types
- **Supplier Integration Modules**: Create new supplier API connectors
- **Report Generation Components**: Build new analytics report generators
- **Data Validation Rules**: Generate validation logic for textile data

### 3. Code Refactoring
- **Performance Optimization**: Optimize planning algorithm performance
- **Modular Architecture**: Refactor monolithic functions into modules
- **Error Handling Enhancement**: Improve error handling across the system
- **Documentation Generation**: Auto-generate code documentation

## Integration Steps

### Step 1: Setup Python MCP Client for Code Management

```python
# src/core/code_management_client.py
import subprocess
import json
import logging
import os
import time
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path

class BeverlyKnitsCodeManager:
    """Code management client for Beverly Knits using zen-mcp-server"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.zen_process = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> None:
        """Initialize zen-mcp-server for code management"""
        try:
            config_path = self.project_root / "config" / "zen_code_config.json"
            self.zen_process = subprocess.Popen([
                'zen-mcp-server',
                '--config', str(config_path),
                '--mode', 'code_management'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, text=True)
            
            self.logger.info("✅ Code management capabilities initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize code management: {e}")
            raise
    
    async def analyze_textile_code_quality(self, module_path: str) -> Dict[str, Any]:
        """Analyze code quality for textile-specific modules"""
        request = {
            "tool": "analyze_code_quality",
            "arguments": {
                "path": module_path,
                "language": "python",
                "industry_context": "textile_manufacturing",
                "focus_areas": [
                    "bom_processing_logic",
                    "inventory_calculations",
                    "supplier_integrations",
                    "data_validation"
                ],
                "quality_metrics": [
                    "complexity",
                    "maintainability", 
                    "textile_domain_compliance",
                    "performance_efficiency"
                ]
            }
        }
        
        return await self._call_zen_tool(request)
    
    async def generate_material_handler(self, material_type: str, properties: List[str]) -> str:
        """Generate code for handling new material types"""
        request = {
            "tool": "generate_material_handler",
            "arguments": {
                "material_type": material_type,
                "properties": properties,
                "template": "beverly_knits_material_handler",
                "include_validation": True,
                "include_tests": True,
                "output_format": "python_class"
            }
        }
        
        result = await self._call_zen_tool(request)
        
        # Save generated code
        output_path = self.project_root / "models" / f"{material_type.lower()}_handler.py"
        with open(output_path, 'w') as f:
            f.write(result['generated_code'])
            
        return str(output_path)
    
    async def refactor_planning_algorithm(self, algorithm_file: str, optimization_type: str) -> Dict[str, Any]:
        """Refactor planning algorithms for better performance"""
        with open(algorithm_file, 'r') as f:
            current_code = f.read()
            
        request = {
            "tool": "refactor_algorithm",
            "arguments": {
                "code": current_code,
                "file_path": algorithm_file,
                "optimization_type": optimization_type,
                "domain": "textile_supply_chain",
                "preserve_functionality": True,
                "add_performance_metrics": True,
                "include_documentation": True
            }
        }
        
        result = await self._call_zen_tool(request)
        
        # Create backup and save refactored code
        backup_path = f"{algorithm_file}.backup.{int(time.time())}"
        shutil.copy2(algorithm_file, backup_path)
        
        with open(algorithm_file, 'w') as f:
            f.write(result['refactored_code'])
            
        return {
            "refactored_file": algorithm_file,
            "backup_file": backup_path,
            "improvements": result.get('improvements', []),
            "performance_gain": result.get('performance_metrics', {})
        }
    
    async def generate_supplier_connector(self, supplier_name: str, api_spec: Dict) -> str:
        """Generate supplier API connector code"""
        request = {
            "tool": "generate_supplier_connector",
            "arguments": {
                "supplier_name": supplier_name,
                "api_specification": api_spec,
                "template": "beverly_knits_supplier_base",
                "include_error_handling": True,
                "include_rate_limiting": True,
                "include_data_validation": True,
                "output_directory": "integrations/suppliers"
            }
        }
        
        result = await self._call_zen_tool(request)
        
        output_path = self.project_root / "integrations" / "suppliers" / f"{supplier_name.lower()}_connector.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(result['connector_code'])
            
        return str(output_path)
    
    async def _call_zen_tool(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to call zen-mcp-server tools"""
        if not self.zen_process:
            raise RuntimeError("Code management client not initialized")
            
        try:
            json_request = json.dumps(request) + '\n'
            self.zen_process.stdin.write(json_request)
            self.zen_process.stdin.flush()
            
            response_line = self.zen_process.stdout.readline()
            response = json.loads(response_line)
            
            if "error" in response:
                raise Exception(f"Tool call failed: {response['error']}")
                
            return response.get("result", {})
            
        except Exception as e:
            self.logger.error(f"❌ Zen tool call failed: {e}")
            raise