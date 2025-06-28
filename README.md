# 🧶 Beverly Knits - AI Raw Material Planner

> **Intelligent supply chain planning system for textile manufacturing**

An AI-driven raw material planner that intelligently analyzes forecasts, explodes BOMs, evaluates inventory, and recommends optimal raw material purchases that are cost-effective, timely, and risk-aware.

## 🎯 Overview

The Beverly Knits Raw Material Planner implements a comprehensive 6-step planning process:

1. **Forecast Unification** - Aggregates forecasts with source weighting
2. **BOM Explosion** - Translates SKU forecasts to material requirements  
3. **Inventory Netting** - Subtracts available and incoming stock
4. **Procurement Optimization** - Applies safety buffers and MOQ constraints
5. **Supplier Selection** - Chooses optimal suppliers based on multiple criteria
6. **Output Generation** - Provides detailed recommendations with reasoning

## 🚀 Quick Start

### Installation

```bash
# Clone or download the project
# Navigate to project directory

# Install dependencies
pip install -r requirements.txt
```

### Run the Streamlit App

```bash
streamlit run main.py
```

### Run the Test Script

```bash
python test_planner.py
```


### Enhanced Data Integration (Recommended)

For real Beverly Knits data, use the enhanced integration system with automatic data fixes:

```bash
# Run enhanced data integration with automatic fixes
python data_integration_v2.py

# Load and validate the enhanced datasets
python data/enhanced_real_data_loader.py
```

## 📊 Features

### Core Capabilities
- **Multi-source Forecast Processing** with reliability weighting
- **Intelligent BOM Explosion** with unit conversion support
- **Advanced Inventory Netting** considering open POs
- **Smart Supplier Selection** optimizing cost/reliability ratio
- **Risk Assessment** with configurable thresholds
- **Comprehensive Reporting** with executive summaries

### 🔧 Enhanced Data Integration (NEW)
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

### User Interface
- **Interactive Streamlit Dashboard** for easy operation
- **Data Upload** support for CSV files
- **Sample Data Generation** for testing and demos
- **Real-time Configuration** of planning parameters
- **Visual Analytics** with charts and graphs
- **Export Functionality** for CSV and reports

### Business Intelligence
- **Material Categorization** with category-specific rules
- **Supplier Performance Tiers** for quality assessment
- **Seasonal Demand Adjustments** for planning accuracy
- **Critical Material Identification** for priority handling

## 📁 Project Structure

```
beverly-knits-planner/
├── main.py                     # Streamlit application
├── test_planner.py            # Test script
├── requirements.txt           # Dependencies
├── models/                    # Data models
│   ├── forecast.py           # Forecast processing
│   ├── bom.py               # BOM explosion logic
│   ├── inventory.py         # Inventory netting
│   ├── supplier.py          # Supplier selection
│   └── recommendation.py    # Output recommendations
├── engine/                   # Planning engine
│   └── planner.py           # Main planning orchestrator
├── config/                  # Configuration
│   └── settings.py          # Business rules & settings
├── utils/                   # Utilities
│   └── helpers.py           # Helper functions
└── data/                    # Sample data
    └── sample_data_generator.py
```

## 📋 Data Requirements

### Enhanced Data Integration (Recommended)

The system includes an enhanced data integration pipeline that automatically processes Beverly Knits real data:

#### Real Data Files (Beverly Knits)
- `data/Yarn_ID_1.csv` - Yarn master with specifications
- `data/Yarn_ID_Current_Inventory.csv` - Current inventory levels
- `data/Supplier_ID.csv` - Supplier master data
- `data/Style_BOM.csv` - Bill of materials for styles

#### Automatic Data Processing
The enhanced integration system (`data_integration_v2.py`) automatically:
- **Fixes negative inventory balances** → rounds to 0
- **Preserves negative planning balances** (business logic)
- **Adjusts BOM percentages** > 0.99 → rounds to 1.0
- **Cleans cost data** (removes $ symbols, commas)
- **Maps supplier relationships** with proper data types
- **Generates quality reports** documenting all fixes

#### Generated Integrated Files
- `integrated_materials_v2.csv` - Materials with costs and specifications
- `integrated_suppliers_v2.csv` - Supplier-material relationships
- `integrated_inventory_v2.csv` - Inventory with fixed balances
- `integrated_boms_v2.csv` - BOMs with corrected percentages
- `interchangeable_yarns_v2.json` - Interchangeable material groups
- `data_quality_report_v2.txt` - Summary of automatic fixes

### Standard Input Tables (Generic Format)

#### 1. Finished Goods Forecast
- `sku_id` (str) - Product SKU identifier
- `forecast_qty` (int) - Forecasted quantity
- `forecast_date` (date) - Forecast period
- `source` (str) - Source: "sales_order", "prod_plan", "projection"

#### 2. Bill of Materials (BOM)
- `sku_id` (str) - Product SKU identifier
- `material_id` (str) - Raw material identifier
- `qty_per_unit` (float) - Material quantity per product unit
- `unit` (str) - Unit of measure

#### 3. Inventory
- `material_id` (str) - Raw material identifier
- `on_hand_qty` (float) - Current stock quantity
- `unit` (str) - Unit of measure
- `open_po_qty` (float) - Quantity on open purchase orders
- `po_expected_date` (date) - Expected delivery date

