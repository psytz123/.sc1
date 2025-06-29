"""
Beverly Knits Code Management Client

This module provides code analysis, generation, and management capabilities
for the Beverly Knits Raw Material Planner using zen-mcp-server.
"""

import asyncio
import json
import logging
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BeverlyKnitsCodeManager:
    """Code management client for Beverly Knits using zen-mcp-server"""
    
    def __init__(self, project_root: str = ".", config_path: str = None):
        self.project_root = Path(project_root)
        self.config_path = Path(config_path or self.project_root / "config" / "zen_code_config.json")
        self.zen_process = None
        self.logger = logging.getLogger(__name__)
        
        # Connection pooling
        self.connection_pool = []
        self.max_connections = 5
        self.connection_lock = threading.Lock()
        
        # Load and validate configuration
        self.config = self._load_and_validate_config()
        
        # Set up paths from config
        self.templates_path = self.project_root / self.config["code_management"]["generation"]["templates_path"]
        self.output_path = self.project_root / self.config["code_management"]["generation"]["output_path"]
        
        # Ensure directories exist
        self._ensure_directories()
        
        self.logger.info(f"✅ Initialized BeverlyKnitsCodeManager with project root: {self.project_root}")
    
    def _load_and_validate_config(self) -> Dict[str, Any]:
        """Load and validate configuration from JSON file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required configuration keys
            required_keys = {
                "code_management": {
                    "analysis": ["languages", "quality_thresholds"],
                    "generation": ["templates_path", "output_path"]
                }
            }
            
            self._validate_config_structure(config, required_keys)
            
            # Validate quality thresholds
            thresholds = config["code_management"]["analysis"]["quality_thresholds"]
            if not isinstance(thresholds.get("complexity"), (int, float)):
                raise ValueError("complexity threshold must be a number")
            if not 0 <= thresholds.get("maintainability", 0) <= 1:
                raise ValueError("maintainability threshold must be between 0 and 1")
            
            self.logger.info("✅ Configuration validated successfully")
            return config
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load or validate config: {e}")
            raise
    
    def _validate_config_structure(self, config: Dict, required: Dict, path: str = "") -> None:
        """Recursively validate configuration structure."""
        for key, value in required.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in config:
                raise ValueError(f"Missing required configuration key: {current_path}")
            
            if isinstance(value, dict):
                self._validate_config_structure(config[key], value, current_path)
            elif isinstance(value, list):
                for item in value:
                    if item not in config[key]:
                        raise ValueError(f"Missing required configuration key: {current_path}.{item}")
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.templates_path,
            self.output_path,
            self.project_root / "models",
            self.project_root / "integrations" / "suppliers",
            self.project_root / "temp" / "code_analysis"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("✅ All required directories created/verified")
    
    async def initialize(self) -> None:
        """Initialize zen-mcp-server for code management with connection pooling"""
        try:
            # Create initial connections
            for _ in range(min(3, self.max_connections)):  # Start with 3 connections
                await self._create_connection()
            
            self.logger.info("✅ Code management capabilities initialized with connection pool")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize code management: {e}")
            raise
    
    async def _create_connection(self) -> subprocess.Popen:
        """Create a new zen-mcp-server connection."""
        try:
            process = subprocess.Popen([
                'zen-mcp-server',
                '--config', str(self.config_path),
                '--mode', 'code_management'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, text=True)
            
            with self.connection_lock:
                self.connection_pool.append(process)
            
            return process
        except Exception as e:
            self.logger.error(f"❌ Failed to create connection: {e}")
            raise
    
    async def _get_connection(self) -> subprocess.Popen:
        """Get an available connection from the pool."""
        with self.connection_lock:
            if self.connection_pool:
                return self.connection_pool.pop(0)
        
        # Create new connection if pool is empty and under limit
        if len(self.connection_pool) < self.max_connections:
            return await self._create_connection()
        
        # Wait for a connection to become available
        await asyncio.sleep(0.1)
        return await self._get_connection()
    
    async def _return_connection(self, process: subprocess.Popen) -> None:
        """Return a connection to the pool."""
        if process.poll() is None:  # Process is still running
            with self.connection_lock:
                self.connection_pool.append(process)
        else:
            # Replace dead connection
            await self._create_connection()
    
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
    
    async def analyze_code_complexity(self, file_path: str) -> Dict[str, Any]:
        """Analyze code complexity metrics for a given file."""
        request = {
            "tool": "analyze_complexity",
            "arguments": {
                "file_path": file_path,
                "metrics": ["cyclomatic", "cognitive", "halstead"],
                "threshold": self.config["code_management"]["analysis"]["quality_thresholds"]["complexity"]
            }
        }
        
        return await self._call_zen_tool(request)
    
    async def generate_documentation(self, module_path: str, doc_format: str = "markdown") -> str:
        """Generate documentation for a module."""
        request = {
            "tool": "generate_documentation",
            "arguments": {
                "module_path": module_path,
                "format": doc_format,
                "include_examples": True,
                "include_api_reference": True,
                "textile_context": True
            }
        }
        
        result = await self._call_zen_tool(request)
        
        # Save documentation
        doc_path = self.project_root / "docs" / f"{Path(module_path).stem}_doc.{doc_format}"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(doc_path, 'w') as f:
            f.write(result['documentation'])
            
        return str(doc_path)
    
    async def validate_textile_patterns(self, code_path: str) -> Dict[str, Any]:
        """Validate code against textile industry patterns and best practices."""
        request = {
            "tool": "validate_patterns",
            "arguments": {
                "code_path": code_path,
                "patterns": [
                    "bom_calculation_pattern",
                    "inventory_management_pattern",
                    "supplier_integration_pattern",
                    "material_handling_pattern"
                ],
                "industry": "textile_manufacturing"
            }
        }
        
        return await self._call_zen_tool(request)
    
    async def optimize_data_processing(self, pipeline_file: str) -> Dict[str, Any]:
        """Optimize data processing pipelines for textile data."""
        request = {
            "tool": "optimize_pipeline",
            "arguments": {
                "pipeline_file": pipeline_file,
                "optimization_targets": [
                    "memory_efficiency",
                    "processing_speed",
                    "batch_processing",
                    "parallel_execution"
                ],
                "data_types": ["bom", "inventory", "supplier", "forecast"]
            }
        }
        
        return await self._call_zen_tool(request)
    
    async def _call_zen_tool(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to call zen-mcp-server tools with connection pooling and retry logic"""
        max_retries = 3
        retry_delay = 1.0
        last_exception = None

        for attempt in range(max_retries):
            process = None
            try:
                # Get connection from pool
                process = await self._get_connection()

                if not process or process.poll() is not None:
                    raise RuntimeError("No valid connection available")

                # Send request
                json_request = json.dumps(request) + '\n'
                process.stdin.write(json_request)
                process.stdin.flush()

                # Read response with timeout
                response_line = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, process.stdout.readline
                    ),
                    timeout=30.0
                )

                response = json.loads(response_line)

                if "error" in response:
                    raise Exception(f"Tool call failed: {response['error']}")

                # Return connection to pool
                await self._return_connection(process)

                return response.get("result", {})

            except asyncio.TimeoutError as e:
                self.logger.warning(f"⚠️ Request timeout on attempt {attempt + 1}")
                last_exception = e
                if process:
                    process.terminate()

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))

            except Exception as e:
                self.logger.error(f"❌ Zen tool call failed on attempt {attempt + 1}: {e}")
                last_exception = e
                if process and process.poll() is None:
                    await self._return_connection(process)

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    raise

        # If we've exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception
        else:
            raise Exception("Failed to call zen tool after all retries")
    
    async def cleanup(self) -> None:
        """Clean up all connections in the pool."""
        with self.connection_lock:
            for process in self.connection_pool:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            self.connection_pool.clear()
        
        self.logger.info("✅ All connections cleaned up")
    
    def __repr__(self):
        return f"BeverlyKnitsCodeManager(project_root='{self.project_root}', config_path='{self.config_path}')"


# Example usage and testing
async def main():
    """Example usage of the BeverlyKnitsCodeManager"""
    manager = BeverlyKnitsCodeManager()
    
    try:
        # Initialize the manager
        await manager.initialize()
        
        # Example: Analyze code quality
        quality_report = await manager.analyze_textile_code_quality("src/core/ml_integration_client.py")
        print(f"Code quality report: {quality_report}")
        
        # Example: Generate material handler
        material_path = await manager.generate_material_handler(
            "CottonBlend",
            ["weight", "thread_count", "shrinkage_rate", "color_fastness"]
        )
        print(f"Generated material handler at: {material_path}")
        
    finally:
        # Clean up connections
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())