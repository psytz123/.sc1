# 🧶 Beverly Knits - AI Raw Material Planner

> **Intelligent supply chain planning system for textile manufacturing**

An AI-driven raw material planner that intelligently analyzes forecasts, explodes BOMs, evaluates inventory, and recommends optimal raw material purchases that are cost-effective, timely, and risk-aware.

## 📋 Executive Summary

The Beverly Knits AI Raw Material Planner is a sophisticated supply chain planning system for textile manufacturing. The core planning engine is **100% complete and production-ready**, implementing a 6-step intelligent planning process for raw material procurement optimization.

**Current State**: 
- ✅ Core planning engine is **fully functional** and tested
- ✅ Web interface (Streamlit) is **complete** 
- ✅ Data integration pipeline is **operational**
- ✅ EOQ and multi-supplier optimization **implemented**
- ✅ Codebase has been cleaned and refactored for maintainability.
- 🟡 Sales integration is **partially implemented** with enhancements complete
- 🟡 Style-to-Yarn BOM integration is **complete** and tested

---

## 🎯 System Overview

The Beverly Knits Raw Material Planner implements a comprehensive 6-step planning process:

1.  **Forecast Unification** - Aggregates forecasts with source weighting
2.  **BOM Explosion** - Translates SKU forecasts to material requirements
3.  **Inventory Netting** - Subtracts available and incoming stock
4.  **Procurement Optimization** - Applies safety buffers and MOQ constraints
5.  **Supplier Selection** - Chooses optimal suppliers based on multiple criteria
6.  **Output Generation** - Provides detailed recommendations with reasoning

---

## 📊 Features

### Core Capabilities
- **Multi-source Forecast Processing** with reliability weighting
- **Intelligent BOM Explosion** with unit conversion support
- **Advanced Inventory Netting** considering open POs
- **Smart Supplier Selection** optimizing cost/reliability ratio
- **Risk Assessment** with configurable thresholds
- **Comprehensive Reporting** with executive summaries
- **EOQ (Economic Order Quantity) optimization** integrated
- **Multi-supplier sourcing** with risk diversification

### Enhanced Data Integration
- **Automatic Data Quality Fixes**:
  - Negative inventory balances automatically rounded to 0
  - Negative planning balances preserved (business logic)
  - BOM percentages > 0.99 automatically adjusted to 1.0
  - Cost data cleaning (removes $ symbols and commas)
- **Real Data Processing**:
  - Beverly Knits yarn master integration
  - Supplier relationship mapping
  - Inventory balance reconciliation
  - BOM percentage validation and correction
- **Quality Reporting**:
  - Comprehensive data quality reports
  - Automatic fix documentation
  - Data validation summaries

### Zen-MCP Server Integration (Optional)
- **Multi-Model Consensus:** Get opinions from multiple AI models (Claude, Gemini, GPT-4).
- **Specialized Models:** Use different models for different tasks.
- **Advanced Code Generation:** Leverage Claude's coding capabilities.
- **AI Orchestration:** Coordinate multiple AIs for complex tasks.
- The application can run with or without the Zen-MCP server.

### User Interface
- **Interactive Streamlit Dashboard** for easy operation
- **Data Upload** support for CSV files
- **Sample Data Generation** for testing and demos
- **Real-time Configuration** of planning parameters
- **Visual Analytics** with charts and graphs
- **Export Functionality** for CSV and reports

---

## 📁 Project Structure

```
beverly-knits/
├── config/          # Configuration files
├── data/            # Data files and samples
├── engine/          # Core planning engine
├── models/          # Data models
├── utils/           # Utility functions
├── tests/           # All test files (organized)
├── scripts/         # Utility and maintenance scripts
│   └── fixes/       # One-time fix scripts
├── main.py          # Main Streamlit application
└── README.md        # Project documentation
```

---

## ⚙️ Setup and Installation

### 1. Environment Setup (Python 3.12)

A Python 3.12 virtual environment is recommended.

**For PowerShell:**
```powershell
# Create and activate the environment
python -m venv venv_py312
.\venv_py312\Scripts\Activate.ps1
```

**For Command Prompt:**
```cmd
# Create and activate the environment
python -m venv venv_py312
venv_py312\Scripts\activate.bat
```

### 2. Install Dependencies

Install the required packages using the appropriate requirements file.

```bash
# For the core application
pip install -r requirements-core.txt

# For the dashboard
pip install -r requirements-dashboard.txt

# For all features including ML and development
pip install -r requirements.txt
```

---

## 🚀 Usage

### Running the Streamlit Application

To start the main web interface:

```bash
streamlit run main.py
```

### Running Data Integration

To process raw data files with automatic quality fixes:

```bash
python data_integration_v2.py
```

To apply specific fixes to the BOM data:

```bash
python scripts/fixes/fix_bom_integration.py
```

### Running Tests

To verify the core functionality:

```bash
pytest
```

---

## 📦 Deployment

Multiple deployment options are available.

### 1. Local Development

Run the dashboard directly for local development.

```bash
# Terminal mode (Rich TUI)
python automation/dashboard.py

# Web interface mode
python automation/dashboard.py --mode web --host 0.0.0.0 --port 8080
```

### 2. Docker Deployment

Use Docker and Docker Compose for a containerized deployment.

```bash
docker-compose up -d
```
The web interface will be available at `http://localhost:8080`.

### 3. Production Deployment (Linux Systemd)

For production environments on Linux, a `systemd` service is provided.

```bash
# Run the deployment script
sudo ./deploy.sh systemd

# Manage the service
systemctl status zen-dashboard
journalctl -u zen-dashboard -f
```

---

## ✨ Codebase Cleanup

The codebase has undergone a significant cleanup to improve quality, organization, and maintainability. Key improvements include:
- **Dead Code Removal:** Removed duplicate files and organized test and utility scripts.
- **Code Style Improvements:** Standardized import ordering, fixed formatting, and removed unused imports.
- **Improved Project Structure:** Reorganized files and folders for clarity.
- **Documentation:** Created comprehensive documentation for the cleanup process and project structure.

---

## 🔮 Future Work

- **Complete Type Hints:** Add type hints to remaining functions and use `mypy` for type checking.
- **Standardize Naming Conventions:** Convert remaining camelCase to snake_case for consistency.
- **Enhance Testing:** Increase test coverage, add integration tests, and set up continuous integration.
- **Documentation Improvements:** Complete docstrings for all public functions and update API documentation.
- **Configuration Cleanup:** Review `.env.example` for unused variables and consolidate configuration settings.