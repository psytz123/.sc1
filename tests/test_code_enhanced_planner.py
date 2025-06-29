"""
Integration tests for Code-Enhanced Planner
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.core.code_enhanced_planner import CodeEnhancedPlanner, create_enhanced_planner


class TestCodeEnhancedPlanner:
    """Integration tests for the enhanced planner"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            "planning_horizon_days": 90,
            "safety_stock_factor": 1.5,
            "ml_config_path": "config/test_ml_config.json"
        }
    
    @pytest.fixture
    def planner(self, config):
        """Create planner instance"""
        with patch('src.core.code_enhanced_planner.BeverlyKnitsCodeManager'):
            with patch('src.core.code_enhanced_planner.BeverlyKnitsMLClient'):
                planner = CodeEnhancedPlanner(config)
                planner.code_manager = AsyncMock()
                planner.ml_client = Mock()
                planner.ml_client.zen_available = True
                return planner
    
    @pytest.mark.asyncio
    async def test_initialize_enhanced_capabilities(self, planner):
        """Test initialization of enhanced capabilities"""
        planner.code_manager.initialize = AsyncMock()
        
        await planner.initialize_enhanced_capabilities()
        
        planner.code_manager.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_planning_code_quality(self, planner):
        """Test code quality analysis"""
        # Mock analysis results
        mock_result = {
            "complexity_score": 15,
            "test_coverage": 85,
            "issues": ["unused_import"],
            "optimization_opportunities": ["simplify_loop"]
        }
        
        planner.code_manager.analyze_textile_code_quality = AsyncMock(return_value=mock_result)
        
        results = await planner.analyze_planning_code_quality()
        
        assert "timestamp" in results
        assert "modules" in results
        assert "summary" in results
        assert "recommendations" in results
        
        # Check summary calculations
        assert results["summary"]["analyzed"] > 0
        assert isinstance(results["recommendations"], list)
    
    @pytest.mark.asyncio
    async def test_generate_code_recommendations(self, planner):
        """Test recommendation generation"""
        analysis = {
            "summary": {
                "issues_found": 15,
                "optimization_opportunities": 8
            },
            "modules": {
                "test.py": {
                    "complexity_score": 25,
                    "test_coverage": 60
                }
            }
        }
        
        recommendations = planner._generate_code_recommendations(analysis)
        
        assert len(recommendations) > 0
        assert any("code review" in r for r in recommendations)
        assert any("complexity" in r for r in recommendations)
        assert any("test coverage" in r for r in recommendations)
    
    @pytest.mark.asyncio
    async def test_generate_new_material_support(self, planner):
        """Test new material support generation"""
        material_type = "recycled_polyester"
        properties = ["recyclable", "moisture_wicking", "durable"]
        
        planner.code_manager.generate_material_handler = AsyncMock(
            return_value="# Generated material handler code"
        )
        
        result = await planner.generate_new_material_support(material_type, properties)
        
        assert result["material_type"] == material_type
        assert result["properties"] == properties
        assert "generated_files" in result
        assert "integration_steps" in result
        assert "sample_config" in result
        
        # Check generated config
        config = result["sample_config"]
        assert config["material_type"] == material_type
        assert all(prop in config["properties"] for prop in properties)
    
    @pytest.mark.asyncio
    async def test_optimize_planning_performance(self, planner):
        """Test performance optimization"""
        # Mock optimization results
        planner.code_manager.refactor_planning_algorithm = AsyncMock(
            return_value={
                "status": "success",
                "changes_made": 5,
                "estimated_improvement": "20%"
            }
        )
        
        # Mock performance measurements
        planner._measure_performance = AsyncMock(
            side_effect=[
                {"execution_time": 2.0, "memory_usage": 150.0, "complexity_score": 20.0},
                {"execution_time": 1.6, "memory_usage": 120.0, "complexity_score": 15.0}
            ]
        )
        
        results = await planner.optimize_planning_performance()
        
        assert results["status"] == "completed"
        assert "optimizations" in results
        assert "performance_improvements" in results
        assert "summary" in results
        
        # Check that improvements were calculated
        improvements = list(results["performance_improvements"].values())[0]
        assert improvements["execution_time"]["improvement_percentage"] == 20.0
    
    @pytest.mark.asyncio
    async def test_generate_supplier_integration(self, planner):
        """Test supplier integration generation"""
        supplier_name = "textile_supplier_xyz"
        api_spec = {
            "base_url": "https://api.supplier.com",
            "auth_type": "oauth2",
            "endpoints": {
                "inventory": "/api/v1/inventory",
                "orders": "/api/v1/orders"
            }
        }
        
        planner.code_manager.generate_supplier_connector = AsyncMock(
            return_value="# Generated connector code"
        )
        
        result = await planner.generate_supplier_integration(supplier_name, api_spec)
        
        assert result["supplier_name"] == supplier_name
        assert "generated_files" in result
        assert "connector_code" in result
        assert "test_template" in result
        assert "configuration_template" in result
        
        # Check configuration template
        config = result["configuration_template"]
        assert config["supplier_name"] == supplier_name
        assert config["api_configuration"]["base_url"] == api_spec["base_url"]
    
    @pytest.mark.asyncio
    async def test_validate_planning_patterns(self, planner):
        """Test textile pattern validation"""
        planner.code_manager.validate_textile_patterns = AsyncMock(
            return_value={
                "compliance_score": 0.85,
                "patterns_found": ["material_handling", "supplier_management"],
                "violations": []
            }
        )
        
        results = await planner.validate_planning_patterns()
        
        assert "timestamp" in results
        assert "validations" in results
        assert "compliance_score" in results
        assert results["compliance_score"] > 0
        
        # Should not have recommendations for good compliance
        assert len(results["recommendations"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_planning_patterns_low_compliance(self, planner):
        """Test validation with low compliance score"""
        planner.code_manager.validate_textile_patterns = AsyncMock(
            return_value={
                "compliance_score": 0.6,
                "patterns_found": ["material_handling"],
                "violations": ["missing_supplier_patterns"]
            }
        )
        
        results = await planner.validate_planning_patterns()
        
        assert results["compliance_score"] < 0.8
        assert len(results["recommendations"]) > 0
        assert any("compliance score is below 80%" in r for r in results["recommendations"])
    
    @pytest.mark.asyncio
    async def test_optimize_data_processing_pipeline(self, planner):
        """Test data pipeline optimization"""
        with patch('pathlib.Path.exists', return_value=True):
            planner.code_manager.optimize_data_processing = AsyncMock(
                return_value={
                    "optimization_applied": True,
                    "changes": ["vectorized_operations", "batch_processing"],
                    "estimated_speedup": 1.25
                }
            )
            
            results = await planner.optimize_data_processing_pipeline()
            
            assert "timestamp" in results
            assert "optimizations" in results
            assert "estimated_improvements" in results
            
            # Check that improvements were estimated
            improvements = list(results["estimated_improvements"].values())
            assert len(improvements) > 0
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_documentation(self, planner):
        """Test documentation generation"""
        planner.code_manager.generate_documentation = AsyncMock(
            return_value="# Module Documentation\n\nDetailed documentation content..."
        )
        
        with patch('pathlib.Path.mkdir'):
            results = await planner.generate_comprehensive_documentation()
            
            assert "timestamp" in results
            assert "generated_docs" in results
            assert "documentation_coverage" in results
            assert results["documentation_coverage"] > 0
    
    @pytest.mark.asyncio
    async def test_run_ml_enhanced_planning(self, planner):
        """Test ML-enhanced planning"""
        forecast_data = Mock()
        
        # Mock base planner method
        planner.plan = Mock(return_value={
            "recommendations": [],
            "total_cost": 100000
        })
        
        result = await planner.run_ml_enhanced_planning(forecast_data)
        
        assert "ml_enhancements" in result
        assert "planning_confidence" in result
        planner.plan.assert_called_once_with(forecast_data)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_analysis(self, planner):
        """Test error handling during code analysis"""
        planner.code_manager.analyze_textile_code_quality = AsyncMock(
            side_effect=Exception("Analysis failed")
        )
        
        results = await planner.analyze_planning_code_quality()
        
        # Should handle errors gracefully
        assert results["summary"]["analyzed"] == 0
        assert all("error" in module_result for module_result in results["modules"].values())
    
    @pytest.mark.asyncio
    async def test_cache_usage_in_analysis(self, planner):
        """Test that analysis results are cached"""
        mock_result = {"complexity_score": 10}
        planner.code_manager.analyze_textile_code_quality = AsyncMock(return_value=mock_result)
        
        # First call
        await planner.analyze_planning_code_quality()
        call_count_1 = planner.code_manager.analyze_textile_code_quality.call_count
        
        # Second call (should use cache)
        await planner.analyze_planning_code_quality()
        call_count_2 = planner.code_manager.analyze_textile_code_quality.call_count
        
        # Call count should be the same (cache hit)
        assert call_count_2 == call_count_1
    
    @pytest.mark.asyncio
    async def test_cleanup(self, planner):
        """Test resource cleanup"""
        planner.code_manager.cleanup = AsyncMock()
        planner.ml_client.close = AsyncMock()
        
        await planner.cleanup()
        
        planner.code_manager.cleanup.assert_called_once()
        planner.ml_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_enhanced_planner_function(self, config):
        """Test the convenience function for creating enhanced planner"""
        with patch('src.core.code_enhanced_planner.CodeEnhancedPlanner') as mock_planner_class:
            mock_instance = AsyncMock()
            mock_planner_class.return_value = mock_instance
            
            planner = await create_enhanced_planner(config)
            
            mock_planner_class.assert_called_once_with(config)
            mock_instance.initialize_enhanced_capabilities.assert_called_once()
            assert planner == mock_instance


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_optimization_workflow(self, config):
        """Test complete optimization workflow"""
        with patch('src.core.code_enhanced_planner.BeverlyKnitsCodeManager'):
            with patch('src.core.code_enhanced_planner.BeverlyKnitsMLClient'):
                planner = CodeEnhancedPlanner(config)
                planner.code_manager = AsyncMock()
                planner.ml_client = Mock()
                
                # Mock all required methods
                planner.code_manager.initialize = AsyncMock()
                planner.code_manager.analyze_textile_code_quality = AsyncMock(
                    return_value={"complexity_score": 25, "test_coverage": 70}
                )
                planner.code_manager.refactor_planning_algorithm = AsyncMock(
                    return_value={"status": "success"}
                )
                planner._measure_performance = AsyncMock(
                    side_effect=[
                        {"execution_time": 2.0},
                        {"execution_time": 1.5}
                    ]
                )
                
                # Run workflow
                await planner.initialize_enhanced_capabilities()
                analysis = await planner.analyze_planning_code_quality()
                
                # Should recommend optimization due to high complexity
                assert len(analysis["recommendations"]) > 0
                
                # Run optimization
                optimization = await planner.optimize_planning_performance()
                assert optimization["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_new_material_integration_workflow(self, config):
        """Test workflow for integrating new material type"""
        with patch('src.core.code_enhanced_planner.BeverlyKnitsCodeManager'):
            with patch('src.core.code_enhanced_planner.BeverlyKnitsMLClient'):
                planner = CodeEnhancedPlanner(config)
                planner.code_manager = AsyncMock()
                
                planner.code_manager.generate_material_handler = AsyncMock(
                    return_value="class BambooFiberHandler: pass"
                )
                
                # Generate support for new material
                result = await planner.generate_new_material_support(
                    "bamboo_fiber",
                    ["sustainable", "antibacterial", "breathable"]
                )
                
                assert result["material_type"] == "bamboo_fiber"
                assert len(result["integration_steps"]) > 0
                assert "handler_code" in result
                
                # Verify configuration includes all properties
                config = result["sample_config"]
                assert all(prop in config["properties"] for prop in ["sustainable", "antibacterial", "breathable"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])