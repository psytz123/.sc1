#!/usr/bin/env python
"""
Setup script for Zen-MCP Automated Code Management System

This script sets up the automation system and creates necessary
configuration files and directories.
"""

import json
from utils.logger import get_logger

logger = get_logger(__name__)
import os
import sys
from pathlib import Path


def create_directories():
    """Create necessary directories"""
    directories = [
        "automation",
        "config",
        "logs",
        "reports",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"✅ Created directory: {directory}")


def create_automation_config():
    """Create automation configuration"""
    config = {
        "zen_server_url": "http://localhost:5000",
        "scan_interval_minutes": 30,
        "auto_commit": False,
        "auto_pr": True,
        "excluded_paths": [
            "__pycache__",
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "dist",
            "build",
            ".pytest_cache",
            "*.egg-info"
        ],
        "file_patterns": [
            "*.py",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
            "*.java",
            "*.cpp",
            "*.c",
            "*.h",
            "*.cs"
        ],
        "max_concurrent_tasks": 3,
        "task_priorities": {
            "security": "CRITICAL",
            "bug_fix": "HIGH",
            "performance": "HIGH",
            "refactor": "MEDIUM",
            "documentation": "LOW"
        },
        "ml_improvements": {
            "enabled": True,
            "model_retraining_interval_days": 7,
            "performance_threshold": 0.85,
            "data_collection": True
        }
    }
    
    config_path = Path("config/automation_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✅ Created automation config: {config_path}")


def create_scheduler_config():
    """Create scheduler configuration"""
    config = {
        "run_interval_minutes": 30,
        "initial_delay_seconds": 10,
        "max_consecutive_errors": 3,
        "error_retry_delay_minutes": 5,
        "working_hours": {
            "enabled": False,
            "start_hour": 9,
            "end_hour": 17,
            "weekends_enabled": False
        },
        "notifications": {
            "enabled": False,
            "webhook_url": "",
            "notify_on_error": True,
            "notify_on_completion": False
        },
        "performance": {
            "max_run_time_minutes": 60,
            "memory_limit_mb": 1024
        }
    }
    
    config_path = Path("config/scheduler_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✅ Created scheduler config: {config_path}")


def create_startup_scripts():
    """Create startup scripts for different platforms"""
    
    # Windows batch script
    windows_script = """@echo off
echo Starting Zen-MCP Automation System...
echo.

REM Check if zen-mcp-server is running
curl -s http://localhost:5000/version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] zen-mcp-server is not running!
    echo Please start it first:
    echo   cd zen-mcp-server
    echo   .zen_venv\\Scripts\\python.exe server.py
    echo.
    pause
    exit /b 1
)

echo [OK] zen-mcp-server is running

REM Start the automation scheduler
echo.
echo Starting automation scheduler...
python automation/scheduler.py

pause
"""
    
    with open("start_automation.bat", 'w', encoding='utf-8') as f:
        f.write(windows_script)
    
    # Unix/Linux/Mac script
    unix_script = """#!/bin/bash
echo "Starting Zen-MCP Automation System..."
echo

# Check if zen-mcp-server is running
if ! curl -s http://localhost:5000/version > /dev/null 2>&1; then
    echo "[ERROR] zen-mcp-server is not running!"
    echo "Please start it first:"
    echo "  cd zen-mcp-server"
    echo "  .zen_venv/bin/python server.py"
    echo
    exit 1
fi

echo "[OK] zen-mcp-server is running"

# Start the automation scheduler
echo
echo "Starting automation scheduler..."
python automation/scheduler.py
"""
    
    with open("start_automation.sh", 'w', encoding='utf-8') as f:
        f.write(unix_script)
    
    # Make Unix script executable
    os.chmod("start_automation.sh", 0o755)
    
    logger.info("✅ Created startup scripts: start_automation.bat, start_automation.sh")


def create_monitoring_script():
    """Create monitoring startup script"""
    
    # Windows batch script
    windows_script = """@echo off
echo Starting Zen-MCP Automation Dashboard...
python automation/dashboard.py
pause
"""
    
    with open("start_dashboard.bat", 'w', encoding='utf-8') as f:
        f.write(windows_script)
    
    # Unix/Linux/Mac script
    unix_script = """#!/bin/bash
echo "Starting Zen-MCP Automation Dashboard..."
python automation/dashboard.py
"""
    
    with open("start_dashboard.sh", 'w', encoding='utf-8') as f:
        f.write(unix_script)
    
    os.chmod("start_dashboard.sh", 0o755)
    
    logger.info("✅ Created dashboard scripts: start_dashboard.bat, start_dashboard.sh")


def check_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        "aiohttp",
        "gitpython",
        "rich",
        "plotext",
        "schedule"
    ]
    
    logger.info("\n📦 Checking dependencies...")
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            logger.info(f"✅ {package} is installed")
        except ImportError:
            logger.info(f"❌ {package} is not installed")
            missing_packages.append(package)
    
    if missing_packages:
        logger.info(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        logger.info("Install them with:")
        logger.info(f"  pip install {' '.join(missing_packages)}")
        return False
    
    return True


def main():
    """Main setup function"""
    logger.info("🚀 Setting up Zen-MCP Automated Code Management System")
    logger.info("=" * 50)
    
    # Create directories
    logger.info("\n📁 Creating directories...")
    create_directories()
    
    # Create configuration files
    logger.info("\n⚙️  Creating configuration files...")
    create_automation_config()
    create_scheduler_config()
    
    # Create startup scripts
    logger.info("\n📝 Creating startup scripts...")
    create_startup_scripts()
    create_monitoring_script()
    
    # Check dependencies
    dependencies_ok = check_dependencies()
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ Setup complete!")
    logger.info("\nNext steps:")
    logger.info("1. Review and customize the configuration files in the 'config' directory")
    logger.info("2. Ensure zen-mcp-server is running (see ZEN_MCP_SUCCESS.md)")
    
    if not dependencies_ok:
        logger.info("3. Install missing dependencies (see above)")
        logger.info("4. Run the automation system:")
    else:
        logger.info("3. Run the automation system:")
    
    if sys.platform == "win32":
        logger.info("   start_automation.bat")
    else:
        logger.info("   ./start_automation.sh")
    
    logger.info("\n4. Monitor the system:")
    if sys.platform == "win32":
        logger.info("   start_dashboard.bat")
    else:
        logger.info("   ./start_dashboard.sh")
    
    logger.info("\n📚 For more information, see automation/README.md")


if __name__ == "__main__":
    main()