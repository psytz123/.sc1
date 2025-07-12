
# Beverly Knits Live Data API Documentation

## LiveDataIntegrator Class

### Purpose
Integrates live CSV files directly into the planning system.

### Key Methods

#### `load_all_live_data() -> Dict[str, Any]`
Loads all live CSV files and returns structured data.

#### `convert_to_planning_format() -> Dict[str, List]`
Converts live data to standard planning system format.

#### `generate_planning_inputs() -> Dict[str, Any]`
Generates complete planning inputs with validation.

## LiveDataPlanner Class

### Purpose
Planning engine optimized for live data format.

### Key Methods

#### `run_full_planning_cycle() -> Dict[str, Any]`
Executes complete planning cycle with live data.

#### `export_planning_results(output_path: str) -> Dict[str, str]`
Exports planning results to multiple formats.

## Live Data Models

### YarnDemandByStyle
Represents yarn demand data from cfab_Yarn_Demand_By_Style.csv

### SalesOrder
Represents sales order data from eFab_SO_List.csv

### StyleBOM
Represents BOM data from Style_BOM.csv

### InventoryItem
Represents inventory data from Inventory.csv

### SupplierInfo
Represents supplier data from Supplier_ID.csv

### YarnMaster
Represents yarn master data from Yarn_ID.csv

## Usage Examples

```python
# Load and process live data
integrator = LiveDataIntegrator()
planning_inputs = integrator.generate_planning_inputs()

# Run planning
planner = LiveDataPlanner()
results = planner.run_full_planning_cycle()

# Export results
exported_files = planner.export_planning_results()
```
