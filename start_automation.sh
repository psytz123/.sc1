#!/bin/bash
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
