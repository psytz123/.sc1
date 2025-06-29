@echo off
echo Fixing zen-mcp-server dependencies...
echo.

cd /d "C:\Users\psytz\zen-mcp-server"

echo Activating virtual environment...
call .zen_venv\Scripts\activate.bat

echo.
echo Installing Google Generative AI...
pip install google-generativeai

echo.
echo Installing all requirements...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo No requirements.txt found, installing common dependencies...
    pip install google-generativeai aiohttp pydantic
)

echo.
echo Testing server...
python server.py --help

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS! Server is working.
    echo.
    echo Getting Claude Desktop configuration...
    python server.py -c
    echo.
    echo Copy the above configuration to:
    echo %APPDATA%\Claude\claude_desktop_config.json
) else (
    echo.
    echo ERROR: Server still has issues.
    echo Please check the error messages above.
)

pause