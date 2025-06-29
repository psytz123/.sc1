#!/usr/bin/env python
"""
Zen MCP Server Installation Verification and Setup Guide

This script checks for zen-mcp-server installation and provides setup instructions.
Updated to detect both Node.js and Python versions of zen-mcp-server.
"""

import json
from utils.logger import get_logger

logger = get_logger(__name__)
import subprocess
import sys
from pathlib import Path


def check_git_installed():
    """Check if Git is installed."""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✓ Git is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    logger.info("✗ Git is not installed")
    return False


def check_node_installed():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✓ Node.js is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    logger.info("✗ Node.js is not installed")
    return False


def check_python_installed():
    """Check Python version."""
    logger.info(f"✓ Python is installed: {sys.version.split()[0]}")
    return True


def check_zen_mcp_server():
    """Check if zen-mcp-server is cloned and set up."""
    # Check common locations
    possible_paths = [
        Path.cwd() / "zen-mcp-server",
        Path.cwd().parent / "zen-mcp-server",
        Path.home() / "zen-mcp-server",
        Path("C:/zen-mcp-server"),
        Path("D:/zen-mcp-server"),
    ]
    
    for path in possible_paths:
        if path.exists():
            # Check for Python version (has server.py)
            if (path / "server.py").exists():
                logger.info(f"✓ Found Python zen-mcp-server at: {path}")
                return path, "python"
            # Check for Node.js version (has package.json)
            elif (path / "package.json").exists():
                logger.info(f"✓ Found Node.js zen-mcp-server at: {path}")
                return path, "nodejs"
    
    logger.info("✗ zen-mcp-server not found in common locations")
    return None, None


def check_env_file(zen_path):
    """Check if .env file is configured."""
    env_path = zen_path / ".env"
    if env_path.exists():
        logger.info(f"✓ .env file exists at: {env_path}")
        # Check if it's properly configured (not just a copy of .env.example)
        try:
            with open(env_path, 'r') as f:
                content = f.read()
                if "your_" in content or "YOUR_" in content:
                    logger.info("  ⚠️  Warning: .env file may contain placeholder values")
                    logger.info("     Please update with your actual API keys")
                else:
                    logger.info("  ✓ .env file appears to be configured")
        except:
            pass
        return True
    else:
        logger.info(f"✗ .env file not found at: {env_path}")
        return False


def check_zen_server_running():
    """Check if zen-mcp-server is currently running."""
    try:
        import requests

        # Try common ports
        for port in [3000, 5000, 8000]:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    logger.info(f"✓ zen-mcp-server appears to be running on port {port}")
                    return True, port
            except:
                pass
    except ImportError:
        pass
    
    logger.info("✗ zen-mcp-server is not currently running")
    return False, None


def print_python_setup_instructions(zen_path=None):
    """Print setup instructions for Python zen-mcp-server."""
    logger.info("\n" + "="*60)
    logger.info("Python Zen MCP Server Setup Instructions")
    logger.info("="*60)
    
    if zen_path:
        logger.info(f"\n✓ zen-mcp-server is installed at: {zen_path}")
        logger.info("\nTo run the server:")
        logger.info(f"   cd {zen_path}")
        logger.info("   python server.py")
        logger.info("\n   Or use the run script:")
        logger.info("   ./run-server.sh  (Linux/Mac)")
        logger.info("   python server.py  (Windows)")
    else:
        logger.info("\n1. Clone the repository:")
        logger.info("   git clone https://github.com/BeehiveInnovations/zen-mcp-server.git")
        logger.info("   cd zen-mcp-server")
        
        logger.info("\n2. Create virtual environment:")
        logger.info("   python -m venv .zen_venv")
        logger.info("   .zen_venv\\Scripts\\activate  (Windows)")
        logger.info("   source .zen_venv/bin/activate  (Linux/Mac)")
        
        logger.info("\n3. Install dependencies:")
        logger.info("   pip install -r requirements.txt")
        
        logger.info("\n4. Configure environment:")
        logger.info("   copy .env.example .env  (Windows)")
        logger.info("   cp .env.example .env  (Linux/Mac)")
        logger.info("   # Edit .env with your API keys")
    
    logger.info("\n" + "="*60)


def update_beverly_knits_config(server_type="python", port=5000):
    """Update Beverly Knits configuration for zen-mcp-server."""
    config_path = Path("config/zen_mcp_config.json")
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update port based on server type
        if server_type == "python":
            config["zen_mcp_server"]["url"] = f"http://localhost:{port}"
            logger.info(f"\n✓ Updated zen_mcp_config.json for Python server on port {port}")
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)


def main():
    """Main verification function."""
    logger.info("="*60)
    logger.info("Zen MCP Server Installation Verification")
    logger.info("="*60)
    logger.info()
    
    # Check prerequisites
    logger.info("Checking Prerequisites:")
    check_git_installed()
    check_node_installed()
    check_python_installed()
    
    logger.info("\nChecking Zen MCP Server:")
    zen_path, server_type = check_zen_mcp_server()
    
    if zen_path:
        check_env_file(zen_path)
        running, port = check_zen_server_running()
        
        if server_type == "python":
            logger.info(f"\n✓ Python-based zen-mcp-server is installed")
            print_python_setup_instructions(zen_path)
            
            # Update Beverly Knits config
            update_beverly_knits_config("python", port or 5000)
            
            logger.info("\nIntegration Status:")
            logger.info("✓ Beverly Knits ML client is configured for zen-mcp-server")
            logger.info("✓ The ML client will automatically detect when the server is running")
            logger.info("\nTo start using zen-mcp-server with Beverly Knits:")
            logger.info("1. Ensure your .env file has valid API keys")
            logger.info("2. Start the zen-mcp-server")
            logger.info("3. The ML client will automatically use it for enhanced AI features")
            
    else:
        logger.info("\nZen MCP Server is not installed.")
        print_python_setup_instructions()
    
    logger.info("\n" + "="*60)
    logger.info("Summary:")
    logger.info("="*60)
    if zen_path:
        logger.info(f"\n✅ zen-mcp-server is installed at: {zen_path}")
        logger.info(f"✅ Server type: {server_type}")
        logger.info("✅ Beverly Knits is configured to use zen-mcp-server")
        logger.info("\n🚀 You're ready to proceed with Phase 2!")
    else:
        logger.info("\n⚠️  zen-mcp-server not found, but Beverly Knits can still work")
        logger.info("   with local ML libraries for all functionality")


if __name__ == "__main__":
    main()