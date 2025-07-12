#!/bin/bash

# Zen-MCP Dashboard Deployment Script
# This script provides multiple deployment options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "   Zen-MCP Dashboard Deployment Script   "
    echo "=========================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_step "Checking requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
        print_error "Python 3.8+ is required, found $python_version"
        exit 1
    fi
    
    echo "✓ Python $python_version found"
}

setup_virtual_environment() {
    print_step "Setting up virtual environment..."
    
    if [ ! -d "venv_dashboard" ]; then
        python3 -m venv venv_dashboard
    fi
    
    source venv_dashboard/bin/activate
    pip install --upgrade pip
    pip install -r requirements-dashboard.txt
    
    echo "✓ Virtual environment ready"
}

deploy_local() {
    print_step "Deploying locally..."
    
    check_requirements
    setup_virtual_environment
    
    # Create necessary directories
    mkdir -p logs reports
    
    # Set permissions
    chmod +x automation/dashboard.py
    
    print_step "Creating startup script..."
    cat > start_dashboard_local.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv_dashboard/bin/activate
export PYTHONPATH="$(pwd)"
python automation/dashboard.py
EOF
    chmod +x start_dashboard_local.sh
    
    echo -e "${GREEN}✓ Local deployment complete!"
    echo -e "Run: ${BLUE}./start_dashboard_local.sh${NC}"
}

deploy_systemd() {
    print_step "Deploying as systemd service..."
    
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run with sudo for systemd deployment"
        exit 1
    fi
    
    # Create user and directories
    useradd -r -s /bin/false dashboard 2>/dev/null || true
    mkdir -p /opt/zen-dashboard
    cp -r . /opt/zen-dashboard/
    chown -R dashboard:dashboard /opt/zen-dashboard
    
    # Setup virtual environment
    cd /opt/zen-dashboard
    sudo -u dashboard python3 -m venv venv
    sudo -u dashboard venv/bin/pip install --upgrade pip
    sudo -u dashboard venv/bin/pip install -r requirements-dashboard.txt
    
    # Install service
    cp zen-dashboard.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable zen-dashboard
    systemctl start zen-dashboard
    
    echo -e "${GREEN}✓ Systemd service deployment complete!"
    echo "Service status: systemctl status zen-dashboard"
    echo "View logs: journalctl -u zen-dashboard -f"
}

deploy_docker() {
    print_step "Deploying with Docker..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    
    # Build image
    docker build -t zen-dashboard:latest .
    
    # Create docker-compose override if needed
    if [ ! -f docker-compose.override.yml ]; then
        cat > docker-compose.override.yml << 'EOF'
version: '3.8'
services:
  dashboard:
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
EOF
    fi
    
    # Start services
    docker-compose up -d
    
    echo -e "${GREEN}✓ Docker deployment complete!"
    echo "Check status: docker-compose ps"
    echo "View logs: docker-compose logs -f dashboard"
}

deploy_cloud() {
    print_step "Preparing cloud deployment files..."
    
    # Create Heroku Procfile
    echo "web: python automation/dashboard.py" > Procfile
    
    # Create app.yaml for Google Cloud App Engine
    cat > app.yaml << 'EOF'
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
EOF
    
    # Create requirements.txt for cloud
    cp requirements-dashboard.txt requirements.txt
    
    echo -e "${GREEN}✓ Cloud deployment files created!"
    echo "For Heroku: git push heroku main"
    echo "For Google Cloud: gcloud app deploy"
    echo "For AWS: Use Elastic Beanstalk with the Dockerfile"
}

show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Deployment options:"
    echo "  local      Deploy locally with virtual environment"
    echo "  systemd    Deploy as systemd service (requires sudo)"
    echo "  docker     Deploy with Docker and docker-compose"
    echo "  cloud      Prepare files for cloud deployment"
    echo "  help       Show this help message"
    echo ""
}

main() {
    print_banner
    
    case "${1:-local}" in
        local)
            deploy_local
            ;;
        systemd)
            deploy_systemd
            ;;
        docker)
            deploy_docker
            ;;
        cloud)
            deploy_cloud
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
