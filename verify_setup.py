#!/usr/bin/env python
"""
Verification script for Beverly Knits AI Raw Material Planner setup

This script verifies that Phase 1 setup has been completed successfully.
"""

import json
from utils.logger import get_logger

logger = get_logger(__name__)
import sys
from pathlib import Path


def check_directory_structure():
    """Check if all required directories exist."""
    logger.info("Checking directory structure...")
    
    required_dirs = [
        "config",
        "src/core",
        "models/ml_models",
        "temp/ml_processing",
        "temp/data_processing",
        "integrations/suppliers",
        "tests",
        "templates",
        "generated"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        exists = path.exists()
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {dir_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_config_files():
    """Check if all configuration files exist and are valid JSON."""
    logger.info("\nChecking configuration files...")
    
    config_files = [
        "config/zen_ml_config.json",
        "config/zen_code_config.json",
        "config/zen_data_config.json"
    ]
    
    all_valid = True
    for config_path in config_files:
        path = Path(config_path)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    json.load(f)
                logger.info(f"  ✓ {config_path} - Valid JSON")
            except json.JSONDecodeError as e:
                logger.info(f"  ✗ {config_path} - Invalid JSON: {e}")
                all_valid = False
        else:
            logger.info(f"  ✗ {config_path} - File not found")
            all_valid = False
    
    return all_valid


def check_core_modules():
    """Check if core Python modules exist."""
    logger.info("\nChecking core modules...")
    
    modules = [
        "src/__init__.py",
        "src/core/__init__.py",
        "src/core/ml_integration_client.py",
        "src/core/code_management_client.py",
        "src/core/data_processing_client.py"
    ]
    
    all_exist = True
    for module_path in modules:
        path = Path(module_path)
        exists = path.exists()
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {module_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_requirements():
    """Check if requirements.txt exists."""
    logger.info("\nChecking requirements file...")
    
    req_path = Path("requirements.txt")
    if req_path.exists():
        with open(req_path, 'r') as f:
            lines = f.readlines()
        logger.info(f"  ✓ requirements.txt - Found {len([l for l in lines if l.strip() and not l.startswith('#')])} dependencies")
        return True
    else:
        logger.info("  ✗ requirements.txt - Not found")
        return False


def check_virtual_environment():
    """Check if virtual environment exists."""
    logger.info("\nChecking virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists() and venv_path.is_dir():
        # Check for key venv indicators
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        if python_exe.exists():
            logger.info("  ✓ Virtual environment 'venv' exists")
            return True
        else:
            logger.info("  ✗ Virtual environment 'venv' exists but appears incomplete")
            return False
    else:
        logger.info("  ✗ Virtual environment 'venv' not found")
        return False


def main():
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("Beverly Knits AI Raw Material Planner - Phase 1 Verification")
    logger.info("=" * 60)
    
    checks = [
        ("Directory Structure", check_directory_structure()),
        ("Configuration Files", check_config_files()),
        ("Core Modules", check_core_modules()),
        ("Requirements File", check_requirements()),
        ("Virtual Environment", check_virtual_environment())
    ]
    
    logger.info("\n" + "=" * 60)
    logger.info("Summary:")
    logger.info("=" * 60)
    
    all_passed = True
    for check_name, passed in checks:
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✓ Phase 1 setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Activate the virtual environment:")
        if sys.platform == "win32":
            logger.info("   venv\\Scripts\\activate")
        else:
            logger.info("   source venv/bin/activate")
        logger.info("2. Install dependencies:")
        logger.info("   pip install -r requirements.txt")
        logger.info("3. Proceed to Phase 2: Core Client Implementation")
    else:
        logger.info("✗ Phase 1 setup incomplete. Please check the failed items above.")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    main()