@echo off
echo Activating Python 3.12 virtual environment...
call venv_py312\Scripts\activate.bat
echo.
echo Python 3.12 environment activated!
echo Python version:
python --version
echo.
echo To deactivate, type: deactivate
cmd /k