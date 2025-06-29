#!/usr/bin/env python3
"""Test script to verify basic imports work correctly."""

import sys
print(f"Python version: {sys.version}")
print("-" * 50)

# Test core imports
try:
    import pandas as pd
    print("✓ pandas imported successfully")
    print(f"  Version: {pd.__version__}")
except ImportError as e:
    print(f"✗ Failed to import pandas: {e}")

try:
    import numpy as np
    print("✓ numpy imported successfully")
    print(f"  Version: {np.__version__}")
except ImportError as e:
    print(f"✗ Failed to import numpy: {e}")

try:
    import openpyxl
    print("✓ openpyxl imported successfully")
    print(f"  Version: {openpyxl.__version__}")
except ImportError as e:
    print(f"✗ Failed to import openpyxl: {e}")

try:
    import xlsxwriter
    print("✓ xlsxwriter imported successfully")
    print(f"  Version: {xlsxwriter.__version__}")
except ImportError as e:
    print(f"✗ Failed to import xlsxwriter: {e}")

try:
    import dotenv
    print("✓ python-dotenv imported successfully")
    # dotenv module doesn't have __version__, so we'll skip version display
except ImportError as e:
    print(f"✗ Failed to import dotenv: {e}")

try:
    import pydantic
    print("✓ pydantic imported successfully")
    print(f"  Version: {pydantic.__version__}")
except ImportError as e:
    print(f"✗ Failed to import pydantic: {e}")

try:
    import loguru
    print("✓ loguru imported successfully")
    print(f"  Version: {loguru.__version__}")
except ImportError as e:
    print(f"✗ Failed to import loguru: {e}")

try:
    import aiohttp
    print("✓ aiohttp imported successfully")
    print(f"  Version: {aiohttp.__version__}")
except ImportError as e:
    print(f"✗ Failed to import aiohttp: {e}")

try:
    import httpx
    print("✓ httpx imported successfully")
    print(f"  Version: {httpx.__version__}")
except ImportError as e:
    print(f"✗ Failed to import httpx: {e}")

print("-" * 50)
print("Basic import test completed!")

# Test basic functionality
print("\nTesting basic functionality...")
try:
    # Create a simple DataFrame
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    print("✓ Created pandas DataFrame successfully")
    
    # Basic numpy operation
    arr = np.array([1, 2, 3])
    print("✓ Created numpy array successfully")
    
    # Basic pydantic model
    from pydantic import BaseModel
    
    class TestModel(BaseModel):
        name: str
        value: int
    
    test_obj = TestModel(name="test", value=42)
    print("✓ Created pydantic model successfully")
    
    print("\nAll basic functionality tests passed!")
    
except Exception as e:
    print(f"✗ Error during functionality test: {e}")