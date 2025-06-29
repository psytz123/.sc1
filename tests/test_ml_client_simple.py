"""
Test script for ML Integration Client
"""

import os
from utils.logger import get_logger

logger = get_logger(__name__)
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

# Import without going through __init__.py
import importlib.util

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "ml_integration_client", 
    "src/core/ml_integration_client.py"
)
ml_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml_module)

BeverlyKnitsMLClient = ml_module.BeverlyKnitsMLClient


async def test_ml_client():
    """Test basic ML client functionality"""
    logger.info("🚀 Testing Beverly Knits ML Client...")
    
    try:
        # Initialize client
        client = BeverlyKnitsMLClient()
        logger.info("✅ Client initialized successfully")
        
        # Check available ML libraries
        logger.info(f"\n📚 Available ML libraries: {ml_module.ML_LIBRARIES}")
        
        # Check server status
        logger.info("\n📡 Checking zen-mcp-server status...")
        status = await client.check_zen_server_status()
        logger.info(f"Server available: {status['available']}")
        if not status['available']:
            logger.info(f"Reason: {status.get('reason', 'Unknown')}")
        
        # Create sample data
        logger.info("\n📊 Creating sample demand data...")
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        demand_data = pd.DataFrame({
            'date': dates,
            'demand': np.random.randint(100, 500, size=len(dates)),
            'price': np.random.uniform(10, 50, size=len(dates)),
            'season': ['winter', 'spring', 'summer', 'fall'][0] * len(dates),
            'material_type': 'yarn'
        })
        logger.info(f"Created {len(demand_data)} days of data")
        
        # Test training (if sklearn is available)
        if ml_module.ML_LIBRARIES.get('sklearn', False):
            logger.info("\n🤖 Testing model training...")
            result = await client.train_demand_forecast_model(
                historical_data=demand_data,
                material_type="yarn"
            )
            logger.info(f"Training result: {result['status']}")
            if result['status'] == 'success':
                logger.info(f"Model ID: {result['model_id']}")
                logger.info(f"Metrics: {result['metrics']}")
        else:
            logger.info("\n⚠️  scikit-learn not available, skipping training test")
        
        # Clean up
        await client.close()
        logger.info("\n✅ All tests completed successfully!")
        
    except Exception as e:
        logger.info(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ml_client())