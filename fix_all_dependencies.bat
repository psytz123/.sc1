@echo off
echo Fixing ALL zen-mcp-server dependencies...
echo ==========================================
echo.

cd /d "C:\Users\psytz\.sc1\zen-mcp-server"

echo Activating virtual environment...
call .zen_venv\Scripts\activate.bat

echo.
echo Installing all required packages...
pip install python-dotenv google-generativeai aiohttp pydantic requests openai anthropic

echo.
echo Checking for requirements.txt...
if exist requirements.txt (
    echo Installing from requirements.txt...
    pip install -r requirements.txt
)

echo.
echo Installed packages:
pip list

echo.
echo Testing imports...
python -c "import dotenv; import google.generativeai; print('✓ All imports successful!')"

echo.
echo Testing server...
python server.py --help

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo ✓ SUCCESS! All dependencies installed.
    echo ==========================================
    echo.
    echo Getting Claude Desktop configuration...
    python server.py -c
) else (
    echo.
    echo ✗ ERROR: Server still has issues.
)

pause