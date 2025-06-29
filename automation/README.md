# 🤖 Zen-MCP Automated Code Management System

> **Continuous, intelligent code improvement powered by AI**

This system uses zen-mcp-server to automatically analyze, improve, and maintain your codebase with minimal human intervention.

## 🎯 Overview

The Zen-MCP Automated Code Management System provides:

- **Continuous Code Analysis** - Regular scanning for issues, vulnerabilities, and improvements
- **Automated Refactoring** - AI-driven code improvements and optimizations
- **Security Monitoring** - Automatic detection and fixing of security vulnerabilities
- **Documentation Generation** - Keeps documentation up-to-date automatically
- **Performance Optimization** - Identifies and implements performance improvements
- **ML Model Improvement** - Continuously improves ML models based on new data

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- zen-mcp-server running (see ZEN_MCP_SUCCESS.md)
- Git (optional, for version control features)

### 2. Setup

```bash
# Run the setup script
python setup_automation.py

# Install any missing dependencies
pip install aiohttp gitpython rich plotext schedule
```

### 3. Configuration

Edit the configuration files in the `config` directory:

- `automation_config.json` - Main automation settings
- `scheduler_config.json` - Scheduling and runtime settings

### 4. Start the System

**Windows:**
```batch
start_automation.bat
```

**Linux/Mac:**
```bash
./start_automation.sh
```

### 5. Monitor Progress

**Windows:**
```batch
start_dashboard.bat
```

**Linux/Mac:**
```bash
./start_dashboard.sh
```

## 📋 Features

### 1. Intelligent Code Analysis

The system uses multiple AI models through zen-mcp-server to:

- **Code Review** - Identifies code quality issues, bugs, and improvements
- **Security Audit** - Detects vulnerabilities and security issues
- **Performance Analysis** - Finds optimization opportunities
- **Documentation Check** - Identifies missing or outdated documentation

### 2. Automated Improvements

Based on analysis results, the system automatically:

- **Refactors Code** - Improves code structure and readability
- **Fixes Security Issues** - Patches vulnerabilities with AI-generated fixes
- **Optimizes Performance** - Implements performance improvements
- **Generates Documentation** - Creates and updates docstrings and comments

### 3. ML Model Enhancement

For ML-specific improvements:

- **Model Performance Tracking** - Monitors model accuracy over time
- **Automated Retraining** - Retrains models when performance drops
- **Data Quality Monitoring** - Ensures training data quality
- **Hyperparameter Optimization** - Automatically tunes model parameters

### 4. Safety Features

- **Automatic Backups** - Creates backups before any modifications
- **Git Integration** - Optional automatic commits with descriptive messages
- **Error Recovery** - Graceful handling of failures with rollback capability
- **Working Hours** - Can be configured to run only during specific hours

## ⚙️ Configuration

### automation_config.json

```json
{
  "zen_server_url": "http://localhost:5000",
  "scan_interval_minutes": 30,
  "auto_commit": false,
  "auto_pr": true,
  "excluded_paths": ["__pycache__", ".git", "node_modules"],
  "file_patterns": ["*.py", "*.js", "*.ts"],
  "max_concurrent_tasks": 3,
  "task_priorities": {
    "security": "CRITICAL",
    "bug_fix": "HIGH",
    "performance": "HIGH",
    "refactor": "MEDIUM",
    "documentation": "LOW"
  },
  "ml_improvements": {
    "enabled": true,
    "model_retraining_interval_days": 7,
    "performance_threshold": 0.85,
    "data_collection": true
  }
}
```

### scheduler_config.json

```json
{
  "run_interval_minutes": 30,
  "initial_delay_seconds": 10,
  "max_consecutive_errors": 3,
  "error_retry_delay_minutes": 5,
  "working_hours": {
    "enabled": false,
    "start_hour": 9,
    "end_hour": 17,
    "weekends_enabled": false
  },
  "notifications": {
    "enabled": false,
    "webhook_url": "",
    "notify_on_error": true,
    "notify_on_completion": false
  }
}
```

