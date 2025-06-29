# PowerShell script to activate Python 3.12 virtual environment
Write-Host "Activating Python 3.12 virtual environment..." -ForegroundColor Green
& ".\venv_py312\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Python 3.12 environment activated!" -ForegroundColor Green
Write-Host "Python version:" -ForegroundColor Yellow
python --version
Write-Host ""
Write-Host "To deactivate, type: deactivate" -ForegroundColor Cyan