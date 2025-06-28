

```markdown
# AI_ML_INTEGRATION.md

# AI/ML Integration for Beverly Knits Raw Material Planner

## Overview
This document outlines the integration of zen-mcp-server for AI/ML capabilities within the Beverly Knits AI Raw Material Planner, focusing on predictive analytics, demand forecasting, and intelligent decision support.

## Use Cases for Beverly Knits

### 1. Demand Forecasting & Prediction
- **Yarn Demand Prediction**: Forecast yarn requirements based on historical sales and trends
- **Seasonal Demand Modeling**: Model seasonal variations in textile demand
- **Style Popularity Prediction**: Predict which styles will be popular in upcoming seasons
- **Material Substitution Recommendations**: AI-powered material substit

ution suggestions

### 2. Supply Chain Optimization
- **Supplier Risk Assessment**: ML-based supplier reliability and risk scoring
- **Lead Time Prediction**: Predict actual delivery times based on supplier performance
- **Price Forecasting**: Forecast raw material price changes
- **Inventory Optimization**: AI-driven safety stock and reorder point optimization

### 3. Quality Prediction & Control
- **Material Quality Prediction**: Predict quality issues before they occur
- **Defect Pattern Recognition**: Identify patterns in quality defects
- **Supplier Quality Scoring**: ML-based quality assessment of suppliers
- **Production Yield Prediction**: Predict production yields based on material quality

### 4. Business Intelligence & Insights
- **Market Trend Analysis**: AI-powered analysis of fashion and textile trends
- **Customer Behavior Prediction**: Predict customer purchasing patterns
- **Cost Optimization**: ML-driven cost reduction recommendations
- **Strategi

c Planning Support**: AI insights for long-term planning

## Integration Steps

### Step 1: AI/ML Client Implementation

```python
# src/core/ml_integration_client.py
import subprocess
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import pickle
import asyncio
from datetime import datetime, timedelta

