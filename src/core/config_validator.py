"""
Configuration validation for Beverly Knits core clients

This module provides validation for configuration files used by the ML and Code Management clients.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml
from jsonschema import Draft7Validator, ValidationError

logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Validates configuration files for Beverly Knits clients"""
    
    # ML Configuration Schema
    ML_CONFIG_SCHEMA = {
        "type": "object",
        "required": ["zen_server", "models", "fallback_settings"],
        "properties": {
            "zen_server": {
                "type": "object",
                "required": ["host", "port", "timeout"],
                "properties": {
                    "host": {"type": "string", "format": "hostname"},
                    "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                    "timeout": {"type": "integer", "minimum": 1},
                    "retry_attempts": {"type": "integer", "minimum": 0, "default": 3},
                    "retry_delay": {"type": "number", "minimum": 0, "default": 1.0}
                }
            },
            "models": {
                "type": "object",
                "required": ["demand_forecasting", "supplier_risk", "inventory_optimization", "price_prediction"],
                "properties": {
                    "demand_forecasting": {
                        "type": "object",
                        "required": ["model_type", "parameters"],
                        "properties": {
                            "model_type": {"type": "string", "enum": ["arima", "lstm", "prophet", "ensemble"]},
                            "parameters": {"type": "object"},
                            "training_config": {"type": "object"}
                        }
                    },
                    "supplier_risk": {
                        "type": "object",
                        "required": ["model_type", "risk_factors"],
                        "properties": {
                            "model_type": {"type": "string"},
                            "risk_factors": {"type": "array", "items": {"type": "string"}},
                            "threshold": {"type": "number", "minimum": 0, "maximum": 1}
                        }
                    },
                    "inventory_optimization": {
                        "type": "object",
                        "required": ["algorithm", "constraints"],
                        "properties": {
                            "algorithm": {"type": "string"},
                            "constraints": {"type": "object"}
                        }
                    },
                    "price_prediction": {
                        "type": "object",
                        "required": ["model_type", "features"],
                        "properties": {
                            "model_type": {"type": "string"},
                            "features": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            },
            "fallback_settings": {
                "type": "object",
                "required": ["use_local_models", "cache_predictions"],
                "properties": {
                    "use_local_models": {"type": "boolean"},
                    "cache_predictions": {"type": "boolean"},
                    "cache_ttl": {"type": "integer", "minimum": 0}
                }
            },
            "logging": {
                "type": "object",
                "properties": {
                    "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                    "format": {"type": "string"}
                }
            }
        }
    }
    
    # Code Management Configuration Schema
    CODE_CONFIG_SCHEMA = {
        "type": "object",
        "required": ["zen_server", "analysis_settings", "generation_settings"],
        "properties": {
            "zen_server": {
                "type": "object",
                "required": ["host", "port"],
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                    "timeout": {"type": "integer", "minimum": 1, "default": 30}
                }
            },
            "analysis_settings": {
                "type": "object",
                "properties": {
                    "complexity_threshold": {"type": "integer", "minimum": 1},
                    "coverage_threshold": {"type": "number", "minimum": 0, "maximum": 100},
                    "lint_rules": {"type": "array", "items": {"type": "string"}},
                    "ignore_patterns": {"type": "array", "items": {"type": "string"}}
                }
            },
            "generation_settings": {
                "type": "object",
                "properties": {
                    "style_guide": {"type": "string"},
                    "templates_path": {"type": "string"},
                    "output_format": {"type": "string", "enum": ["python", "typescript", "javascript"]},
                    "include_tests": {"type": "boolean", "default": True}
                }
            },
            "textile_patterns": {
                "type": "object",
                "properties": {
                    "material_types": {"type": "array", "items": {"type": "string"}},
                    "quality_metrics": {"type": "array", "items": {"type": "string"}},
                    "supplier_attributes": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
    
    # Planner Configuration Schema
    PLANNER_CONFIG_SCHEMA = {
        "type": "object",
        "required": ["planning_horizon_days", "safety_stock_factor"],
        "properties": {
            "planning_horizon_days": {"type": "integer", "minimum": 1},
            "safety_stock_factor": {"type": "number", "minimum": 1.0},
            "ml_config_path": {"type": "string"},
            "code_config_path": {"type": "string"},
            "optimization_settings": {
                "type": "object",
                "properties": {
                    "enable_ml_enhancements": {"type": "boolean", "default": True},
                    "enable_code_optimization": {"type": "boolean", "default": True},
                    "cache_analysis_results": {"type": "boolean", "default": True}
                }
            },
            "supplier_settings": {
                "type": "object",
                "properties": {
                    "min_reliability_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "preferred_suppliers": {"type": "array", "items": {"type": "string"}},
                    "blacklisted_suppliers": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
    
    def __init__(self):
        """Initialize the configuration validator"""
        self.validators = {
            "ml": Draft7Validator(self.ML_CONFIG_SCHEMA),
            "code": Draft7Validator(self.CODE_CONFIG_SCHEMA),
            "planner": Draft7Validator(self.PLANNER_CONFIG_SCHEMA)
        }
    
    def validate_ml_config(self, config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        """
        Validate ML configuration.
        
        Args:
            config: Configuration dict, file path, or Path object
            
        Returns:
            Validated configuration dict
            
        Raises:
            ValidationError: If configuration is invalid
        """
        config_dict = self._load_config(config)
        self._validate_config(config_dict, "ml")
        return self._apply_defaults(config_dict, self.ML_CONFIG_SCHEMA)
    
    def validate_code_config(self, config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        """
        Validate Code Management configuration.
        
        Args:
            config: Configuration dict, file path, or Path object
            
        Returns:
            Validated configuration dict
            
        Raises:
            ValidationError: If configuration is invalid
        """
        config_dict = self._load_config(config)
        self._validate_config(config_dict, "code")
        return self._apply_defaults(config_dict, self.CODE_CONFIG_SCHEMA)
    
    def validate_planner_config(self, config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        """
        Validate Planner configuration.
        
        Args:
            config: Configuration dict, file path, or Path object
            
        Returns:
            Validated configuration dict
            
        Raises:
            ValidationError: If configuration is invalid
        """
        config_dict = self._load_config(config)
        self._validate_config(config_dict, "planner")
        return self._apply_defaults(config_dict, self.PLANNER_CONFIG_SCHEMA)
    
    def validate_all_configs(self, ml_config: Any, code_config: Any, planner_config: Any) -> Dict[str, Dict[str, Any]]:
        """
        Validate all configurations together.
        
        Args:
            ml_config: ML configuration
            code_config: Code management configuration
            planner_config: Planner configuration
            
        Returns:
            Dict with all validated configurations
        """
        return {
            "ml": self.validate_ml_config(ml_config),
            "code": self.validate_code_config(code_config),
            "planner": self.validate_planner_config(planner_config)
        }
    
    def _load_config(self, config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        """Load configuration from various sources"""
        if isinstance(config, dict):
            return config
        
        config_path = Path(config)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif config_path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
    
    def _validate_config(self, config: Dict[str, Any], config_type: str):
        """Validate configuration against schema"""
        validator = self.validators.get(config_type)
        if not validator:
            raise ValueError(f"Unknown configuration type: {config_type}")
        
        errors = list(validator.iter_errors(config))
        if errors:
            error_messages = []
            for error in errors:
                path = " -> ".join(str(p) for p in error.path)
                error_messages.append(f"{path}: {error.message}")
            
            raise ValidationError(f"Configuration validation failed:\n" + "\n".join(error_messages))
    
    def _apply_defaults(self, config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values from schema"""
        def apply_defaults_recursive(obj: Dict[str, Any], schema_part: Dict[str, Any]):
            if schema_part.get("type") == "object" and "properties" in schema_part:
                for prop, prop_schema in schema_part["properties"].items():
                    if prop not in obj and "default" in prop_schema:
                        obj[prop] = prop_schema["default"]
                    elif prop in obj and isinstance(obj[prop], dict):
                        apply_defaults_recursive(obj[prop], prop_schema)
        
        result = config.copy()
        apply_defaults_recursive(result, schema)
        return result
    
    def generate_sample_config(self, config_type: str) -> Dict[str, Any]:
        """Generate a sample configuration for the specified type"""
        samples = {
            "ml": {
                "zen_server": {
                    "host": "localhost",
                    "port": 8000,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "retry_delay": 1.0
                },
                "models": {
                    "demand_forecasting": {
                        "model_type": "arima",
                        "parameters": {
                            "p": 2,
                            "d": 1,
                            "q": 2
                        },
                        "training_config": {
                            "epochs": 100,
                            "batch_size": 32
                        }
                    },
                    "supplier_risk": {
                        "model_type": "random_forest",
                        "risk_factors": ["delivery_history", "quality_score", "financial_stability"],
                        "threshold": 0.7
                    },
                    "inventory_optimization": {
                        "algorithm": "genetic_algorithm",
                        "constraints": {
                            "max_storage": 10000,
                            "min_order_size": 100
                        }
                    },
                    "price_prediction": {
                        "model_type": "linear_regression",
                        "features": ["material_type", "market_demand", "season", "supplier"]
                    }
                },
                "fallback_settings": {
                    "use_local_models": True,
                    "cache_predictions": True,
                    "cache_ttl": 3600
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "code": {
                "zen_server": {
                    "host": "localhost",
                    "port": 8000,
                    "timeout": 30
                },
                "analysis_settings": {
                    "complexity_threshold": 20,
                    "coverage_threshold": 80.0,
                    "lint_rules": ["E", "W", "F"],
                    "ignore_patterns": ["*_test.py", "*.pyc", "__pycache__"]
                },
                "generation_settings": {
                    "style_guide": "pep8",
                    "templates_path": "templates/",
                    "output_format": "python",
                    "include_tests": True
                },
                "textile_patterns": {
                    "material_types": ["cotton", "polyester", "wool", "silk", "linen"],
                    "quality_metrics": ["tensile_strength", "color_fastness", "shrinkage"],
                    "supplier_attributes": ["lead_time", "minimum_order", "certifications"]
                }
            },
            "planner": {
                "planning_horizon_days": 90,
                "safety_stock_factor": 1.5,
                "ml_config_path": "config/ml_config.json",
                "code_config_path": "config/code_config.json",
                "optimization_settings": {
                    "enable_ml_enhancements": True,
                    "enable_code_optimization": True,
                    "cache_analysis_results": True
                },
                "supplier_settings": {
                    "min_reliability_score": 0.8,
                    "preferred_suppliers": ["supplier_a", "supplier_b"],
                    "blacklisted_suppliers": []
                }
            }
        }
        
        return samples.get(config_type, {})
    
    def check_config_compatibility(self, configs: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Check compatibility between different configurations.
        
        Args:
            configs: Dict with 'ml', 'code', and 'planner' configurations
            
        Returns:
            List of compatibility warnings
        """
        warnings = []
        
        # Check if ML and Code configs point to same zen server
        ml_server = configs.get("ml", {}).get("zen_server", {})
        code_server = configs.get("code", {}).get("zen_server", {})
        
        if ml_server and code_server:
            if (ml_server.get("host") != code_server.get("host") or 
                ml_server.get("port") != code_server.get("port")):
                warnings.append("ML and Code configurations use different zen servers")
        
        # Check if planner config references valid config files
        planner = configs.get("planner", {})
        if planner.get("ml_config_path") and not Path(planner["ml_config_path"]).exists():
            warnings.append(f"ML config file not found: {planner['ml_config_path']}")
        
        if planner.get("code_config_path") and not Path(planner["code_config_path"]).exists():
            warnings.append(f"Code config file not found: {planner['code_config_path']}")
        
        return warnings


# Convenience functions
def validate_ml_config(config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
    """Validate ML configuration"""
    validator = ConfigurationValidator()
    return validator.validate_ml_config(config)


def validate_code_config(config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
    """Validate Code Management configuration"""
    validator = ConfigurationValidator()
    return validator.validate_code_config(config)


def validate_planner_config(config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
    """Validate Planner configuration"""
    validator = ConfigurationValidator()
    return validator.validate_planner_config(config)


def generate_sample_configs(output_dir: Union[str, Path] = "config/samples"):
    """Generate sample configuration files"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    validator = ConfigurationValidator()
    
    for config_type in ["ml", "code", "planner"]:
        sample = validator.generate_sample_config(config_type)
        
        # Save as JSON
        json_path = output_path / f"{config_type}_config_sample.json"
        with open(json_path, 'w') as f:
            json.dump(sample, f, indent=2)
        
        # Save as YAML
        yaml_path = output_path / f"{config_type}_config_sample.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(sample, f, default_flow_style=False)
        
        logger.info(f"Generated sample {config_type} configs: {json_path}, {yaml_path}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        generate_sample_configs()
        print("Sample configuration files generated in config/samples/")
    else:
        # Validate example configurations
        validator = ConfigurationValidator()
        
        # Generate and validate sample configs
        ml_config = validator.generate_sample_config("ml")
        code_config = validator.generate_sample_config("code")
        planner_config = validator.generate_sample_config("planner")
        
        try:
            validated = validator.validate_all_configs(ml_config, code_config, planner_config)
            print("✅ All configurations are valid!")
            
            # Check compatibility
            warnings = validator.check_config_compatibility(validated)
            if warnings:
                print("\n⚠️  Compatibility warnings:")
                for warning in warnings:
                    print(f"  - {warning}")
        except ValidationError as e:
            print(f"❌ Configuration validation failed: {e}")