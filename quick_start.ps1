# Quick Start Script for Zen-MCP Dashboard
# Run this to quickly start the dashboard

Write-Host "🚀 Starting Zen-MCP Dashboard..." -ForegroundColor Cyan

# Check if virtual environment exists
if (!(Test-Path "venv_dashboard")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv_dashboard
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\venv_dashboard\Scripts\Activate.ps1

# Install/update requirements
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements-dashboard.txt

# Create directories if they don't exist
Write-Host "📁 Setting up directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "logs", "reports" | Out-Null

# Copy environment file if it doesn't exist
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "⚙️  Created .env file from template" -ForegroundColor Green
    Write-Host "💡 Edit .env file to customize configuration" -ForegroundColor Yellow
}

# Set Python path
$env:PYTHONPATH = Get-Location

Write-Host ""
Write-Host "✅ Setup complete! Choose dashboard mode:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Terminal mode (Rich TUI in console)" -ForegroundColor Cyan
Write-Host "2. Web mode (Browser interface at http://localhost:8080)" -ForegroundColor Cyan
Write-Host ""
$choice = Read-Host "Enter choice (1 or 2)"

switch ($choice) {
    "1" {
        Write-Host "🖥️  Starting terminal dashboard..." -ForegroundColor Cyan
        python automation/dashboard.py
    }
    "2" {
        Write-Host "🌐 Starting web dashboard at http://localhost:8080..." -ForegroundColor Cyan
        python automation/dashboard.py --mode web --host 0.0.0.0 --port 8080
    }
    default {
        Write-Host "🖥️  Starting terminal dashboard (default)..." -ForegroundColor Cyan
        python automation/dashboard.py
    }
}
