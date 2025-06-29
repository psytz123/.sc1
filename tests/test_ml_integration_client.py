"""
Unit tests for Beverly Knits ML Integration Client
"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import numpy as np
import pandas as pd
import pytest

from src.core.ml_integration_client import ML_LIBRARIES, BeverlyKnitsMLClient


class TestBeverlyKnitsMLClient:
    """Test suite for ML integration client"""
    
    @pytest.fixture
    def ml_client(self, tmp_path):
        """Create ML client instance for testing"""
        # Create temporary config file
        config_path = tmp_path / "test_ml_config.json"
        config_data = {
            "zen_mcp_server": {
                "enabled": True,
                "url": "http://localhost:8080",
                "api_key": "test-key",
                "timeout": 5,
                "retries": 2
            },
            "ml_features": {
                "demand_forecasting": {"enabled": True},
                "supplier_risk": {"enabled": True}
            }
        }
        config_path.write_text(json.dumps(config_data))
        
        client = BeverlyKnitsMLClient(str(config_path))
        return client
    
    @pytest.fixture
    def ml_client_no_zen(self, tmp_path):
        """Create ML client without zen-mcp-server"""
        config_path = tmp_path / "test_ml_config.json"
        config_data = {
            "zen_mcp_server": {
                "enabled": False
            }
        }
        config_path.write_text(json.dumps(config_data))
        
        client = BeverlyKnitsMLClient(str(config_path))
        return client
    
    @pytest.fixture
    def sample_sales_data(self):
        """Create sample sales data for testing"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sales = np.random.randint(100, 500, size=len(dates))
        return pd.DataFrame({'date': dates, 'sales': sales})
    
    @pytest.fixture
    def sample_supplier_data(self):
        """Create sample supplier data"""
        return pd.DataFrame({
            'supplier_id': ['S001', 'S002', 'S003'],
            'delivery_performance': [0.95, 0.85, 0.75],
            'quality_metrics': [0.98, 0.92, 0.88],
            'financial_stability': [0.9, 0.8, 0.7]
        })
    
    def test_initialization(self, ml_client):
        """Test client initialization"""
        assert ml_client.zen_available == True
        assert ml_client.models_dir.exists()
        assert ml_client.temp_dir.exists()
        assert ml_client.connection_timeout == 5
        assert ml_client.connection_retries == 2
    
    def test_initialization_no_config(self, tmp_path):
        """Test initialization without config file"""
        client = BeverlyKnitsMLClient(str(tmp_path / "nonexistent.json"))
        assert client.zen_available == False
        assert client.zen_config is None
    
    @pytest.mark.asyncio
    async def test_call_zen_tool_success(self, ml_client):
        """Test successful zen tool call"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success", "data": {"test": "value"}})
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            result = await ml_client._call_zen_tool("test_tool", {"param": "value"})
            assert result["result"] == "success"
            assert result["data"]["test"] == "value"
    
    @pytest.mark.asyncio
    async def test_call_zen_tool_error(self, ml_client):
        """Test zen tool call with error response"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            result = await ml_client._call_zen_tool("test_tool", {"param": "value"})
            assert result["status"] == "error"
            assert "500" in result["message"]
    
    @pytest.mark.asyncio
    async def test_call_zen_tool_no_zen(self, ml_client_no_zen):
        """Test zen tool call when zen is not available"""
        result = await ml_client_no_zen._call_zen_tool("test_tool", {"param": "value"})
        assert result["status"] == "error"
        assert result["message"] == "zen-mcp-server not configured"
        assert result["fallback"] == "using_local_ml"
    
    @pytest.mark.asyncio
    async def test_train_demand_forecasting_model_with_zen(self, ml_client, sample_sales_data):
        """Test training demand forecasting model with zen-mcp-server"""
        mock_response = {
            "model_id": "test_model_123",
            "model_path": "/models/test_model.pkl",
            "metrics": {"mae": 10.5, "rmse": 15.2},
            "validation_score": 0.85
        }
        
        with patch.object(ml_client, '_call_zen_tool', return_value=mock_response):
            result = await ml_client.train_demand_forecasting_model(sample_sales_data, "yarn")
            
            assert result["model_id"] == "test_model_123"
            assert result["validation_score"] == 0.85
            assert "mae" in result["training_metrics"]
    
    @pytest.mark.asyncio
    @patch.dict(ML_LIBRARIES, {'sklearn': True})
    async def test_train_demand_forecasting_model_local_fallback(self, ml_client, sample_sales_data):
        """Test training with local ML when zen fails"""
        # Mock zen failure
        zen_error = {"status": "error", "message": "zen server unavailable"}
        
        with patch.object(ml_client, '_call_zen_tool', return_value=zen_error):
            with patch('sklearn.ensemble.RandomForestRegressor') as mock_rf:
                mock_model = Mock()
                mock_model.fit = Mock()
                mock_model.predict = Mock(return_value=np.array([100, 200, 300]))
                mock_rf.return_value = mock_model
                
                with patch('sklearn.metrics.mean_absolute_error', return_value=10.0):
                    with patch('sklearn.metrics.r2_score', return_value=0.8):
                        result = await ml_client.train_demand_forecasting_model(sample_sales_data, "yarn")
                        
                        assert result["model_type"] == "local_random_forest"
                        assert result["validation_score"] == 0.8
                        assert "local_demand_yarn" in result["model_id"]
    
    @pytest.mark.asyncio
    async def test_predict_material_demand_with_zen(self, ml_client):
        """Test demand prediction with zen-mcp-server"""
        mock_response = {
            "predictions": [{"day": 1, "demand": 150}, {"day": 2, "demand": 160}],
            "confidence_intervals": {"lower": [140, 150], "upper": [160, 170]},
            "model_confidence": 0.9
        }
        
        with patch.object(ml_client, '_call_zen_tool', return_value=mock_response):
            result = await ml_client.predict_material_demand("test_model", 2)
            
            assert isinstance(result["predictions"], pd.DataFrame)
            assert len(result["predictions"]) == 2
            assert result["model_confidence"] == 0.9
    
    @pytest.mark.asyncio
    async def test_train_supplier_risk_model(self, ml_client, sample_supplier_data):
        """Test training supplier risk model"""
        performance_data = pd.DataFrame({
            'supplier_id': ['S001', 'S002', 'S003'],
            'on_time_delivery': [0.95, 0.85, 0.75],
            'defect_rate': [0.02, 0.05, 0.08]
        })
        
        mock_response = {
            "model_id": "risk_model_123",
            "accuracy": 0.92,
            "precision_recall": {"precision": 0.9, "recall": 0.88}
        }
        
        with patch.object(ml_client, '_call_zen_tool', return_value=mock_response):
            result = await ml_client.train_supplier_risk_model(sample_supplier_data, performance_data)
            
            assert result["model_id"] == "risk_model_123"
            assert result["accuracy_score"] == 0.92
            assert "precision" in result["precision_recall"]
    
    @pytest.mark.asyncio
    async def test_assess_supplier_risk_with_zen(self, ml_client):
        """Test supplier risk assessment with zen"""
        supplier_info = {
            "supplier_id": "S004",
            "delivery_performance": 0.82,
            "quality_metrics": 0.89,
            "financial_stability": 0.85
        }
        
        mock_response = {
            "risk_score": 0.65,
            "risk_category": "medium",
            "confidence": 0.88,
            "risk_factors": ["delivery_performance"],
            "recommendations": ["Monitor delivery closely"]
        }
        
        with patch.object(ml_client, '_call_zen_tool', return_value=mock_response):
            result = await ml_client.assess_supplier_risk("risk_model_123", supplier_info)
            
            assert result["risk_score"] == 0.65
            assert result["risk_category"] == "medium"
            assert len(result["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_assess_supplier_risk_fallback(self, ml_client_no_zen):
        """Test supplier risk assessment fallback"""
        supplier_info = {
            "delivery_performance": 0.75,
            "quality_metrics": 0.85
        }
        
        result = await ml_client_no_zen.assess_supplier_risk("any_model", supplier_info)
        
        assert result["risk_category"] in ["low", "medium", "high"]
        assert 0 <= result["risk_score"] <= 1
        assert "simple scoring algorithm" in result["explanation"]
    
    @pytest.mark.asyncio
    async def test_optimize_inventory_with_ml(self, ml_client, sample_sales_data):
        """Test ML-powered inventory optimization"""
        inventory_data = pd.DataFrame({
            'material': ['yarn_001', 'yarn_002'],
            'current_stock': [1000, 500],
            'reorder_point': [200, 100]
        })
        
        supplier_data = pd.DataFrame({
            'supplier': ['S001', 'S002'],
            'lead_time': [14, 21]
        })
        
        mock_response = {
            "optimized_levels": [{"material": "yarn_001", "optimal_stock": 800}],
            "cost_savings": {"total": 5000, "percentage": 15},
            "service_improvement": {"from": 0.85, "to": 0.95}
        }
        
        with patch.object(ml_client, '_call_zen_tool', return_value=mock_response):
            result = await ml_client.optimize_inventory_with_ml(
                inventory_data, sample_sales_data, supplier_data
            )
            
            assert isinstance(result["optimized_inventory"], pd.DataFrame)
            assert result["cost_reduction"]["percentage"] == 15
            assert result["service_level_improvement"]["to"] == 0.95
    
    @pytest.mark.asyncio
    async def test_predict_material_prices(self, ml_client):
        """Test material price prediction"""
        historical_prices = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100),
            'price': np.random.uniform(10, 20, 100)
        })
        
        mock_response = {
            "predictions": [{"day": 1, "price": 15.5}, {"day": 2, "price": 15.8}],
            "volatility": {"daily": 0.02, "weekly": 0.05},
            "key_factors": ["commodity_prices", "seasonal_demand"],
            "recommendation": "Consider forward contracts"
        }
        
        with patch.object(ml_client, '_call_zen_tool', return_value=mock_response):
            result = await ml_client.predict_material_prices("cotton", historical_prices, 30)
            
            assert isinstance(result["price_forecast"], pd.DataFrame)
            assert "volatility" in result["volatility_forecast"]
            assert len(result["price_drivers"]) > 0
            assert result["recommendation"] != ""
    
    @pytest.mark.asyncio
    async def test_check_zen_server_status(self, ml_client):
        """Test checking zen server status"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "status": "healthy",
            "version": "1.0.0",
            "ml_models_loaded": 5
        })
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await ml_client.check_zen_server_status()
            
            assert result["status"] == "healthy"
            assert result["version"] == "1.0.0"
            assert result["ml_models_loaded"] == 5
    
    @pytest.mark.asyncio
    async def test_connection_retry_logic(self, ml_client):
        """Test connection retry logic"""
        ml_client.connection_retries = 3
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise aiohttp.ClientError("Connection failed")
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"result": "success"})
            return mock_response
        
        with patch('aiohttp.ClientSession.post', side_effect=mock_post):
            result = await ml_client._call_zen_tool("test", {})
            
            assert call_count == 3
            assert result["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_cleanup(self, ml_client):
        """Test resource cleanup"""
        # Create a mock session
        ml_client.session = AsyncMock()
        ml_client.session.closed = False
        
        await ml_client.close()
        
        ml_client.session.close.assert_called_once()
    
    def test_temp_file_cleanup(self, ml_client, sample_sales_data):
        """Test that temporary files are cleaned up"""
        # This test verifies the cleanup in finally blocks
        # We'll use a mock to ensure unlink is called
        with patch('pathlib.Path.unlink') as mock_unlink:
            with patch.object(ml_client, '_call_zen_tool', side_effect=Exception("Test error")):
                try:
                    asyncio.run(ml_client.train_demand_forecasting_model(sample_sales_data))
                except:
                    pass
                
                # Verify unlink was called (cleanup happened)
                mock_unlink.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])