#### 4. Suppliers
- `material_id` (str) - Raw material identifier
- `supplier_id` (str) - Supplier identifier
- `cost_per_unit` (float) - Cost per unit
- `lead_time_days` (int) - Lead time in days
- `moq` (int) - Minimum order quantity
- `contract_qty_limit` (int, optional) - Contract quantity limit
- `reliability_score` (float) - Reliability score (0-1)

## ⚙️ Configuration

### Planning Parameters
- **Safety Buffer**: Percentage buffer for safety stock (default: 10%)
- **Max Lead Time**: Maximum acceptable lead time in days (default: 30)
- **Planning Horizon**: Planning period in days (default: 90)

### Source Weights
- **Sales Orders**: 1.0 (highest reliability)
- **Production Plan**: 0.9 (high reliability)
- **Projections**: 0.7 (moderate reliability)

### Risk Thresholds
- **High Risk**: Reliability score < 0.7
- **Medium Risk**: Reliability score < 0.85
- **Low Risk**: Reliability score ≥ 0.85

## 📊 Output Format

### Procurement Recommendations

```json
{
  "material_id": "YARN-B12",
  "recommended_order_qty": 2200,
  "supplier_id": "KNITCO-01", 
  "unit": "lb",
  "expected_lead_time": 10,
  "risk_flag": "low",
  "reasoning": "Net need of 2000 lb plus 10% buffer; supplier selected based on lowest cost/reliability ratio within 14-day lead time.",
  "total_cost": 8800.00,
  "cost_per_unit": 4.00
}
```

## 🧪 Testing

The system includes comprehensive testing capabilities:

```bash
# Run full system test
python test_planner.py

# Test individual components
python -c "from test_planner import test_individual_components; test_individual_components()"
```

## 🔧 Customization

### Business Rules
Modify `config/settings.py` to customize:
- Material categories and safety buffers
- Supplier performance tiers
- Seasonal demand adjustments
- Unit conversion factors

### Planning Logic
Extend the planning engine in `engine/planner.py`:
- Add custom optimization algorithms
- Implement multi-supplier sourcing
- Add EOQ (Economic Order Quantity) optimization

## 📈 Analytics & Reporting

The system provides comprehensive analytics:
- **Forecast Analysis** - SKU demand patterns
- **Material Requirements** - Requirement complexity analysis
- **Inventory Status** - Stock level distribution
- **Supplier Performance** - Cost vs lead time analysis
- **Risk Assessment** - Risk distribution and mitigation

## 🛠️ Advanced Features

### Completed Features ✅
- [x] Multi-supplier sourcing optimization
- [x] Economic Order Quantity (EOQ) integration
- [x] Enhanced data integration with automatic fixes
- [x] Real Beverly Knits data processing
- [x] Comprehensive data quality validation
- [x] Automatic BOM percentage correction
- [x] Inventory balance reconciliation

### Planned Enhancements
- [ ] Machine learning demand forecasting
- [ ] Real-time inventory integration
- [ ] Automated purchase order generation
- [ ] Advanced constraint optimization

## 🔄 Data Integration Workflow

### For Beverly Knits Real Data

1. **Run Enhanced Integration**:
   ```bash
   python data_integration_v2.py
   ```
   This automatically:
   - Loads raw Beverly Knits data files
   - Fixes negative inventory balances (rounds to 0)
   - Preserves negative planning balances
   - Corrects BOM percentages > 0.99 to 1.0
   - Cleans cost data formatting
   - Generates integrated datasets

2. **Validate Data Quality**:
   ```bash
   python data/enhanced_real_data_loader.py
   ```
   This provides:
   - Data quality validation summary
   - Automatic fix verification
   - Planning system object creation

3. **Review Quality Report**:
   Check `data/data_quality_report_v2.txt` for:
   - Summary of automatic fixes applied
   - Data quality metrics
   - Items requiring manual review

### Data Quality Fixes Applied Automatically

| Issue | Fix Applied | Business Logic |
|-------|-------------|----------------|
| Negative inventory balances | Round to 0 | Cannot have negative physical stock |
| Negative planning balances | Preserve | Represents demand vs supply gap |
| BOM percentages > 0.99 | Round to 1.0 | Close to 100% should be exactly 100% |
| Cost formatting | Clean $ and commas | Ensure numeric processing |
| Supplier mapping | Type conversion | Handle text/numeric mismatches |

### Integration Capabilities
- **ERP Systems** - CSV import/export for seamless integration
- **Database Connectivity** - Extensible for direct database connections
- **API Ready** - Modular design supports REST API development
- **Cloud Deployment** - Streamlit Cloud compatible

## 📞 Support

For questions, issues, or feature requests:
1. Review the test script examples
2. Check the configuration documentation
3. Examine the sample data format
4. Review the planning logic in the engine module

## 📄 License

This project is designed as a comprehensive demonstration of AI-driven supply chain planning for textile manufacturing.

---

**Built with**: Python, Streamlit, Pandas, Plotly  
**Version**: 1.0.0  
**Industry**: Textile Manufacturing & Supply Chain Planning