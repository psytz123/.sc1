"""
Integration tests for Code-Enhanced Planner - Full Workflow
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.core.code_enhanced_planner import CodeEnhancedPlanner


class TestCodeEnhancedPlannerIntegration:
    """Full integration tests for the enhanced planner workflow"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            "planning_horizon_days": 90,
            "safety_stock_factor": 1.5,
            "ml_config_path": "config/test_ml_config.json",
            "optimization_settings": {
                "enable_performance_optimization": True,
                "enable_code_analysis": True,
                "cache_analysis_results": True
            }
        }
    
    @pytest.fixture
    def planner(self, config):
        """Create planner instance with mocked dependencies"""
        with patch('src.core.code_enhanced_planner.BeverlyKnitsCodeManager'):
            with patch('src.core.code_enhanced_planner.BeverlyKnitsMLClient'):
                planner = CodeEnhancedPlanner(config)
                
                # Mock code manager
                planner.code_manager = AsyncMock()
                planner.code_manager.initialize = AsyncMock()
                planner.code_manager.analyze_textile_code_quality = AsyncMock()
                planner.code_manager.refactor_planning_algorithm = AsyncMock()
                planner.code_manager.generate_material_handler = AsyncMock()
                planner.code_manager.generate_supplier_connector = AsyncMock()
                planner.code_manager.validate_textile_patterns = AsyncMock()
                
                # Mock ML client
                planner.ml_client = Mock()
                planner.ml_client.zen_available = True
                planner.ml_client.predict_demand = AsyncMock()
                planner.ml_client.optimize_inventory = AsyncMock()
                
                return planner
    
    @pytest.mark.asyncio
    async def test_full_planning_workflow(self, planner):
        """Test complete planning workflow with code enhancements"""
        # Step 1: Initialize capabilities
        await planner.initialize_enhanced_capabilities()
        planner.code_manager.initialize.assert_called_once()
        
        # Step 2: Analyze code quality before planning
        planner.code_manager.analyze_textile_code_quality.return_value = {
            "complexity_score": 15,
            "test_coverage": 85,
            "issues": ["unused_import"],
            "optimization_opportunities": ["simplify_loop"]
        }
        
        analysis_results = await planner.analyze_planning_code_quality()
        assert analysis_results["summary"]["analyzed"] > 0
        assert len(analysis_results["recommendations"]) > 0
        
        # Step 3: Optimize performance if needed
        if analysis_results["summary"]["optimization_opportunities"] > 5:
            planner.code_manager.refactor_planning_algorithm.return_value = {
                "status": "success",
                "changes_made": 3,
                "performance_improvement": 20
            }
            
            optimization_results = await planner.optimize_planning_performance()
            assert optimization_results["summary"]["successful"] > 0
        
        # Step 4: Run enhanced planning with ML predictions
        forecast_data = {
            "forecasts": [
                {
                    "sku": "KNIT-001",
                    "quantity": 1000,
                    "date": "2024-03-01"
                }
            ]
        }
        
        planner.ml_client.predict_demand.return_value = {
            "predictions": {
                "KNIT-001": {
                    "predicted_quantity": 1200,
                    "confidence": 0.85
                }
            }
        }
        
        planning_results = await planner.run_enhanced_planning(forecast_data)
        assert "ml_predictions" in planning_results
        assert "code_quality_score" in planning_results
        
        # Step 5: Generate new material support if needed
        new_material_needed = planning_results.get("new_materials_detected", False)
        if new_material_needed:
            planner.code_manager.generate_material_handler.return_value = (
                "# Generated handler for bamboo fiber"
            )
            
            material_support = await planner.generate_new_material_support(
                "bamboo_fiber",
                ["sustainable", "antibacterial", "moisture_wicking"]
            )
            assert material_support["status"] == "success"
        
        # Step 6: Validate planning patterns
        planner.code_manager.validate_textile_patterns.return_value = {
            "compliance_score": 0.92,
            "patterns_found": ["material_handling", "supplier_management"],
            "violations": []
        }
        
        validation_results = await planner.validate_planning_patterns()
        assert validation_results["compliance_score"] > 0.8
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, planner):
        """Test concurrent execution of multiple operations"""
        # Mock all async methods
        planner.code_manager.analyze_textile_code_quality.return_value = {
            "complexity_score": 10
        }
        planner.code_manager.validate_textile_patterns.return_value = {
            "compliance_score": 0.9
        }
        planner.ml_client.predict_demand.return_value = {
            "predictions": {}
        }
        
        # Run multiple operations concurrently
        tasks = [
            planner.analyze_planning_code_quality(),
            planner.validate_planning_patterns(),
            planner.run_enhanced_planning({"forecasts": []})
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(result is not None for result in results)
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, planner):
        """Test workflow with errors and recovery"""
        # Initialize with partial failure
        planner.code_manager.initialize.side_effect = [
            Exception("First attempt failed"),
            None  # Success on retry
        ]
        
        # First attempt fails
        with pytest.raises(Exception):
            await planner.initialize_enhanced_capabilities()
        
        # Retry succeeds
        await planner.initialize_enhanced_capabilities()
        assert planner.code_manager.initialize.call_count == 2
        
        # Continue with workflow despite some errors
        planner.code_manager.analyze_textile_code_quality.side_effect = [
            Exception("Analysis failed for module 1"),
            {"complexity_score": 15},  # Success for module 2
            {"complexity_score": 20},  # Success for module 3
        ]
        
        results = await planner.analyze_planning_code_quality()
        
        # Should have partial results
        assert results["summary"]["analyzed"] > 0
        assert any("error" in module for module in results["modules"].values())
        assert any("complexity_score" in module for module in results["modules"].values() 
                  if isinstance(module, dict) and "error" not in module)
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, planner):
        """Test performance monitoring during operations"""
        # Mock slow operation
        async def slow_analysis(*args):
            await asyncio.sleep(0.1)
            return {"complexity_score": 15}
        
        planner.code_manager.analyze_textile_code_quality = slow_analysis
        
        start_time = datetime.now()
        results = await planner.analyze_planning_code_quality()
        end_time = datetime.now()
        
        # Check that operation completed
        assert results["summary"]["analyzed"] > 0
        
        # Verify timing (should take at least 0.1 seconds per module)
        duration = (end_time - start_time).total_seconds()
        assert duration >= 0.1
    
    @pytest.mark.asyncio
    async def test_cache_effectiveness(self, planner):
        """Test that caching improves performance"""
        call_count = 0
        
        async def counting_analysis(*args):
            nonlocal call_count
            call_count += 1
            return {"complexity_score": 15}
        
        planner.code_manager.analyze_textile_code_quality = counting_analysis
        
        # First run - should call analysis for each module
        await planner.analyze_planning_code_quality()
        first_call_count = call_count
        
        # Second run - should use cache
        await planner.analyze_planning_code_quality()
        second_call_count = call_count
        
        # Cache should prevent additional calls
        assert second_call_count == first_call_count
        
        # Clear cache and run again
        planner.analysis_cache.clear()
        await planner.analyze_planning_code_quality()
        third_call_count = call_count
        
        # Should make new calls after cache clear
        assert third_call_count > second_call_count