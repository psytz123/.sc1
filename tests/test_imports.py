"""Test script to verify all imports work correctly"""

import sys
print(f"Python version: {sys.version}")

# Test core imports
try:
    import pandas as pd
    import numpy as np
    print("✓ Core data libraries imported successfully")
except ImportError as e:
    print(f"✗ Core data libraries import error: {e}")

# Test Streamlit
try:
    import streamlit as st
    import plotly.express as px
    print("✓ Streamlit and Plotly imported successfully")
except ImportError as e:
    print(f"✗ Streamlit/Plotly import error: {e}")

# Test project modules
try:
    from config.settings import BusinessRules
    from data.sample_data_generator import SampleDataGenerator
    from engine.planner import RawMaterialPlanner
    from models.bom import BOMExploder
    from models.forecast import ForecastProcessor
    from models.inventory import InventoryNetter
    from models.recommendation import RecommendationGenerator
    from models.supplier import SupplierSelector
    from utils.helpers import ReportGenerator
    print("✓ All project modules imported successfully")
except ImportError as e:
    print(f"✗ Project modules import error: {e}")

# Test ML libraries (optional)
try:
    import scikit_learn
    print("✓ Scikit-learn imported successfully")
except ImportError:
    print("⚠ Scikit-learn not installed (optional)")

try:
    import xgboost
    print("✓ XGBoost imported successfully")
except ImportError:
    print("⚠ XGBoost not installed (optional)")

print("\nImport test completed!")