class BeverlyKnitsMLClient:
    """AI/ML integration client for Beverly Knits using zen-mcp-server"""
    
    def __init__(self, config_path: str = "config/zen_ml_config.json"):
        self.config_path = config_path
        self.zen_process = None
        self.logger = logging.getLogger(__name__)
        self.models_dir = Path("models/ml_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("temp/ml_processing")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self) -> None:
        """Initialize zen-mcp-

server for ML operations"""
        try:
            self.zen_process = subprocess.Popen([
                'zen-mcp-server',
                '--config', self.config_path,
                '--mode', 'ml_integration'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, text=True)
            
            self.logger.info("✅ ML integration capabilities initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize ML integration: {e}")
            raise
    
    async def train_demand_forecasting_model(self, sales_data: pd.DataFrame, material_type: str = "yarn") -> Dict[str, Any]:
        """Train demand forecasting model for textile materials"""
        # Prepare training data
        training_file = self.temp_dir / f"demand_training_{material_type}.csv"
        sales_data.to_csv(training_file, index=False)
        
        request = {
            "tool": "train_textile_demand_model",
            "

arguments": {
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
                    "forecast_horizon": 90,  # 90 days
                    "seasonality_periods": [7, 30, 365],  # weekly, monthly, yearly
                    "include_holidays": True,
                    "include_weather": False  # Can be enabled if weather data available
                },
                "validation_split": 0.2,
                "hyperparameter_tuning": True,
                "save_model": True,
                "model_name": f"demand_forecast_{material_type}"
            }
        }
        
        result

 = await self._call_zen_tool(request)
        
        # Clean up temp file
        training_file.unlink(missing_ok=True)
        
        return {
            "model_id": result.get("model_id"),
            "model_path": result.get("model_path"),
            "training_metrics": result.get("metrics", {}),
            "validation_score": result.get("validation_score"),
            "feature_importance": result.get("feature_importance", {}),
            "model_summary": result.get("model_summary", {})
        }
    
    async def predict_material_demand(self, model_id: str, forecast_days: int = 30) -> Dict[str, Any]:
        """Predict material demand using trained model"""
        request = {
            "tool": "predict_material_demand",
            "arguments": {
                "model_id": model_id,
                "forecast_horizon": forecast_days,
                "include_confidence_intervals": True,
                "include_scenario_analysis": True,
                "scenarios": ["optim

istic", "realistic", "pessimistic"],
                "external_factors": {
                    "seasonal_adjustment": True,
                    "trend_continuation": True,
                    "market_conditions": "normal"
                }
            }
        }
        
        result = await self._call_zen_tool(request)
        
        return {
            "predictions": pd.DataFrame(result.get("predictions", [])),
            "confidence_intervals": result.get("confidence_intervals", {}),
            "scenario_forecasts": result.get("scenarios", {}),
            "prediction_date": datetime.now().isoformat(),
            "model_confidence": result.get("model_confidence", 0)
        }
    
    async def train_supplier_risk_model(self, supplier_data: pd.DataFrame, performance_data: pd.DataFrame) -> Dict[str, Any]:
        """Train supplier risk assessment model"""
        # Prepare training data
        supplier_file = self.temp_dir / "supplier_training.csv"
        performance_file = sel

f.temp_dir / "performance_training.csv"
        
        supplier_data.to_csv(supplier_file, index=False)
        performance_data.to_csv(performance_file, index=False)
        
        request = {
            "tool": "train_supplier_risk_model",
            "arguments": {
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
                    "

feature_selection": True,
                    "cross_validation": 5
                },
                "model_name": "supplier_risk_assessment"
            }
        }
        
        result = await self._call_zen_tool(request)
        
        # Clean up temp files
        supplier_file.unlink(missing_ok=True)
        performance_file.unlink(missing_ok=True)
        
        return {
            "model_id": result.get("model_id"),
            "model_path": result.get("model_path"),
            "accuracy_score": result.get("accuracy"),
            "precision_recall": result.get("precision_recall", {}),
            "feature_importance": result.get("feature_importance", {}),
            "confusion_matrix": result.get("confusion_matrix", [])
        }
    
    async def assess_supplier_risk(self, model_id: str, supplier_info: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for a specific supplier"""
        request = {
            "tool": "assess_supplier_risk",
            "

arguments": {
                "model_id": model_id,
                "supplier_data": supplier_info,
                "include_explanation": True,
                "include_recommendations": True,
                "risk_factors_analysis": True
            }
        }
        
        result = await self._call_zen_tool(request)
        
        return {
            "risk_score": result.get("risk_score"),
            "risk_category": result.get("risk_category"),
            "confidence": result.get("confidence"),
            "risk_factors": result.get("risk_factors", []),
            "recommendations": result.get("recommendations", []),
            "explanation": result.get("explanation", "")
        }
    
    async def optimize_inventory_with_ml(self, inventory_data: pd.DataFrame, sales_data: pd.DataFrame, 
                                       supplier_data: pd.DataFrame) -> Dict[str, Any]:
        """ML-powered inventory optimization"""
        # Prepare data files
        inventory_file = self.

temp_dir / "inventory_opt.csv"
        sales_file = self.temp_dir / "sales_opt.csv"
        supplier_file = self.temp_dir / "supplier_opt.csv"
        
        inventory_data.to_csv(inventory_file, index=False)
        sales_data.to_csv(sales_file, index=False)
        supplier_data.to_csv(supplier_file, index=False)
        
        request = {
            "tool": "optimize_inventory_ml",
            "arguments": {
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
                    "budget_limit": None,  # Will be set from config
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
        }
        
        result = await self._call_zen_tool(request)
        
        # Clean up temp files
        inventory_file.unlink(missing_ok=True)
        sales_file.unlink(missing_ok=True)
        supplier_file.unlink(missing_ok=True)
        
        return {
            "optimized_inventory": pd.DataFrame(result.get("optimized_levels", [])),
            "cost_reduction": result.get("cost_savings", {}),
            "

service_level_improvement": result.get("service_improvement", {}),
            "implementation_plan": result.get("implementation_steps", []),
            "sensitivity_analysis": result.get("sensitivity", {}),
            "roi_projection": result.get("roi", {})
        }
    
    async def predict_material_prices(self, material_type: str, historical_prices: pd.DataFrame, 
                                    forecast_days: int = 60) -> Dict[str, Any]:
        """Predict material price changes"""
        price_file = self.temp_dir / f"prices_{material_type}.csv"
        historical_prices.to_csv(price_file, index=False)
        
        request = {
            "tool": "predict_material_prices",
            "arguments": {
                "price_data_path": str(price_file),
                "material_type": material_type,
                "forecast_horizon": forecast_days,
                "model_type": "time_series_with_external_factors",
                "external_factors": [
                    "

commodity_prices",
                    "currency_exchange",
                    "supply_chain_disruptions",
                    "seasonal_demand",
                    "market_sentiment"
                ],
                "include_volatility": True,
                "include_scenarios": True,
                "confidence_levels": [0.8, 0.9, 0.95]
            }
        }
        
        result = await self._call_zen_tool(request)
        
        price_file.unlink(missing_ok=True)
        
        return {
            "price_forecast": pd.DataFrame(result.get("predictions", [])),
            "volatility_forecast": result.get("volatility", {}),
            "scenario_analysis": result.get("scenarios", {}),
            "price_drivers": result.get("key_factors", []),
            "recommendation": result.
