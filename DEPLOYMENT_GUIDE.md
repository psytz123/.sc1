# Zen-MCP Dashboard Deployment Guide

This guide provides multiple deployment options for the Zen-MCP Automation Dashboard.

## Quick Start

For a quick local deployment:

### Windows (PowerShell)
```powershell
.\deploy.ps1 local
```

### Linux/macOS (Bash)
```bash
chmod +x deploy.sh
./deploy.sh local
```

## Deployment Options

### 1. Local Development Deployment

**Requirements:**
- Python 3.8+ (recommended: Python 3.12)
- Virtual environment support

**Steps:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements-dashboard.txt
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start dashboard:**
   ```bash
   # Terminal mode (Rich TUI)
   python automation/dashboard.py
   
   # Web interface mode
   python automation/dashboard.py --mode web --host 0.0.0.0 --port 8080
   ```

### 2. Docker Deployment

**Requirements:**
- Docker
- Docker Compose

**Steps:**

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **Check status:**
   ```bash
   docker-compose ps
   docker-compose logs -f dashboard
   ```

3. **Access dashboard:**
   - Terminal mode: `docker-compose exec dashboard python automation/dashboard.py`
   - Web mode: http://localhost:8080

### 3. Production Deployment (Linux Systemd)

**Requirements:**
- Linux server with systemd
- sudo access

**Steps:**

1. **Run deployment script:**
   ```bash
   sudo ./deploy.sh systemd
   ```

2. **Manage service:**
   ```bash
   # Check status
   systemctl status zen-dashboard
   
   # View logs
   journalctl -u zen-dashboard -f
   
   # Restart service
   sudo systemctl restart zen-dashboard
   ```

### 4. Cloud Deployment

#### Heroku

1. **Prepare files:**
   ```bash
   ./deploy.sh cloud
   ```

2. **Deploy:**
   ```bash
   # Initialize git repo if needed
   git init
   git add .
   git commit -m "Initial dashboard deployment"
   
   # Create Heroku app
   heroku create your-dashboard-name
   
   # Deploy
   git push heroku main
   ```

#### Google Cloud Platform

1. **Prepare files:**
   ```bash
   ./deploy.sh cloud
   ```

2. **Deploy:**
   ```bash
   # Install Google Cloud SDK first
   gcloud app deploy
   ```

#### AWS Elastic Beanstalk

1. **Use the Dockerfile:**
   - Upload the entire project as a ZIP
   - Elastic Beanstalk will automatically detect and use the Dockerfile

#### DigitalOcean App Platform

1. **Create app.yaml:**
   ```yaml
   name: zen-dashboard
   services:
   - name: dashboard
     source_dir: /
     github:
       repo: your-username/your-repo
       branch: main
     run_command: python automation/dashboard.py --mode web --host 0.0.0.0 --port 8080
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     routes:
     - path: /
     envs:
     - key: DASHBOARD_HOST
       value: "0.0.0.0"
     - key: DASHBOARD_PORT
       value: "8080"
   ```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Dashboard Settings
DASHBOARD_HOST=0.0.0.0          # Host to bind to
DASHBOARD_PORT=8080             # Port for web interface
DASHBOARD_REFRESH_INTERVAL=5    # Refresh interval in seconds

# Zen-MCP Server
ZEN_SERVER_URL=http://localhost:5000
ZEN_SERVER_TIMEOUT=5

# File Paths
METRICS_FILE=logs/automation_metrics.json
REPORTS_DIR=reports
LOGS_DIR=logs

# Performance
MAX_RECENT_REPORTS=10
GRAPH_DATA_POINTS=20
```

### Dashboard Modes

1. **Terminal Mode (Default):**
   - Rich text user interface in terminal
   - Real-time updates with interactive display
   - Best for development and monitoring

2. **Web Mode:**
   - HTTP server with web interface
   - REST API endpoints
   - Best for production and remote access

## Dashboard Features

### Terminal Mode
- 📊 Real-time metrics display
- 📈 Performance graphs with plotext
- 🔧 Recent task monitoring
- 🔌 System status indicators
- ⚡ Live updates every 5 seconds

### Web Mode
- 🌐 Web interface accessible via browser
- 📱 Responsive design
- 🔄 Auto-refreshing metrics
- 🛡️ Health check endpoint at `/health`
- 📊 JSON API at `/api/metrics`

## API Endpoints (Web Mode)

- `GET /` - Dashboard web interface
- `GET /health` - Health check endpoint
- `GET /api/metrics` - JSON metrics and reports

## Monitoring and Maintenance

### Log Files
- Dashboard logs: Check systemd journal or container logs
- Metrics file: `logs/automation_metrics.json`
- Reports: `reports/improvement_report_*.json`

### Health Checks
```bash
# Check if dashboard is responding
curl http://localhost:8080/health

# Get metrics via API
curl http://localhost:8080/api/metrics
```

### Troubleshooting

1. **Dashboard not starting:**
   - Check Python version (3.8+ required)
   - Verify all dependencies installed
   - Check if ports are available

2. **Can't connect to Zen-MCP server:**
   - Verify `ZEN_SERVER_URL` in environment
   - Check if zen-mcp-server is running
   - Verify network connectivity

3. **Missing metrics/reports:**
   - Check file permissions on logs/ and reports/ directories
   - Verify automation system is running
   - Check file paths in configuration

4. **Performance issues:**
   - Adjust `DASHBOARD_REFRESH_INTERVAL`
   - Reduce `MAX_RECENT_REPORTS`
   - Check system resources

## Security Considerations

1. **Production deployment:**
   - Change `DASHBOARD_SECRET_KEY` in environment
   - Configure `ALLOWED_HOSTS` appropriately
   - Use reverse proxy (nginx/Apache) for HTTPS
   - Implement authentication if needed

2. **Network security:**
   - Restrict dashboard port access
   - Use VPN for remote access
   - Configure firewall rules

3. **File permissions:**
   - Ensure dashboard user has appropriate file access
   - Protect configuration files
   - Regular security updates

## Scaling

For high-load scenarios:
- Use multiple dashboard instances behind load balancer
- Implement caching for metrics
- Use external metrics storage (Redis/InfluxDB)
- Configure monitoring alerts

## Support

For issues or questions:
1. Check logs for error messages
2. Verify configuration
3. Test connectivity to zen-mcp-server
4. Review this deployment guide

## Version Compatibility

- Python: 3.8+
- Zen-MCP Server: Any version with `/version` endpoint
- Dependencies: See `requirements-dashboard.txt`
