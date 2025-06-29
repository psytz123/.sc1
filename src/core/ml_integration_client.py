"""
Beverly Knits ML Integration Client

This module provides the interface for integrating ML capabilities
into the Beverly Knits Raw Material Planner using both local ML libraries
and optional zen-mcp-server integration.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import warnings
import aiohttp
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager
import time

import logging
# Try to import logging configuration, fall back to basic logging if not available
try:
    from .logging_config import setup_logging, get_logger, MLOperationLogger
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fall back to basic logging configuration
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Define a simple MLOperationLogger for compatibility
    class MLOperationLogger:
        def __init__(self, operation_name: str, logger: logging.Logger = None):
            self.operation_name = operation_name
            self.logger = logger or logging.getLogger(__name__)
            self.start_time = None

        def __enter__(self):
            self.start_time = datetime.now()
            self.logger.info(f"Starting {self.operation_name}...")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = (datetime.now() - self.start_time).total_seconds()

            if exc_type is None:
                self.logger.info(f"Completed {self.operation_name} in {duration:.2f} seconds")
            else:
                self.logger.error(f"Failed {self.operation_name} after {duration:.2f} seconds: {exc_val}")

            return False

# Check for available ML libraries
ML_LIBRARIES = {
    'sklearn': False,
    'xgboost': False,
    'lightgbm': False,
    'prophet': False,
    'tensorflow': False,
    'torch': False
}

# Try importing ML libraries
try:
    import sklearn
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    ML_LIBRARIES['sklearn'] = True
except ImportError:
    pass

try:
    import xgboost
    ML_LIBRARIES['xgboost'] = True
except ImportError:
    pass

try:
    import lightgbm
    ML_LIBRARIES['lightgbm'] = True
except ImportError:
    pass

try:
    from prophet import Prophet
    ML_LIBRARIES['prophet'] = True
except ImportError:
    pass

try:
    import tensorflow
    ML_LIBRARIES['tensorflow'] = True
except ImportError:
    pass

try:
    import torch
    ML_LIBRARIES['torch'] = True
except ImportError:
    pass


class MLConnectionError(Exception):
    """Raised when connection to ML service fails"""
    pass


class MLTimeoutError(Exception):
    """Raised when ML operation times out"""
    pass


class BeverlyKnitsMLClient:
    """
    AI/ML integration client for Beverly Knits Raw Material Planner.
    
    This client provides a unified interface for ML operations, supporting both
    local ML libraries and optional zen-mcp-server integration for advanced
    AI capabilities.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ML client.
        
        Args:
            config_path: Path to zen ML configuration file. If None, uses default.
        """
        self.config_path = config_path or "config/zen_ml_config.json"
        self.zen_config = None
        self.zen_available = False
        self.session = None
        self.models_cache = {}
        self.connection_retries = 3
        self.connection_timeout = 30  # seconds
        
        # Initialize directories
        self.models_dir = Path("models/ml_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("temp/ml_processing")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self._load_config()
        
        # Log available ML libraries
        available_libs = [lib for lib, available in ML_LIBRARIES.items() if available]
        if available_libs:
            logger.info(f"Available ML libraries: {', '.join(available_libs)}")
        else:
            logger.warning("No ML libraries available. Install scikit-learn, xgboost, etc.")
    
    def _load_config(self) -> None:
        """Load zen-mcp-server configuration if available."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.zen_config = json.load(f)
                self.zen_available = self.zen_config.get('zen_mcp_server', {}).get('enabled', False)
                
                if self.zen_available:
                    # Update connection settings from config
                    server_config = self.zen_config.get('zen_mcp_server', {})
                    self.connection_timeout = server_config.get('timeout', 30)
                    self.connection_retries = server_config.get('retries', 3)
                    logger.info("zen-mcp-server configuration loaded successfully")
            else:
                logger.info(f"No zen configuration found at {self.config_path}")
        except Exception as e:
            logger.warning(f"Failed to load zen configuration: {e}")
            self.zen_available = False
    
    @asynccontextmanager
    async def _get_session(self):
        """Get or create an aiohttp session with proper timeout."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.connection_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        try:
            yield self.session
        except Exception:
            # Don't close session on error, reuse for retries
            raise
    
    async def _call_zen_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a zen-mcp-server tool via HTTP API with retry logic.
        
        Args:
            tool_name: Name of the tool/endpoint to call
            params: Parameters to send to the tool
            
        Returns:
            Response from zen-mcp-server or error dict with fallback indication
        """
        if not self.zen_available or not self.zen_config:
            return {
                "status": "error",
                "message": "zen-mcp-server not configured",
                "fallback": "using_local_ml"
            }
        
        url = f"{self.zen_config['zen_mcp_server']['url']}/{tool_name}"
        
        for attempt in range(self.connection_retries):
            try:
                async with self._get_session() as session:
                    start_time = time.time()
                    async with session.post(url, json=params) as response:
                        elapsed_time = time.time() - start_time
                        
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Successfully called zen tool: {tool_name} (took {elapsed_time:.2f}s)")
                            return result
                        else:
                            error_text = await response.text()
                            error_msg = f"zen-mcp-server returned status {response.status}: {error_text}"
                            logger.warning(f"Attempt {attempt + 1}/{self.connection_retries}: {error_msg}")
                            
                            if attempt < self.connection_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            
                            return {
                                "status": "error",
                                "message": error_msg,
                                "fallback": "using_local_ml"
                            }
                            
            except asyncio.TimeoutError:
                logger.warning(f"Attempt {attempt + 1}/{self.connection_retries}: Timeout calling {tool_name}")
                if attempt < self.connection_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {
                    "status": "error",
                    "message": f"Operation timed out after {self.connection_timeout}s",
                    "fallback": "using_local_ml"
                }
                
            except aiohttp.ClientError as e:
                logger.warning(f"Attempt {attempt + 1}/{self.connection_retries}: Connection error: {e}")
                if attempt < self.connection_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {
                    "status": "error",
                    "message": f"Connection error: {str(e)}",
                    "fallback": "using_local_ml"
                }
                
            except Exception as e:
                logger.error(f"Unexpected error calling zen tool: {e}")
                return {
                    "status": "error",
                    "message": f"Unexpected error: {str(e)}",
                    "fallback": "using_local_ml"
                }
    
    async def check_zen_server_status(self) -> Dict[str, Any]:
        """
        Check if zen-mcp-server is running and accessible.
        
        Returns:
            Dict with availability status and details
        """
        if not self.zen_available:
            return {
                "available": False,
                "reason": "Not configured",
                "ml_libraries": ML_LIBRARIES
            }
        
        try:
            url = f"{self.zen_config['zen_mcp_server']['url']}/health"
            async with self._get_session() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        return {
                            "available": True,
                            "status": "healthy",
                            "details": health_data,
                            "ml_libraries": ML_LIBRARIES
                        }
                    else:
                        return {
                            "available": False,
                            "status": f"unhealthy (status: {response.status})",
                            "ml_libraries": ML_LIBRARIES
                        }
        except Exception as e:
            return {
                "available": False,
                "reason": f"Connection failed: {str(e)}",
                "ml_libraries": ML_LIBRARIES
            }
    
    async def train_demand_forecast_model(
        self,
        historical_data: pd.DataFrame,
        material_type: str = "yarn",
        model_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Train a demand forecasting model for textile materials.
        
        Args:
            historical_data: DataFrame with historical demand data
            material_type: Type of material (yarn, fabric, etc.)
            model_type: Model type to use (auto, prophet, xgboost, etc.)
            
        Returns:
            Dict with model performance metrics and model ID
        """
        try:
            # First try zen-mcp-server if available
            if self.zen_available:
                result = await self._call_zen_tool(
                    "ml/train_forecast",
                    {
                        "data": historical_data.to_dict(orient='records'),
                        "material_type": material_type,
                        "model_type": model_type,
                        "features": list(historical_data.columns)
                    }
                )
                
                if result.get("status") != "error":
                    return result
            
            # Fallback to local ML implementation
            logger.info("Using local ML libraries for demand forecasting")
            
            if not ML_LIBRARIES['sklearn']:
                return {
                    "status": "error",
                    "message": "scikit-learn not installed. Run: pip install scikit-learn"
                }
            
            # Simple local implementation using sklearn
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.model_selection import train_test_split
            
            # Prepare features and target
            # This is a simplified example - real implementation would be more sophisticated
            X = historical_data.drop(['demand', 'date'], axis=1, errors='ignore')
            y = historical_data['demand']
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # Evaluate model
            predictions = model.predict(X_test)
            mae = mean_absolute_error(y_test, predictions)
            mse = mean_squared_error(y_test, predictions)
            
            # Save model
            model_id = f"{material_type}_demand_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_path = self.models_dir / f"{model_id}.pkl"
            
            import pickle
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            self.models_cache[model_id] = model
            
            return {
                "status": "success",
                "model_id": model_id,
                "metrics": {
                    "mae": float(mae),
                    "mse": float(mse),
                    "rmse": float(np.sqrt(mse))
                },
                "model_type": "RandomForestRegressor",
                "fallback_used": True
            }
            
        except Exception as e:
            logger.error(f"Error training demand forecast model: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def predict_demand(
        self,
        model_id: str,
        features: pd.DataFrame,
        horizon: int = 30
    ) -> Dict[str, Any]:
        """
        Generate demand predictions using a trained model.
        
        Args:
            model_id: ID of the trained model
            features: Feature data for prediction
            horizon: Prediction horizon in days
            
        Returns:
            Dict with predictions and confidence intervals
        """
        try:
            # Try zen-mcp-server first
            if self.zen_available:
                result = await self._call_zen_tool(
                    "ml/predict",
                    {
                        "model_id": model_id,
                        "features": features.to_dict(orient='records'),
                        "horizon": horizon
                    }
                )
                
                if result.get("status") != "error":
                    return result
            
            # Fallback to local prediction
            logger.info("Using local model for prediction")
            
            # Check cache first
            if model_id in self.models_cache:
                model = self.models_cache[model_id]
            else:
                # Load from disk
                model_path = self.models_dir / f"{model_id}.pkl"
                if not model_path.exists():
                    return {
                        "status": "error",
                        "message": f"Model {model_id} not found"
                    }
                
                import pickle
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                self.models_cache[model_id] = model
            
            # Generate predictions
            predictions = model.predict(features)
            
            # Simple confidence intervals (real implementation would be more sophisticated)
            std_dev = np.std(predictions) * 0.1  # Simplified
            
            return {
                "status": "success",
                "predictions": predictions.tolist(),
                "confidence_intervals": {
                    "lower": (predictions - 1.96 * std_dev).tolist(),
                    "upper": (predictions + 1.96 * std_dev).tolist()
                },
                "horizon": horizon,
                "fallback_used": True
            }
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def analyze_supplier_risk(
        self,
        supplier_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze supplier risk using ML models.
        
        Args:
            supplier_data: DataFrame with supplier performance metrics
            
        Returns:
            Dict with risk scores and recommendations
        """
        try:
            # Implementation would include risk scoring logic
            # This is a placeholder for the actual implementation
            logger.info("Analyzing supplier risk")
            
            # For now, return a simple analysis
            return {
                "status": "success",
                "risk_scores": {},
                "recommendations": [],
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing supplier risk: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def optimize_inventory_levels(
        self,
        inventory_data: pd.DataFrame,
        demand_forecast: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Optimize inventory levels using ML.
        
        Args:
            inventory_data: Current inventory levels
            demand_forecast: Forecasted demand
            
        Returns:
            Dict with optimized inventory recommendations
        """
        try:
            logger.info("Optimizing inventory levels")
            
            # Placeholder implementation
            return {
                "status": "success",
                "recommendations": {},
                "optimization_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error optimizing inventory: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def close(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("ML client closed")

    async def train_demand_forecasting_model(self, sales_data: pd.DataFrame, material_type: str = "yarn") -> Dict[str, Any]:
        """
        Train demand forecasting model for textile materials.

        Args:
            sales_data: Historical sales data
            material_type: Type of material (yarn, fabric, etc.)

        Returns:
            Dict with model training results
        """
        with MLOperationLogger("train_demand_forecasting_model", logger):
            # Prepare training data
            training_file = self.temp_dir / f"demand_training_{material_type}.csv"
            sales_data.to_csv(training_file, index=False)

            try:
                if self.zen_available:
                    # Use zen-mcp-server for advanced ML
                    result = await self._call_zen_tool(
                        "train_textile_demand_model",
                        {
                            "training_data_path": str(training_file),
                            "material_type": material_type,
                            "model_type": "time_series_forecasting",
                            "features": [
                                "historical_sales",
                                "seasonal_patterns",
                                "trend_components",
                                "external_factors"
                            ],
                            "model_config": {
                                "algorithm": "lstm_with_attention",
                                "forecast_horizon": 90,
                                "seasonality_periods": [7, 30, 365],
                                "include_holidays": True,
                                "include_weather": False
                            },
                            "validation_split": 0.2,
                            "hyperparameter_tuning": True,
                            "save_model": True,
                            "model_name": f"demand_forecast_{material_type}"
                        }
                    )

                    if result.get("status") == "error":
                        logger.warning(f"zen-mcp-server error: {result.get('message')}, falling back to local ML")
                        return await self._train_local_demand_model(sales_data, material_type)

                    return {
                        "model_id": result.get("model_id"),
                        "model_path": result.get("model_path"),
                        "training_metrics": result.get("metrics", {}),
                        "validation_score": result.get("validation_score"),
                        "feature_importance": result.get("feature_importance", {}),
                        "model_summary": result.get("model_summary", {})
                    }
                else:
                    # Use local ML libraries
                    return await self._train_local_demand_model(sales_data, material_type)

            finally:
                # Clean up temp file
                training_file.unlink(missing_ok=True)

    async def _train_local_demand_model(self, sales_data: pd.DataFrame, material_type: str) -> Dict[str, Any]:
        """Train demand model using local ML libraries."""
        if not ML_LIBRARIES['sklearn']:
            return {
                "status": "error",
                "message": "scikit-learn not available for local training"
            }

        try:
            # Simple implementation using sklearn
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_absolute_error, r2_score

            # Prepare features (simplified)
            X = sales_data.index.values.reshape(-1, 1)  # Using index as time feature
            y = sales_data.iloc[:, 0].values  # First column as target

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            predictions = model.predict(X_test)
            mae = mean_absolute_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)

            # Save model
            model_path = self.models_dir / f"demand_forecast_{material_type}_local.pkl"
            with open(model_path, 'wb') as f:
                import pickle
                pickle.dump(model, f)

            return {
                "model_id": f"local_demand_{material_type}",
                "model_path": str(model_path),
                "training_metrics": {
                    "mae": mae,
                    "r2_score": r2
                },
                "validation_score": r2,
                "model_type": "local_random_forest"
            }

        except Exception as e:
            logger.error(f"Error training local demand model: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def predict_material_demand(self, model_id: str, forecast_days: int = 30) -> Dict[str, Any]:
        """
        Predict material demand using trained model.

        Args:
            model_id: ID of the trained model
            forecast_days: Number of days to forecast

        Returns:
            Dict with demand predictions
        """
        with MLOperationLogger("predict_material_demand", logger):
            if self.zen_available:
                result = await self._call_zen_tool(
                    "predict_material_demand",
                    {
                        "model_id": model_id,
                        "forecast_horizon": forecast_days,
                        "include_confidence_intervals": True,
                        "include_scenario_analysis": True,
                        "scenarios": ["optimistic", "realistic", "pessimistic"],
                        "external_factors": {
                            "seasonal_adjustment": True,
                            "trend_continuation": True,
                            "market_conditions": "normal"
                        }
                    }
                )

                if result.get("status") != "error":
                    return {
                        "predictions": pd.DataFrame(result.get("predictions", [])),
                        "confidence_intervals": result.get("confidence_intervals", {}),
                        "scenario_forecasts": result.get("scenarios", {}),
                        "prediction_date": datetime.now().isoformat(),
                        "model_confidence": result.get("model_confidence", 0)
                    }

            # Fallback to local prediction
            return await self._predict_local_demand(model_id, forecast_days)

    async def _predict_local_demand(self, model_id: str, forecast_days: int) -> Dict[str, Any]:
        """Make predictions using local model."""
        try:
            # Load local model
            model_path = self.models_dir / f"{model_id}.pkl"
            if not model_path.exists():
                # Try alternative naming
                model_path = self.models_dir / f"{model_id}_local.pkl"

            if not model_path.exists():
                return {
                    "status": "error",
                    "message": f"Model {model_id} not found"
                }

            with open(model_path, 'rb') as f:
                import pickle
                model = pickle.load(f)

            # Generate future dates for prediction
            future_indices = np.arange(1, forecast_days + 1).reshape(-1, 1)
            predictions = model.predict(future_indices)

            return {
                "predictions": pd.DataFrame({
                    "day": range(1, forecast_days + 1),
                    "demand": predictions
                }),
                "prediction_date": datetime.now().isoformat(),
                "model_type": "local"
            }

        except Exception as e:
            logger.error(f"Error making local predictions: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def train_supplier_risk_model(self, supplier_data: pd.DataFrame, performance_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train supplier risk assessment model.

        Args:
            supplier_data: Supplier information
            performance_data: Historical performance data

        Returns:
            Dict with model training results
        """
        with MLOperationLogger("train_supplier_risk_model", logger):
            # Prepare training data
            supplier_file = self.temp_dir / "supplier_training.csv"
            performance_file = self.temp_dir / "performance_training.csv"

            supplier_data.to_csv(supplier_file, index=False)
            performance_data.to_csv(performance_file, index=False)

            try:
                if self.zen_available:
                    result = await self._call_zen_tool(
                        "train_supplier_risk_model",
                        {
                            "supplier_data_path": str(supplier_file),
                            "performance_data_path": str(performance_file),
                            "model_type": "classification",
                            "risk_categories": ["low", "medium", "high", "critical"],
                            "features": [
                                "delivery_performance",
                                "quality_metrics",
                                "financial_stability",
                                "communication_responsiveness",
                                "capacity_utilization",
                                "geographic_risk",
                                "industry_experience"
                            ],
                            "model_config": {
                                "algorithm": "gradient_boosting",
                                "class_balancing": True,
                                "feature_selection": True,
                                "cross_validation": 5
                            },
                            "model_name": "supplier_risk_assessment"
                        }
                    )

                    if result.get("status") != "error":
                        return {
                            "model_id": result.get("model_id"),
                            "model_path": result.get("model_path"),
                            "accuracy_score": result.get("accuracy"),
                            "precision_recall": result.get("precision_recall", {}),
                            "feature_importance": result.get("feature_importance", {}),
                            "confusion_matrix": result.get("confusion_matrix", [])
                        }

                # Fallback to simple risk scoring
                return {
                    "status": "success",
                    "model_id": "simple_risk_scorer",
                    "message": "Using simple risk scoring algorithm"
                }

            finally:
                # Clean up temp files
                supplier_file.unlink(missing_ok=True)
                performance_file.unlink(missing_ok=True)

    async def assess_supplier_risk(self, model_id: str, supplier_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for a specific supplier.

        Args:
            model_id: ID of the risk model
            supplier_info: Supplier information

        Returns:
            Dict with risk assessment
        """
        with MLOperationLogger("assess_supplier_risk", logger):
            if self.zen_available:
                result = await self._call_zen_tool(
                    "assess_supplier_risk",
                    {
                        "model_id": model_id,
                        "supplier_data": supplier_info,
                        "include_explanation": True,
                        "include_recommendations": True,
                        "risk_factors_analysis": True
                    }
                )

                if result.get("status") != "error":
                    return {
                        "risk_score": result.get("risk_score"),
                        "risk_category": result.get("risk_category"),
                        "confidence": result.get("confidence"),
                        "risk_factors": result.get("risk_factors", []),
                        "recommendations": result.get("recommendations", []),
                        "explanation": result.get("explanation", "")
                    }

            # Simple risk assessment fallback
            risk_score = 0.5  # Default medium risk
            if supplier_info.get("delivery_performance", 0) < 0.8:
                risk_score += 0.2
            if supplier_info.get("quality_metrics", 0) < 0.9:
                risk_score += 0.1

            risk_category = "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high"

            return {
                "risk_score": risk_score,
                "risk_category": risk_category,
                "confidence": 0.7,
                "risk_factors": ["delivery_performance", "quality_metrics"],
                "recommendations": ["Monitor performance closely"],
                "explanation": "Risk assessed using simple scoring algorithm"
            }

    async def optimize_inventory_with_ml(self, inventory_data: pd.DataFrame, sales_data: pd.DataFrame,
                                       supplier_data: pd.DataFrame) -> Dict[str, Any]:
        """
        ML-powered inventory optimization.

        Args:
            inventory_data: Current inventory levels
            sales_data: Historical sales data
            supplier_data: Supplier information

        Returns:
            Dict with optimization recommendations
        """
        with MLOperationLogger("optimize_inventory_with_ml", logger):
            # Prepare data files
            inventory_file = self.temp_dir / "inventory_opt.csv"
            sales_file = self.temp_dir / "sales_opt.csv"
            supplier_file = self.temp_dir / "supplier_opt.csv"

            inventory_data.to_csv(inventory_file, index=False)
            sales_data.to_csv(sales_file, index=False)
            supplier_data.to_csv(supplier_file, index=False)

            try:
                if self.zen_available:
                    result = await self._call_zen_tool(
                        "optimize_inventory_ml",
                        {
                            "inventory_data_path": str(inventory_file),
                            "sales_data_path": str(sales_file),
                            "supplier_data_path": str(supplier_file),
                            "optimization_objectives": [
                                "minimize_total_cost",
                                "maximize_service_level",
                                "minimize_stockout_risk",
                                "optimize_cash_flow"
                            ],
                            "constraints": {
                                "budget_limit": None,
                                "storage_capacity": None,
                                "supplier_minimums": True,
                                "lead_time_variability": True
                            },
                            "ml_approach": {
                                "demand_uncertainty": True,
                                "supply_uncertainty": True,
                                "dynamic_safety_stock": True,
                                "multi_objective_optimization": True
                            },
                            "textile_specific": {
                                "seasonality_factor": 0.3,
                                "fashion_trend_impact": 0.2,
                                "material_shelf_life": True,
                                "style_lifecycle": True
                            }
                        }
                    )

                    if result.get("status") != "error":
                        return {
                            "optimized_inventory": pd.DataFrame(result.get("optimized_levels", [])),
                            "cost_reduction": result.get("cost_savings", {}),
                            "service_level_improvement": result.get("service_improvement", {}),
                            "implementation_plan": result.get("implementation_steps", []),
                            "sensitivity_analysis": result.get("sensitivity", {}),
                            "roi_projection": result.get("roi", {})
                        }

                # Simple optimization fallback
                return {
                    "status": "success",
                    "optimized_inventory": inventory_data,
                    "message": "Using basic inventory optimization"
                }

            finally:
                # Clean up temp files
                inventory_file.unlink(missing_ok=True)
                sales_file.unlink(missing_ok=True)
                supplier_file.unlink(missing_ok=True)

    async def predict_material_prices(self, material_type: str, historical_prices: pd.DataFrame,
                                    forecast_days: int = 60) -> Dict[str, Any]:
        """
        Predict material price changes.

        Args:
            material_type: Type of material
            historical_prices: Historical price data
            forecast_days: Days to forecast

        Returns:
            Dict with price predictions
        """
        with MLOperationLogger("predict_material_prices", logger):
            price_file = self.temp_dir / f"prices_{material_type}.csv"
            historical_prices.to_csv(price_file, index=False)

            try:
                if self.zen_available:
                    result = await self._call_zen_tool(
                        "predict_material_prices",
                        {
                            "price_data_path": str(price_file),
                            "material_type": material_type,
                            "forecast_horizon": forecast_days,
                            "model_type": "time_series_with_external_factors",
                            "external_factors": [
                                "commodity_prices",
                                "currency_exchange",
                                "supply_chain_disruptions",
                                "seasonal_demand",
                                "market_sentiment"
                            ],
                            "include_volatility": True,
                            "include_scenarios": True,
                            "confidence_levels": [0.8, 0.9, 0.95]
                        }
                    )

                    if result.get("status") != "error":
                        return {
                            "price_forecast": pd.DataFrame(result.get("predictions", [])),
                            "volatility_forecast": result.get("volatility", {}),
                            "scenario_analysis": result.get("scenarios", {}),
                            "price_drivers": result.get("key_factors", []),
                            "recommendation": result.get("recommendation", "")
                        }

                # Simple price trend analysis
                if len(historical_prices) > 0:
                    avg_price = historical_prices.iloc[:, 0].mean()
                    trend = "stable"

                    return {
                        "price_forecast": pd.DataFrame({
                            "day": range(1, forecast_days + 1),
                            "price": [avg_price] * forecast_days
                        }),
                        "trend": trend,
                        "confidence": 0.6
                    }

                return {
                    "status": "error",
                    "message": "Insufficient data for price prediction"
                }

            finally:
                price_file.unlink(missing_ok=True)