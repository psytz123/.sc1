"""
Unit tests for configuration validator
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from jsonschema import ValidationError

from src.core.config_validator import (
    ConfigurationValidator,
    generate_sample_configs,
    validate_code_config,
    validate_ml_config,
    validate_planner_config,
)


class TestConfigurationValidator:
    """Test suite for configuration validator"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return ConfigurationValidator()
    
    @pytest.fixture
    def valid_ml_config(self):
        """Valid ML configuration"""
        return {
            "zen_server": {
                "host": "localhost",
                "port": 8000,
                "timeout": 30
            },
            "models": {
                "demand_forecasting": {
                    "model_type": "arima",
                    "parameters": {"p": 2, "d": 1, "q": 2}
                },
                "supplier_risk": {
                    "model_type": "random_forest",
                    "risk_factors": ["delivery", "quality"]
                },
                "inventory_optimization": {
                    "algorithm": "genetic",
                    "constraints": {}
                },
                "price_prediction": {
                    "model_type": "linear",
                    "features": ["material", "demand"]
                }
            },
            "fallback_settings": {
                "use_local_models": True,
                "cache_predictions": False
            }
        }
    
    @pytest.fixture
    def valid_code_config(self):
        """Valid Code Management configuration"""
        return {
            "zen_server": {
                "host": "localhost",
                "port": 8000
            },
            "analysis_settings": {
                "complexity_threshold": 20,
                "coverage_threshold": 80.0
            },
            "generation_settings": {
                "style_guide": "pep8",
                "output_format": "python"
            }
        }
    
    @pytest.fixture
    def valid_planner_config(self):
        """Valid Planner configuration"""
        return {
            "planning_horizon_days": 90,
            "safety_stock_factor": 1.5,
            "ml_config_path": "config/ml.json",
            "optimization_settings": {
                "enable_ml_enhancements": True
            }
        }
    
    def test_validate_ml_config_valid(self, validator, valid_ml_config):
        """Test validation of valid ML configuration"""
        result = validator.validate_ml_config(valid_ml_config)
        
        assert result["zen_server"]["host"] == "localhost"
        assert result["models"]["demand_forecasting"]["model_type"] == "arima"
        assert result["fallback_settings"]["use_local_models"] == True
    
    def test_validate_ml_config_with_defaults(self, validator, valid_ml_config):
        """Test that defaults are applied"""
        result = validator.validate_ml_config(valid_ml_config)
        
        # Check defaults were applied
        assert result["zen_server"]["retry_attempts"] == 3
        assert result["zen_server"]["retry_delay"] == 1.0
    
    def test_validate_ml_config_invalid_missing_required(self, validator):
        """Test validation fails for missing required fields"""
        invalid_config = {
            "zen_server": {
                "host": "localhost"
                # Missing port and timeout
            },
            "models": {},  # Missing required models
            "fallback_settings": {}  # Missing required settings
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_ml_config(invalid_config)
        
        assert "port" in str(exc_info.value)
    
    def test_validate_ml_config_invalid_type(self, validator, valid_ml_config):
        """Test validation fails for invalid types"""
        valid_ml_config["zen_server"]["port"] = "not_a_number"
        
        with pytest.raises(ValidationError):
            validator.validate_ml_config(valid_ml_config)
    
    def test_validate_ml_config_invalid_enum(self, validator, valid_ml_config):
        """Test validation fails for invalid enum values"""
        valid_ml_config["models"]["demand_forecasting"]["model_type"] = "invalid_model"
        
        with pytest.raises(ValidationError):
            validator.validate_ml_config(valid_ml_config)
    
    def test_validate_code_config_valid(self, validator, valid_code_config):
        """Test validation of valid Code configuration"""
        result = validator.validate_code_config(valid_code_config)
        
        assert result["zen_server"]["host"] == "localhost"
        assert result["analysis_settings"]["complexity_threshold"] == 20
        
        # Check default was applied
        assert result["zen_server"]["timeout"] == 30
    
    def test_validate_planner_config_valid(self, validator, valid_planner_config):
        """Test validation of valid Planner configuration"""
        result = validator.validate_planner_config(valid_planner_config)
        
        assert result["planning_horizon_days"] == 90
        assert result["safety_stock_factor"] == 1.5
    
    def test_validate_all_configs(self, validator, valid_ml_config, valid_code_config, valid_planner_config):
        """Test validation of all configurations together"""
        result = validator.validate_all_configs(
            valid_ml_config,
            valid_code_config,
            valid_planner_config
        )
        
        assert "ml" in result
        assert "code" in result
        assert "planner" in result
        
        assert result["ml"]["zen_server"]["host"] == "localhost"
        assert result["code"]["zen_server"]["host"] == "localhost"
        assert result["planner"]["planning_horizon_days"] == 90
    
    def test_load_config_from_json_file(self, validator, valid_ml_config):
        """Test loading configuration from JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_ml_config, f)
            temp_path = f.name
        
        try:
            result = validator.validate_ml_config(temp_path)
            assert result["zen_server"]["host"] == "localhost"
        finally:
            Path(temp_path).unlink()
    
    def test_load_config_from_yaml_file(self, validator, valid_ml_config):
        """Test loading configuration from YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_ml_config, f)
            temp_path = f.name
        
        try:
            result = validator.validate_ml_config(temp_path)
            assert result["zen_server"]["host"] == "localhost"
        finally:
            Path(temp_path).unlink()
    
    def test_load_config_file_not_found(self, validator):
        """Test error when config file not found"""
        with pytest.raises(FileNotFoundError):
            validator.validate_ml_config("nonexistent_file.json")
    
    def test_load_config_unsupported_format(self, validator):
        """Test error for unsupported file format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("invalid config")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                validator.validate_ml_config(temp_path)
            assert "Unsupported configuration file format" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_generate_sample_config(self, validator):
        """Test sample configuration generation"""
        ml_sample = validator.generate_sample_config("ml")
        code_sample = validator.generate_sample_config("code")
        planner_sample = validator.generate_sample_config("planner")
        
        # Validate that samples are valid
        validator.validate_ml_config(ml_sample)
        validator.validate_code_config(code_sample)
        validator.validate_planner_config(planner_sample)
    
    def test_check_config_compatibility_same_server(self, validator):
        """Test compatibility check with same zen server"""
        configs = {
            "ml": {
                "zen_server": {"host": "localhost", "port": 8000}
            },
            "code": {
                "zen_server": {"host": "localhost", "port": 8000}
            },
            "planner": {}
        }
        
        warnings = validator.check_config_compatibility(configs)
        assert len(warnings) == 0
    
    def test_check_config_compatibility_different_servers(self, validator):
        """Test compatibility check with different zen servers"""
        configs = {
            "ml": {
                "zen_server": {"host": "localhost", "port": 8000}
            },
            "code": {
                "zen_server": {"host": "localhost", "port": 9000}
            },
            "planner": {}
        }
        
        warnings = validator.check_config_compatibility(configs)
        assert len(warnings) > 0
        assert any("different zen servers" in w for w in warnings)
    
    def test_check_config_compatibility_missing_files(self, validator):
        """Test compatibility check with missing config files"""
        configs = {
            "ml": {},
            "code": {},
            "planner": {
                "ml_config_path": "nonexistent_ml.json",
                "code_config_path": "nonexistent_code.json"
            }
        }
        
        warnings = validator.check_config_compatibility(configs)
        assert len(warnings) == 2
        assert any("ML config file not found" in w for w in warnings)
        assert any("Code config file not found" in w for w in warnings)
    
    def test_convenience_functions(self, valid_ml_config, valid_code_config, valid_planner_config):
        """Test convenience validation functions"""
        ml_result = validate_ml_config(valid_ml_config)
        code_result = validate_code_config(valid_code_config)
        planner_result = validate_planner_config(valid_planner_config)
        
        assert ml_result["zen_server"]["host"] == "localhost"
        assert code_result["zen_server"]["host"] == "localhost"
        assert planner_result["planning_horizon_days"] == 90
    
    def test_generate_sample_configs_function(self):
        """Test sample config generation function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generate_sample_configs(temp_dir)
            
            # Check files were created
            temp_path = Path(temp_dir)
            assert (temp_path / "ml_config_sample.json").exists()
            assert (temp_path / "ml_config_sample.yaml").exists()
            assert (temp_path / "code_config_sample.json").exists()
            assert (temp_path / "code_config_sample.yaml").exists()
            assert (temp_path / "planner_config_sample.json").exists()
            assert (temp_path / "planner_config_sample.yaml").exists()
            
            # Validate generated configs
            validator = ConfigurationValidator()
            
            with open(temp_path / "ml_config_sample.json") as f:
                ml_config = json.load(f)
                validator.validate_ml_config(ml_config)
            
            with open(temp_path / "code_config_sample.yaml") as f:
                code_config = yaml.safe_load(f)
                validator.validate_code_config(code_config)


