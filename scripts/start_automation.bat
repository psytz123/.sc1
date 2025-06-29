@echo off
echo Starting Zen-MCP Automation System...
echo.

REM Check if zen-mcp-server is running
curl -s http://localhost:5000/version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] zen-mcp-server is not running!
    echo Please start it first:
    echo   cd zen-mcp-server
    echo   .zen_venv\Scripts\python.exe server.py
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