## 📊 Monitoring

The dashboard provides real-time insights:

- **Metrics Summary** - Total runs, success rate, tasks completed
- **Performance Graphs** - Visual representation of improvements over time
- **Recent Tasks** - List of recent improvements made
- **System Status** - Health of zen-mcp-server and automation system

## 🔧 Advanced Usage

### Custom Task Priorities

Modify task priorities in `automation_config.json`:

```json
"task_priorities": {
  "security": "CRITICAL",
  "custom_task": "HIGH"
}
```

### Webhook Notifications

Enable notifications for Slack, Discord, or custom webhooks:

```json
"notifications": {
  "enabled": true,
  "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "notify_on_error": true,
  "notify_on_completion": true
}
```

### ML Model Improvement

The system can automatically improve ML models by:

1. **Monitoring Performance**
   ```python
   # Automatically tracked metrics
   - Model accuracy
   - Prediction latency
   - Data drift detection
   ```

2. **Retraining Triggers**
   - Performance drops below threshold
   - Significant data drift detected
   - Scheduled interval reached

3. **Improvement Strategies**
   - Hyperparameter tuning
   - Feature engineering
   - Model architecture updates

### Custom Analysis Tools

Add custom analysis by extending the automation system:

```python
async def _analyze_custom_aspect(self, file_path: Path) -> List[AutomationTask]:
    """Custom analysis implementation"""
    # Your custom analysis logic
    pass
```

## 🛡️ Security Considerations

- **API Keys** - Stored securely in zen-mcp-server configuration
- **Code Backups** - All modifications are backed up before changes
- **Audit Trail** - Complete logs of all automated changes
- **Rollback** - Easy restoration from backups if needed

## 📈 Performance Tips

1. **Optimize Scan Patterns**
   - Exclude unnecessary directories
   - Focus on active development areas

2. **Adjust Concurrency**
   - Increase `max_concurrent_tasks` for faster processing
   - Balance with system resources

3. **Schedule Wisely**
   - Run during off-peak hours
   - Adjust interval based on codebase size

## 🐛 Troubleshooting

### Common Issues

1. **"zen-mcp-server not running"**
   - Start zen-mcp-server first
   - Check port 5000 is not blocked

2. **"No improvements found"**
   - Check file patterns in config
   - Verify excluded paths
   - Review logs for errors

3. **"High memory usage"**
   - Reduce `max_concurrent_tasks`
   - Increase scan interval
   - Exclude large files

### Debug Mode

Enable detailed logging:

```python
# In automation/zen_code_automation.py
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

To extend the automation system:

1. Add new analysis tools in `zen_code_automation.py`
2. Implement task executors for new improvement types
3. Update configuration schemas
4. Add tests for new features

## 📝 Best Practices

1. **Start Conservative**
   - Begin with `auto_commit: false`
   - Review changes before enabling automation

2. **Monitor Regularly**
   - Check dashboard daily initially
   - Review improvement reports

3. **Customize for Your Needs**
   - Adjust file patterns
   - Set appropriate priorities
   - Configure working hours

4. **Backup Strategy**
   - Regular full codebase backups
   - Version control integration
   - Test restore procedures

## 🎉 Benefits

- **Consistent Code Quality** - Maintains high standards automatically
- **Security Compliance** - Continuous vulnerability scanning and fixing
- **Time Savings** - Automates repetitive improvement tasks
- **Knowledge Capture** - AI learns from your codebase patterns
- **Continuous Improvement** - Code gets better over time

## 📚 Additional Resources

- [zen-mcp-server Documentation](https://github.com/zen-mcp/zen-mcp-server)
- [Automation API Reference](automation/API_REFERENCE.md)
- [Custom Extensions Guide](automation/EXTENSIONS.md)

---

**Remember**: This system is designed to augment, not replace, human developers. Always review significant changes and maintain oversight of the automation process.