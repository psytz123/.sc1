"""
Example usage of Beverly Knits ML Integration Client

This script demonstrates how to use the ML client for demand forecasting
and other ML operations in the Beverly Knits Raw Material Planner.
"""

import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)
import os
import sys

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.ml_integration_client import BeverlyKnitsMLClient


async def main():
    """Main example function"""
    
    # Initialize the ML client
    logger.info("🚀 Initializing Beverly Knits ML Client...")
    client = BeverlyKnitsMLClient()
    
    # Check zen-mcp-server status
    logger.info("\n📡 Checking zen-mcp-server status...")
    status = await client.check_zen_server_status()
    logger.info(f"Server available: {status['available']}")
    if not status['available']:
        logger.info(f"Reason: {status.get('reason', 'Unknown')}")
    logger.info(f"Available ML libraries: {[lib for lib, avail in status['ml_libraries'].items() if avail]}")
    
    # Create sample historical demand data
    logger.info("\n📊 Creating sample demand data...")
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    demand_data = pd.DataFrame({
        'date': dates,
        'demand': np.random.randint(100, 500, size=len(dates)) + 
                  np.sin(np.arange(len(dates)) * 2 * np.pi / 365) * 50,  # Add seasonality
        'price': np.random.uniform(10, 50, size=len(dates)),
        'season': ['winter', 'winter', 'spring', 'spring', 'summer', 'summer', 
                   'fall', 'fall'][[(i // 45) % 8 for i in range(len(dates))]],
        'material_type': 'yarn',
        'day_of_week': [d.dayofweek for d in dates],
        'month': [d.month for d in dates]
    })
    
    logger.info(f"Created {len(demand_data)} days of historical data")
    logger.info(demand_data.head())
    
    # Train a demand forecasting model
    logger.info("\n🤖 Training demand forecast model...")
    train_result = await client.train_demand_forecast_model(
        historical_data=demand_data,
        material_type="yarn",
        model_type="auto"
    )
    
    if train_result['status'] == 'success':
        logger.info(f"✅ Model trained successfully!")
        logger.info(f"Model ID: {train_result['model_id']}")
        logger.info(f"Metrics: MAE={train_result['metrics']['mae']:.2f}, "
              f"RMSE={train_result['metrics']['rmse']:.2f}")
        if train_result.get('fallback_used'):
            logger.info("ℹ️  Used local ML libraries (zen-mcp-server not available)")
        
        # Generate predictions
        logger.info("\n🔮 Generating demand predictions...")
        future_dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        future_features = pd.DataFrame({
            'price': np.random.uniform(10, 50, size=len(future_dates)),
            'season': ['winter'] * len(future_dates),
            'material_type': 'yarn',
            'day_of_week': [d.dayofweek for d in future_dates],
            'month': [d.month for d in future_dates]
        })
        
        predict_result = await client.predict_demand(
            model_id=train_result['model_id'],
            features=future_features,
            horizon=30
        )
        
        if predict_result['status'] == 'success':
            logger.info(f"✅ Generated {len(predict_result['predictions'])} predictions")
            logger.info(f"Average predicted demand: {np.mean(predict_result['predictions']):.2f}")
            logger.info(f"Prediction range: {min(predict_result['predictions']):.2f} - "
                  f"{max(predict_result['predictions']):.2f}")
    else:
        logger.info(f"❌ Model training failed: {train_result['message']}")
    
    # Test supplier risk analysis
    logger.info("\n📈 Analyzing supplier risk...")
    supplier_data = pd.DataFrame({
        'supplier_id': ['SUP001', 'SUP002', 'SUP003', 'SUP004'],
        'supplier_name': ['Premium Yarns Inc', 'Global Textiles', 'FastThread Co', 'ReliableKnits'],
        'delivery_performance': [0.95, 0.75, 0.85, 0.92],
        'quality_score': [0.98, 0.88, 0.92, 0.95],
        'price_stability': [0.90, 0.70, 0.85, 0.88],
        'lead_time_days': [14, 28, 21, 16],
        'order_history_count': [150, 75, 100, 200]
    })
    
    risk_result = await client.analyze_supplier_risk(supplier_data)
    if risk_result['status'] == 'success':
        logger.info("✅ Supplier risk analysis completed")
        logger.info(f"Analysis date: {risk_result['analysis_date']}")
    
    # Test inventory optimization
    logger.info("\n📦 Optimizing inventory levels...")
    inventory_data = pd.DataFrame({
        'material_id': ['YARN001', 'YARN002', 'YARN003'],
        'material_name': ['Cotton Yarn 30s', 'Polyester Yarn 40s', 'Wool Blend 20s'],
        'current_stock': [5000, 3000, 2000],
        'safety_stock': [1000, 600, 400],
        'unit_cost': [25.50, 18.75, 45.00],
        'storage_cost_per_unit': [0.50, 0.40, 0.75]
    })
    
    optim_result = await client.optimize_inventory_levels(
        inventory_data=inventory_data,
        demand_forecast=demand_data.tail(30)  # Last 30 days as forecast
    )
    
    if optim_result['status'] == 'success':
        logger.info("✅ Inventory optimization completed")
        logger.info(f"Optimization date: {optim_result['optimization_date']}")
    
    # Clean up
    logger.info("\n🧹 Closing ML client...")
    await client.close()
    logger.info("✅ Done!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())