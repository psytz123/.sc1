# Zen-MCP Dashboard Deployment Script for Windows PowerShell
# This script provides multiple deployment options for Windows

param(
    [Parameter(Position=0)]
    [ValidateSet("local", "docker", "cloud", "help")]
    [string]$DeploymentType = "local"
)

# Colors for output (if supported)
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

function Write-Banner {
    Write-Host "==========================================" -ForegroundColor $InfoColor
    Write-Host "   Zen-MCP Dashboard Deployment Script   " -ForegroundColor $InfoColor
    Write-Host "==========================================" -ForegroundColor $InfoColor
}

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor $SuccessColor
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $WarningColor
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $ErrorColor
}

function Test-Requirements {
    Write-Step "Checking requirements..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python not found"
        }
        Write-Host "✓ $pythonVersion found" -ForegroundColor $SuccessColor
    }
    catch {
        Write-Error "Python 3 is required but not installed"
        exit 1
    }
    
    # Check Python version
    $version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ([version]$version -lt [version]"3.8") {
        Write-Error "Python 3.8+ is required, found $version"
        exit 1
    }
}

function Setup-VirtualEnvironment {
    Write-Step "Setting up virtual environment..."
    
    if (!(Test-Path "venv_dashboard")) {
        python -m venv venv_dashboard
    }
    
    & .\venv_dashboard\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements-dashboard.txt
    
    Write-Host "✓ Virtual environment ready" -ForegroundColor $SuccessColor
}

function Deploy-Local {
    Write-Step "Deploying locally..."
    
    Test-Requirements
    Setup-VirtualEnvironment
    
    # Create necessary directories
    New-Item -ItemType Directory -Force -Path "logs", "reports" | Out-Null
    
    Write-Step "Creating startup script..."
    $startupScript = @"
# Zen-MCP Dashboard Startup Script
# Activate virtual environment and start dashboard

Set-Location `$PSScriptRoot
& .\venv_dashboard\Scripts\Activate.ps1
`$env:PYTHONPATH = Get-Location
python automation/dashboard.py
"@
    
    $startupScript | Out-File -FilePath "start_dashboard_local.ps1" -Encoding UTF8
    
    Write-Host "✓ Local deployment complete!" -ForegroundColor $SuccessColor
    Write-Host "Run: " -NoNewline
    Write-Host ".\start_dashboard_local.ps1" -ForegroundColor $InfoColor
}

function Deploy-Docker {
    Write-Step "Deploying with Docker..."
    
    # Check if Docker is installed
    try {
        docker --version | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker not found"
        }
    }
    catch {
        Write-Error "Docker is required but not installed"
        exit 1
    }
    
    # Build image
    docker build -t zen-dashboard:latest .
    
    # Create docker-compose override if needed
    if (!(Test-Path "docker-compose.override.yml")) {
        $override = @"
version: '3.8'
services:
  dashboard:
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
"@
        $override | Out-File -FilePath "docker-compose.override.yml" -Encoding UTF8
    }
    
    # Start services
    docker-compose up -d
    
    Write-Host "✓ Docker deployment complete!" -ForegroundColor $SuccessColor
    Write-Host "Check status: docker-compose ps"
    Write-Host "View logs: docker-compose logs -f dashboard"
}

function Deploy-Cloud {
    Write-Step "Preparing cloud deployment files..."
    
    # Create Heroku Procfile
    "web: python automation/dashboard.py" | Out-File -FilePath "Procfile" -Encoding UTF8 -NoNewline
    
    # Create app.yaml for Google Cloud App Engine
    $appYaml = @"
runtime: python312
env: standard

instance_class: F1

automatic_scaling:
  min_instances: 1
  max_instances: 3

env_variables:
  PYTHONPATH: /srv

handlers:
- url: /.*
  script: auto
"@
    $appYaml | Out-File -FilePath "app.yaml" -Encoding UTF8
    
    # Create requirements.txt for cloud
    Copy-Item "requirements-dashboard.txt" "requirements.txt"
    
    Write-Host "✓ Cloud deployment files created!" -ForegroundColor $SuccessColor
    Write-Host "For Heroku: git push heroku main"
    Write-Host "For Google Cloud: gcloud app deploy"
    Write-Host "For AWS: Use Elastic Beanstalk with the Dockerfile"
}

function Show-Help {
    Write-Host "Usage: .\deploy.ps1 [OPTION]"
    Write-Host ""
    Write-Host "Deployment options:"
    Write-Host "  local      Deploy locally with virtual environment (default)"
    Write-Host "  docker     Deploy with Docker and docker-compose"
    Write-Host "  cloud      Prepare files for cloud deployment"
    Write-Host "  help       Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy.ps1"
    Write-Host "  .\deploy.ps1 local"
    Write-Host "  .\deploy.ps1 docker"
}

function Main {
    Write-Banner
    
    switch ($DeploymentType) {
        "local" {
            Deploy-Local
        }
        "docker" {
            Deploy-Docker
        }
        "cloud" {
            Deploy-Cloud
        }
        "help" {
            Show-Help
        }
        default {
            Write-Error "Unknown option: $DeploymentType"
            Show-Help
            exit 1
        }
    }
}

# Run main function
Main
