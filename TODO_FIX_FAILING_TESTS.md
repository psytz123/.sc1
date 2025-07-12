# TODO: Fix Failing Tests - MaterialPlanner Implementation

## 🎯 Priority 1: Core MaterialPlanner Class Implementation

### 1. Create MaterialPlanner Class
- [ ] **File**: `engine/planner.py`
- [ ] **Issue**: Tests expect `MaterialPlanner` class but only `RawMaterialPlanner` exists
- [ ] **Solution**: Create `MaterialPlanner` class or alias existing class
- [ ] **Methods Required**:
  - `unify_forecasts(forecast_data)` - Process and unify forecast data
  - `explode_bom(bom_data, forecast_data)` - Explode BOM requirements  
  - `net_inventory(requirements, inventory)` - Calculate net requirements
  - `has_errors()` - Check for validation errors

### 2. Implement Individual Step Methods
- [ ] **Method**: `unify_forecasts(forecast_data: pd.DataFrame) -> pd.DataFrame`
  - [ ] Handle empty DataFrame input
  - [ ] Process single forecast source (sales_order, demand_forecast, production_plan)
  - [ ] Handle multiple forecast sources with weighting
  - [ ] Validate forecast dates and resolve conflicts
  - [ ] Handle invalid source types gracefully
  - [ ] Process zero, negative, and extremely large quantities
  - [ ] Maintain decimal precision
  - [ ] Handle duplicate SKUs
  - [ ] Return unified forecast with source_weight column

- [ ] **Method**: `explode_bom(bom_data: pd.DataFrame, forecast_data: pd.DataFrame) -> pd.DataFrame`
  - [ ] Handle standard BOM processing
  - [ ] Validate BOM percentages (99%, 101% cases)
  - [ ] Support single material BOMs
  - [ ] Handle zero percentage materials
  - [ ] Process missing BOM scenarios
  - [ ] Detect and handle circular BOM references
  - [ ] Implement unit conversion logic
  - [ ] Support style-to-yarn explosion
  - [ ] Handle fractional requirements
  - [ ] Return material requirements

- [ ] **Method**: `net_inventory(requirements: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame`
  - [ ] Handle negative inventory balances
  - [ ] Calculate net requirements (gross - on_hand)
  - [ ] Handle missing inventory records
  - [ ] Support different units of measure
  - [ ] Return net requirements with proper calculations

- [ ] **Method**: `has_errors() -> bool`
  - [ ] Track validation errors during processing
  - [ ] Return True if any errors occurred
  - [ ] Implement error state management

## 🎯 Priority 2: Error Handling & Validation

### 3. Enhanced Error Handling
- [ ] **Class**: Add error tracking to MaterialPlanner
- [ ] **Properties**:
  - `_errors: List[str]` - Track validation errors
  - `_warnings: List[str]` - Track warnings
- [ ] **Methods**:
  - `add_error(message: str)` - Add error to tracking
  - `add_warning(message: str)` - Add warning to tracking
  - `clear_errors()` - Reset error state
  - `get_errors() -> List[str]` - Return all errors
  - `get_warnings() -> List[str]` - Return all warnings

### 4. Input Validation
- [ ] **Forecast Data Validation**:
  - [ ] Check required columns: sku_id, forecast_qty, forecast_date, source
  - [ ] Validate data types
  - [ ] Check for null values
  - [ ] Validate date formats
  - [ ] Validate source types

- [ ] **BOM Data Validation**:
  - [ ] Check required columns: sku_id, material_id, qty_per_unit
  - [ ] Validate percentage sums per SKU
  - [ ] Check for negative quantities
  - [ ] Validate material IDs

- [ ] **Inventory Data Validation**:
  - [ ] Check required columns: material_id, on_hand_qty, unit
  - [ ] Validate numeric quantities
  - [ ] Check for missing materials

## 🎯 Priority 3: Data Processing Logic

### 5. Forecast Unification Logic
- [ ] **Source Weighting System**:
  - [ ] sales_order: 0.4 weight
  - [ ] demand_forecast: 0.6 weight  
  - [ ] production_plan: 0.3 weight
  - [ ] Configurable weights via config

- [ ] **Date Conflict Resolution**:
  - [ ] Aggregate by SKU and date
  - [ ] Apply source weights
  - [ ] Handle date ranges

