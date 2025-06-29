#!/usr/bin/env python
"""
Python Environment and Dependency Installation Helper

This script helps with Python version compatibility and dependency installation.
"""

import platform
from utils.logger import get_logger

logger = get_logger(__name__)
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check Python version and provide recommendations."""
    version = sys.version_info
    logger.info(f"Current Python version: {version.major}.{version.minor}.{version.micro}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info()
    
    if version.major == 3 and version.minor >= 13:
        logger.info("⚠️  WARNING: You are using Python 3.13+")
        logger.info("   TensorFlow does not yet support Python 3.13.")
        logger.info("   You have the following options:")
        logger.info()
        logger.info("   1. Use alternative ML libraries (already configured)")
        logger.info("      - scikit-learn, XGBoost, LightGBM, Prophet")
        logger.info("      - These provide excellent ML capabilities")
        logger.info()
        logger.info("   2. Install Python 3.11 or 3.12 for TensorFlow support")
        logger.info("      - Download from https://www.python.org/downloads/")
        logger.info("      - Create a new virtual environment with the older Python")
        logger.info()
        logger.info("   3. Use PyTorch instead of TensorFlow")
        logger.info("      - PyTorch often has better Python version support")
        logger.info("      - Run: pip install torch torchvision torchaudio")
        logger.info()
        return False
    elif version.major == 3 and version.minor >= 8:
        logger.info("✓ Python version is compatible with most ML libraries")
        return True
    else:
        logger.info("⚠️  WARNING: Python version is too old")
        logger.info("   Please upgrade to Python 3.8 or newer")
        return False


def install_basic_dependencies():
    """Install basic dependencies that work with Python 3.13."""
    logger.info("\nInstalling basic dependencies compatible with Python 3.13...")
    
    basic_deps = [
        "pandas>=1.5.0",
        "numpy>=1.23.0",
        "scikit-learn>=1.3.0",
        "xgboost>=1.7.0",
        "lightgbm>=4.0.0",
        "openpyxl>=3.1.0",
        "xlsxwriter>=3.1.0",
        "aiohttp>=3.8.0",
        "aiofiles>=23.0.0",
        "pytest>=7.4.0",
        "loguru>=0.7.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "tqdm>=4.65.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0"
    ]
    
    for dep in basic_deps:
        logger.info(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            logger.info(f"✓ Successfully installed {dep}")
        except subprocess.CalledProcessError:
            logger.info(f"✗ Failed to install {dep}")


def create_alternative_venv_script():
    """Create a script to set up Python 3.11/3.12 environment."""
    script_content = """#!/bin/bash
# Script to create a virtual environment with Python 3.11 or 3.12 for TensorFlow

echo "This script helps create a virtual environment with Python 3.11/3.12 for TensorFlow support"
echo ""

# Check if Python 3.11 or 3.12 is installed
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "Found Python 3.11"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "Found Python 3.12"
else
    echo "Neither Python 3.11 nor 3.12 found."
    echo "Please install Python 3.11 or 3.12 from https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv venv_tf

# Activate and install dependencies
echo "Activating virtual environment..."
source venv_tf/bin/activate

echo "Installing TensorFlow and dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-deep-learning.txt

echo ""
echo "Setup complete! To use this environment:"
echo "  source venv_tf/bin/activate"
"""
    
    # Windows version
    script_content_windows = """@echo off
REM Script to create a virtual environment with Python 3.11 or 3.12 for TensorFlow

echo This script helps create a virtual environment with Python 3.11/3.12 for TensorFlow support
echo.

REM Check for Python versions
where py -3.11 >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3.11
    echo Found Python 3.11
    goto create_venv
)

where py -3.12 >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3.12
    echo Found Python 3.12
    goto create_venv
)

echo Neither Python 3.11 nor 3.12 found.
echo Please install Python 3.11 or 3.12 from https://www.python.org/downloads/
exit /b 1

:create_venv
echo Creating virtual environment...
%PYTHON_CMD% -m venv venv_tf

echo Activating virtual environment...
call venv_tf\\Scripts\\activate.bat

echo Installing TensorFlow and dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-deep-learning.txt

echo.
echo Setup complete! To use this environment:
echo   venv_tf\\Scripts\\activate
"""
    
    if platform.system() == "Windows":
        with open("create_tf_env.bat", "w") as f:
            f.write(script_content_windows)
        logger.info("\nCreated create_tf_env.bat for setting up TensorFlow environment")
    else:
        with open("create_tf_env.sh", "w") as f:
            f.write(script_content)
        Path("create_tf_env.sh").chmod(0o755)
        logger.info("\nCreated create_tf_env.sh for setting up TensorFlow environment")


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Beverly Knits - Python Environment Check")
    logger.info("=" * 60)
    logger.info()
    
    # Check Python version
    version_ok = check_python_version()
    
    logger.info("\n" + "=" * 60)
    logger.info("Recommended Installation Approach:")
    logger.info("=" * 60)
    
    if not version_ok and sys.version_info.minor >= 13:
        logger.info("\n1. For immediate development (without TensorFlow):")
        logger.info("   pip install -r requirements.txt")
        logger.info("   This includes all ML libraries except TensorFlow")
        logger.info()
        logger.info("2. For TensorFlow support:")
        create_alternative_venv_script()
        logger.info("   - Install Python 3.11 or 3.12")
        if platform.system() == "Windows":
            logger.info("   - Run: create_tf_env.bat")
        else:
            logger.info("   - Run: ./create_tf_env.sh")
        logger.info()
        logger.info("3. Try PyTorch as an alternative:")
        logger.info("   pip install torch torchvision torchaudio")
        logger.info()
        
        response = input("Would you like to install basic dependencies now? (y/n): ")
        if response.lower() == 'y':
            install_basic_dependencies()
    else:
        logger.info("\nYour Python version is compatible. Install all dependencies with:")
        logger.info("   pip install -r requirements.txt")
        logger.info("   pip install -r requirements-deep-learning.txt  # For deep learning")
    
    logger.info("\n" + "=" * 60)
    logger.info("Additional Notes:")
    logger.info("=" * 60)
    logger.info("- The project is configured to work without TensorFlow")
    logger.info("- Alternative ML libraries provide excellent capabilities:")
    logger.info("  * XGBoost/LightGBM for gradient boosting")
    logger.info("  * Prophet for time series forecasting")
    logger.info("  * scikit-learn for traditional ML algorithms")
    logger.info("- You can proceed with Phase 2 using these libraries")


if __name__ == "__main__":
    main()