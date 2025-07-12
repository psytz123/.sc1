
# Beverly Knits Live Data Format Guide

## Overview
This guide covers the exact format and structure of Beverly Knits live CSV data files and how the planning system processes them.

## Live Data Files

### 1. cfab_Yarn_Demand_By_Style.csv
**Purpose**: Yarn demand by style with weekly breakdown
**Format**: Style, Yarn, Percentage, This Week, Week 17-24, Later, Total
**Special Processing**:
- Handles comma-separated numbers (e.g., "1,919.4")
- Percentage is in 0-100 scale
- Weekly columns may be empty

### 2. eFab_SO_List.csv
**Purpose**: Sales orders with customer and product details
**Format**: Status, CSR, Unit Price, Quoted Date, cFVersion, fBase, On Hold, Ordered, UOM, SOP, PO #, Sold To, Ship To, Ship Date
**Special Processing**:
- Unit Price in format "$5.95 (yds)"
- On Hold contains HTML toggle content
- cFVersion is the style/product code

### 3. Style_BOM.csv
**Purpose**: Bill of Materials defining yarn composition
**Format**: Style_ID, Yarn_ID, BOM_Percentage
**Special Processing**:
- BOM_Percentage is in 0-1 scale
- Percentages should sum to 1.0 per style

### 4. Inventory.csv
**Purpose**: Current inventory levels
**Format**: style_id, yds, lbs
**Special Processing**:
- Handles comma-separated numbers
- Both yds and lbs columns may contain formatted numbers

### 5. Supplier_ID.csv
**Purpose**: Supplier master data with constraints
**Format**: Supplier_ID, Supplier, Lead_time, MOQ, Type
**Special Processing**:
- "Remove" values indicate inactive suppliers
- Lead_time and MOQ may be "Remove" or numeric

### 6. Yarn_ID.csv
**Purpose**: Yarn master data with costs and inventory
**Format**: Yarn_ID, Supplier, Description, Blend, Type, Color, Desc_1, Desc_2, Desc_3, On_Order, Allocated, Planning_Ballance, Cost_Pound, Total_Cast
**Special Processing**:
- Cost_Pound in format "$5.09 "
- Total_Cast uses parentheses for negatives: "($2,183.40)"
- Planning_Ballance can be negative

## Data Processing Flow

1. **Load**: Read CSV files with proper encoding
2. **Parse**: Handle formatted numbers, currency, HTML
3. **Validate**: Check data quality and consistency
4. **Convert**: Transform to planning system format
5. **Plan**: Execute planning algorithms
6. **Export**: Generate recommendations and reports

## Key Features

- **Automatic Format Detection**: System recognizes and handles all formatting
- **Cross-Validation**: Validates consistency between BOM files
- **Error Handling**: Graceful handling of missing or invalid data
- **Live Updates**: No preprocessing required - use files directly

## Best Practices

1. Maintain exact column names and formats
2. Use consistent style and yarn IDs across files
3. Ensure BOM percentages sum correctly
4. Keep supplier data up to date
5. Validate data before major planning runs
