"""
Unit tests for BeverlyKnitsCodeManager

Tests cover:
- Configuration loading and validation
- Connection pooling
- Code analysis functionality
- Code generation functionality
- Error handling and retry logic
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from src.core.code_management_client import BeverlyKnitsCodeManager


class TestBeverlyKnitsCodeManager:
    """Test suite for BeverlyKnitsCodeManager"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with required structure"""
        temp_dir = tempfile.mkdtemp()
        
        # Create config directory and file
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        config_data = {
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
        
        with open(config_dir / "zen_code_config.json", 'w') as f:
            json.dump(config_data, f)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_project_dir):
        """Create a BeverlyKnitsCodeManager instance"""
        return BeverlyKnitsCodeManager(project_root=temp_project_dir)
    
    def test_initialization(self, manager, temp_project_dir):
        """Test manager initialization"""
        assert manager.project_root == Path(temp_project_dir)
        assert manager.config_path.exists()
        assert manager.max_connections == 5
        assert len(manager.connection_pool) == 0
        
        # Check if directories were created
        assert (manager.templates_path).exists()
        assert (manager.output_path).exists()
        assert (manager.project_root / "models").exists()
        assert (manager.project_root / "integrations" / "suppliers").exists()
    
    def test_config_validation_missing_file(self, temp_project_dir):
        """Test configuration validation with missing file"""
        # Remove config file
        config_path = Path(temp_project_dir) / "config" / "zen_code_config.json"
        config_path.unlink()
        
        with pytest.raises(FileNotFoundError):
            BeverlyKnitsCodeManager(project_root=temp_project_dir)
    
    def test_config_validation_invalid_structure(self, temp_project_dir):
        """Test configuration validation with invalid structure"""
        config_path = Path(temp_project_dir) / "config" / "zen_code_config.json"
        
        # Write invalid config
        with open(config_path, 'w') as f:
            json.dump({"invalid": "config"}, f)
        
        with pytest.raises(ValueError, match="Missing required configuration key"):
            BeverlyKnitsCodeManager(project_root=temp_project_dir)
    
    def test_config_validation_invalid_thresholds(self, temp_project_dir):
        """Test configuration validation with invalid thresholds"""
        config_path = Path(temp_project_dir) / "config" / "zen_code_config.json"
        
        # Write config with invalid thresholds
        config_data = {
            "code_management": {
                "analysis": {
                    "languages": ["python"],
                    "quality_thresholds": {
                        "complexity": "not_a_number",
                        "maintainability": 2.0  # Out of range
                    }
                },
                "generation": {
                    "templates_path": "templates/",
                    "output_path": "generated/"
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with pytest.raises(ValueError, match="complexity threshold must be a number"):
            BeverlyKnitsCodeManager(project_root=temp_project_dir)
    
    @pytest.mark.asyncio
    async def test_initialize_connection_pool(self, manager):
        """Test connection pool initialization"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            await manager.initialize()
            
            # Should create 3 initial connections
            assert mock_popen.call_count == 3
            assert len(manager.connection_pool) == 3
    
    @pytest.mark.asyncio
    async def test_connection_pool_management(self, manager):
        """Test getting and returning connections"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            await manager.initialize()
            initial_pool_size = len(manager.connection_pool)
            
            # Get a connection
            conn = await manager._get_connection()
            assert len(manager.connection_pool) == initial_pool_size - 1
            
            # Return the connection
            await manager._return_connection(conn)
            assert len(manager.connection_pool) == initial_pool_size
    
    @pytest.mark.asyncio
    async def test_analyze_textile_code_quality(self, manager):
        """Test code quality analysis"""
        with patch.object(manager, '_call_zen_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "complexity": 8,
                "maintainability": 0.85,
                "issues": []
            }
            
            result = await manager.analyze_textile_code_quality("test_module.py")
            
            assert result["complexity"] == 8
            assert result["maintainability"] == 0.85
            
            # Verify the request
            mock_call.assert_called_once()
            request = mock_call.call_args[0][0]
            assert request["tool"] == "analyze_code_quality"
            assert request["arguments"]["path"] == "test_module.py"
            assert "bom_processing_logic" in request["arguments"]["focus_areas"]
    
    @pytest.mark.asyncio
    async def test_generate_material_handler(self, manager):
        """Test material handler generation"""
        with patch.object(manager, '_call_zen_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "generated_code": "class CottonHandler:\n    pass"
            }
            
            output_path = await manager.generate_material_handler(
                "Cotton",
                ["weight", "thread_count"]
            )
            
            # Check if file was created
            expected_path = manager.project_root / "models" / "cotton_handler.py"
            assert Path(output_path) == expected_path
            assert expected_path.exists()
            
            with open(expected_path, 'r') as f:
                content = f.read()
                assert content == "class CottonHandler:\n    pass"
    
    @pytest.mark.asyncio
    async def test_refactor_planning_algorithm(self, manager):
        """Test algorithm refactoring"""
        # Create a test algorithm file
        test_file = manager.project_root / "test_algorithm.py"
        with open(test_file, 'w') as f:
            f.write("def old_algorithm():\n    pass")
        
        with patch.object(manager, '_call_zen_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "refactored_code": "def optimized_algorithm():\n    pass",
                "improvements": ["Reduced complexity"],
                "performance_metrics": {"speed_gain": "20%"}
            }
            
            result = await manager.refactor_planning_algorithm(
                str(test_file),
                "performance"
            )
            
            # Check backup was created
            assert "backup_file" in result
            assert Path(result["backup_file"]).exists()
            
            # Check refactored file
            with open(test_file, 'r') as f:
                content = f.read()
                assert content == "def optimized_algorithm():\n    pass"
    
    @pytest.mark.asyncio
    async def test_generate_supplier_connector(self, manager):
        """Test supplier connector generation"""
        with patch.object(manager, '_call_zen_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "connector_code": "class SupplierAConnector:\n    pass"
            }
            
            api_spec = {
                "base_url": "https://api.supplier.com",
                "auth_type": "bearer"
            }
            
            output_path = await manager.generate_supplier_connector(
                "SupplierA",
                api_spec
            )
            
            expected_path = manager.project_root / "integrations" / "suppliers" / "suppliera_connector.py"
            assert Path(output_path) == expected_path
            assert expected_path.exists()
    
    @pytest.mark.asyncio
    async def test_call_zen_tool_retry_logic(self, manager):
        """Test retry logic in _call_zen_tool"""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.stdout.readline.side_effect = [
            TimeoutError("Timeout"),
            json.dumps({"result": {"success": True}})
        ]
        
        with patch.object(manager, '_get_connection', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_process
            
            with patch.object(manager, '_return_connection', new_callable=AsyncMock):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    result = await manager._call_zen_tool({"tool": "test"})
                    
                    assert result == {"success": True}
                    assert mock_get.call_count == 2  # One retry
    
    @pytest.mark.asyncio
    async def test_call_zen_tool_max_retries_exceeded(self, manager):
        """Test when max retries are exceeded"""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.stdout.readline.side_effect = TimeoutError("Timeout")
        
        with patch.object(manager, '_get_connection', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_process
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(Exception):
                    await manager._call_zen_tool({"tool": "test"})
    
    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """Test cleanup of connections"""
        # Create mock processes
        mock_processes = []
        for _ in range(3):
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_processes.append(mock_process)
        
        manager.connection_pool = mock_processes
        
        await manager.cleanup()
        
        # All processes should be terminated
        for process in mock_processes:
            process.terminate.assert_called_once()
            process.wait.assert_called_once_with(timeout=5)
        
        assert len(manager.connection_pool) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_code_complexity(self, manager):
        """Test code complexity analysis"""
        with patch.object(manager, '_call_zen_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "cyclomatic": 5,
                "cognitive": 8,
                "halstead": {"difficulty": 12}
            }
            
            result = await manager.analyze_code_complexity("test.py")
            
            assert result["cyclomatic"] == 5
            assert result["cognitive"] == 8
            
            # Verify request
            request = mock_call.call_args[0][0]
            assert request["tool"] == "analyze_complexity"
            assert request["arguments"]["file_path"] == "test.py"
            assert "cyclomatic" in request["arguments"]["metrics"]
    
    @pytest.mark.asyncio
    async def test_generate_documentation(self, manager):
        """Test documentation generation"""
        with patch.object(manager, '_call_zen_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "documentation": "# Module Documentation\n\nTest content"
            }
            
            doc_path = await manager.generate_documentation("module.py", "markdown")
            
            expected_path = manager.project_root / "docs" / "module_doc.markdown"
            assert Path(doc_path) == expected_path
            assert expected_path.exists()
            
            with open(expected_path, 'r') as f:
                content = f.read()
                assert content == "# Module Documentation\n\nTest content"
    
    @pytest.mark.asyncio
    async def test_validate_textile_patterns(self, manager):
        """Test textile pattern validation"""
        with patch.object(manager, '_call_zen_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "valid": True,
                "patterns_found": ["bom_calculation_pattern"],
                "violations": []
            }
            
            result = await manager.validate_textile_patterns("code.py")
            
            assert result["valid"] is True
            assert "bom_calculation_pattern" in result["patterns_found"]
    
    @pytest.mark.asyncio
    async def test_optimize_data_processing(self, manager):
        """Test data processing optimization"""
        with patch.object(manager, '_call_zen_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "optimized": True,
                "improvements": {
                    "memory_efficiency": "30% reduction",
                    "processing_speed": "2x faster"
                }
            }
            
            result = await manager.optimize_data_processing("pipeline.py")
            
            assert result["optimized"] is True
            assert "memory_efficiency" in result["improvements"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])