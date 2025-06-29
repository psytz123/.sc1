"""
Test suite for Beverly Knits integration components
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
TEST_CONFIG_DIR = Path(__file__).parent / "test_configs"
TEST_DATA_DIR = Path(__file__).parent / "test_data"

# Create test directories
TEST_CONFIG_DIR.mkdir(exist_ok=True)
TEST_DATA_DIR.mkdir(exist_ok=True)