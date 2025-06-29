@echo off
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
call venv_tf\Scripts\activate.bat

echo Installing TensorFlow and dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-deep-learning.txt

echo.
echo Setup complete! To use this environment:
echo   venv_tf\Scripts\activate