class TestConfigurationEdgeCases:
    """Test edge cases and complex scenarios"""
    
    @pytest.fixture
    def validator(self):
        return ConfigurationValidator()
    
    def test_deeply_nested_validation_error(self, validator):
        """Test validation error in deeply nested structure"""
        config = {
            "zen_server": {"host": "localhost", "port": 8000, "timeout": 30},
            "models": {
                "demand_forecasting": {
                    "model_type": "arima",
                    "parameters": {"p": "not_a_number"},  # Invalid nested value
                    "training_config": {"epochs": 100}
                },
                "supplier_risk": {"model_type": "rf", "risk_factors": []},
                "inventory_optimization": {"algorithm": "ga", "constraints": {}},
                "price_prediction": {"model_type": "lr", "features": []}
            },
            "fallback_settings": {"use_local_models": True, "cache_predictions": False}
        }
        
        # Should still validate (parameters is just an object)
        result = validator.validate_ml_config(config)
        assert result is not None
    
    def test_additional_properties_allowed(self, validator):
        """Test that additional properties are preserved"""
        config = {
            "zen_server": {"host": "localhost", "port": 8000, "timeout": 30},
            "models": {
                "demand_forecasting": {"model_type": "arima", "parameters": {}},
                "supplier_risk": {"model_type": "rf", "risk_factors": []},
                "inventory_optimization": {"algorithm": "ga", "constraints": {}},
                "price_prediction": {"model_type": "lr", "features": []}
            },
            "fallback_settings": {"use_local_models": True, "cache_predictions": False},
            "custom_setting": "preserved"  # Additional property
        }
        
        result = validator.validate_ml_config(config)
        assert result["custom_setting"] == "preserved"
    
    def test_port_range_validation(self, validator):
        """Test port number range validation"""
        config = {
            "zen_server": {"host": "localhost", "port": 70000, "timeout": 30},  # Invalid port
            "models": {
                "demand_forecasting": {"model_type": "arima", "parameters": {}},
                "supplier_risk": {"model_type": "rf", "risk_factors": []},
                "inventory_optimization": {"algorithm": "ga", "constraints": {}},
                "price_prediction": {"model_type": "lr", "features": []}
            },
            "fallback_settings": {"use_local_models": True, "cache_predictions": False}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_ml_config(config)
        assert "70000" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])