- [ ] **Data Quality Checks**:
  - [ ] Flag extreme values
  - [ ] Handle missing dates
  - [ ] Process invalid quantities

### 6. BOM Explosion Logic
- [ ] **Standard BOM Processing**:
  - [ ] Multiply forecast qty by material qty_per_unit
  - [ ] Sum requirements by material_id
  - [ ] Handle multi-level BOMs

- [ ] **Percentage Correction**:
  - [ ] Auto-correct BOMs summing to 99%
  - [ ] Warning for BOMs over 101%
  - [ ] Normalize percentages

- [ ] **Special Cases**:
  - [ ] Single material BOMs (qty_per_unit = 1.0)
  - [ ] Zero percentage materials (exclude from calculations)
  - [ ] Missing BOM records (flag as error)

### 7. Inventory Netting Logic
- [ ] **Net Calculation**:
  - [ ] Net = Gross Requirement - On Hand Quantity
  - [ ] Handle negative inventory as additional requirement
  - [ ] Apply safety stock buffers

- [ ] **Unit Conversion**:
  - [ ] Convert between different units of measure
  - [ ] Support yards, pounds, pieces, etc.
  - [ ] Maintain conversion factors

## 🎯 Priority 4: Integration & Testing

### 8. Update Import Structure
- [ ] **File**: `engine/__init__.py`
- [ ] **Action**: Export MaterialPlanner class
- [ ] **Code**: `from .planner import MaterialPlanner`

### 9. Configuration Integration
- [ ] **File**: `config/settings.py`
- [ ] **Add Settings**:
  - [ ] `source_weights: Dict[str, float]`
  - [ ] `safety_stock_percentage: float`
  - [ ] `bom_tolerance: float`
  - [ ] `enable_circular_bom_detection: bool`

### 10. Test Data Setup
- [ ] **Create Test Data Files**:
  - [ ] `test_forecasts.csv` - Sample forecast data
  - [ ] `test_boms.csv` - Sample BOM data
  - [ ] `test_inventory.csv` - Sample inventory data

### 11. Method Signatures
- [ ] **Ensure Compatibility**:
```python
class MaterialPlanner:
    def __init__(self, config=None):
        pass
    
    def unify_forecasts(self, forecast_data: pd.DataFrame) -> pd.DataFrame:
        pass
    
    def explode_bom(self, bom_data: pd.DataFrame, forecast_data: pd.DataFrame) -> pd.DataFrame:
        pass
    
    def net_inventory(self, requirements: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
        pass
    
    def has_errors(self) -> bool:
        pass
```

## 🎯 Priority 5: Code Quality & Documentation

### 12. Documentation
- [ ] **Add docstrings** to all methods
- [ ] **Add type hints** for all parameters
- [ ] **Add usage examples** in docstrings
- [ ] **Document error conditions** and return values

### 13. Logging Integration
- [ ] **Add logging** to all major operations
- [ ] **Log warnings** for data quality issues
- [ ] **Log errors** for validation failures
- [ ] **Log success** metrics and timing

### 14. Performance Optimization
- [ ] **Add caching** for repeated calculations
- [ ] **Optimize DataFrame operations**
- [ ] **Add progress indicators** for large datasets
- [ ] **Memory management** for large files

## 🎯 Estimated Timeline

| Priority | Tasks | Estimated Time |
|----------|-------|---------------|
| 1 | Core MaterialPlanner Class | 4-6 hours |
| 2 | Error Handling & Validation | 2-3 hours |
| 3 | Data Processing Logic | 3-4 hours |
| 4 | Integration & Testing | 1-2 hours |
| 5 | Code Quality & Documentation | 1-2 hours |
| **Total** | **All Tasks** | **11-17 hours** |

## 🎯 Success Criteria

- [ ] All 20 failing tests pass
- [ ] Code coverage increases from 39% to >80%
- [ ] No breaking changes to existing functionality
- [ ] All edge cases handled gracefully
- [ ] Comprehensive error messaging
- [ ] Performance meets requirements (<5 seconds for 1000 SKUs)

## 🎯 Implementation Order

1. **Start with Priority 1** - Core MaterialPlanner class
2. **Implement basic methods** - Get tests passing first
3. **Add error handling** - Make it robust
4. **Optimize performance** - Make it fast
5. **Add documentation** - Make it maintainable

This plan will systematically address all failing tests while maintaining code quality and ensuring robust error handling.