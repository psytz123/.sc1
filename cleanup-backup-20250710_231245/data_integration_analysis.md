# Beverly Knits Data Integration Analysis

## Overview
This document provides a comprehensive analysis of all CSV files and their relationships for the Beverly Knits raw material planning system.

## File Descriptions and Key Fields

### 1. eFab_SO_List.csv (Sales Orders)
- **Purpose**: Active sales orders with customer and product details
- **Key Fields**:
  - `cFVersion`: Product/style code (links to Style_BOM)
  - `Ordered`: Quantity ordered
  - `UOM`: Unit of measure (typically "yds")
  - `Ship Date`: Expected shipping date
  - `On Hold`: HTML toggle for order status
  - `SOP`: Sales order processing number
  - `PO #`: Purchase order number
  - `Sold To/Ship To`: Customer information

### 2. cfab_Yarn_Demand_By_Style.csv (Yarn Requirements by Style)
- **Purpose**: Yarn demand broken down by style and time period
- **Key Fields**:
  - `Style`: Style ID (links to Style_BOM)
  - `Yarn`: Yarn ID (links to Yarn_ID tables)
  - `Percentage`: BOM percentage for the yarn in that style
  - `This Week`, `Week 17-24`, `Later`: Time-phased demand
  - `Total`: Total yarn demand

### 3. Style_BOM.csv (Bill of Materials)
- **Purpose**: Defines yarn composition for each style
- **Key Fields**:
  - `Style_ID`: Unique style identifier
  - `Yarn_ID`: Component yarn identifier
  - `BOM_Percentage`: Percentage of yarn in style (0-1 scale)

### 4. Yarn_ID.csv (Yarn Master Data)
- **Purpose**: Complete yarn specifications and inventory status
- **Key Fields**:
  - `Yarn_ID`: Unique yarn identifier
  - `Supplier`: Supplier name
  - `Description`: Yarn count/specification
  - `Blend`: Fiber composition
  - `Type`: Fiber type
  - `On_Order`: Quantity on order
  - `Allocated`: Quantity allocated
  - `Planning_Ballance`: Available for planning
  - `Cost_Pound`: Cost per pound

### 5. Yarn_ID_Current_Inventory.csv (Current Inventory)
- **Purpose**: Real-time inventory levels and costs
- **Key Fields**:
  - `Yarn_ID`: Unique yarn identifier
  - `Inventory`: Current on-hand quantity
  - `On_Order`: Open purchase orders
  - `Planning_Ballance`: Net available
  - `Cost_Pound`: Current cost per pound
  - `Total_Cost`: Total inventory value

### 6. inventory.csv (Simplified Inventory)
- **Purpose**: Streamlined inventory for upload/integration
- **Key Fields**:
  - `material_id`: Maps to Yarn_ID
  - `on_hand_qty`: Current inventory in pounds
  - `open_po_qty`: Open purchase order quantity
  - `po_expected_date`: Expected receipt date

### 7. Supplier_ID.csv (Supplier Master)
- **Purpose**: Supplier information and constraints
- **Key Fields**:
  - `Supplier_ID`: Unique supplier identifier
  - `Supplier`: Supplier name
  - `Lead_time`: Days to delivery
  - `MOQ`: Minimum order quantity
  - `Type`: Import/Domestic

### 8. Yarn_Demand_2025-06-27_0442.csv (Time-Phased Demand)
- **Purpose**: Detailed weekly yarn demand and supply planning
- **Key Fields**:
  - `Yarn_ID`: Unique yarn identifier
  - `Inventory`: Starting inventory
  - `Total_Demand/Receipt`: Aggregate demand and receipts
  - `Balance`: Net position
  - Weekly demand/receipt/balance columns

### 9. Sales Activity Report.csv (Historical Sales)
- **Purpose**: Historical sales transactions
- **Key Fields**:
  - `Style`: Style sold (links to Style_BOM)
  - `Yds_ordered`: Quantity sold
  - `Invoice Date`: Transaction date
  - `Customer`: Customer name
  - `Unit Price`: Price per yard

## Data Relationships

### Primary Key Relationships:
1. **Style_ID** links:
   - eFab_SO_List.cFVersion → Style_BOM.Style_ID
   - cfab_Yarn_Demand_By_Style.Style → Style_BOM.Style_ID
   - Sales Activity Report.Style → Style_BOM.Style_ID

2. **Yarn_ID** links:
   - Style_BOM.Yarn_ID → Yarn_ID.Yarn_ID
   - cfab_Yarn_Demand_By_Style.Yarn → Yarn_ID.Yarn_ID
   - Yarn_ID_Current_Inventory.Yarn_ID → Yarn_ID.Yarn_ID
   - inventory.material_id → Yarn_ID.Yarn_ID
   - Yarn_Demand_2025-06-27_0442.Yarn_ID → Yarn_ID.Yarn_ID

3. **Supplier** links:
   - Yarn_ID.Supplier → Supplier_ID.Supplier
   - Yarn_ID_Current_Inventory.Supplier → Supplier_ID.Supplier

## Data Flow for Integration

### 1. Demand Calculation Flow:
```
Sales Orders (eFab_SO_List) 
    ↓ [via Style_ID]
Style BOM (Style_BOM)
    ↓ [explode BOM percentages]
Yarn Requirements (cfab_Yarn_Demand_By_Style)
    ↓ [aggregate by Yarn_ID]
Total Yarn Demand
```

### 2. Supply Planning Flow:
```
Total Yarn Demand
    ↓ [compare with]
Current Inventory (Yarn_ID_Current_Inventory/inventory.csv)
    ↓ [calculate net requirements]
Net Requirements
    ↓ [apply supplier constraints]
Supplier Information (Supplier_ID)
    ↓ [generate purchase orders]
Procurement Plan
```

### 3. Time-Phased Planning:
```
Weekly Demand (cfab_Yarn_Demand_By_Style)
    ↓ [merge with]
Weekly Supply (Yarn_Demand_2025-06-27_0442)
    ↓ [calculate weekly balances]
Time-Phased Net Requirements
```

## Integration Considerations

### Data Quality Issues:
1. **Supplier_ID.csv**: Contains "Remove" values that need handling
2. **Yarn_ID tables**: Multiple versions with slightly different structures
3. **Date formats**: Need standardization across files
4. **Unit consistency**: Ensure all quantities are in pounds (lbs)

### Key Calculations:
1. **BOM Explosion**: Style quantity × BOM_Percentage = Yarn requirement
2. **Net Requirements**: Demand - (Inventory + On_Order) = Net requirement
3. **Safety Stock**: Apply buffers based on lead time and variability
4. **MOQ Rounding**: Round up to supplier MOQ constraints

### Critical Fields for Integration:
- **Primary Keys**: Yarn_ID, Style_ID, Supplier_ID
- **Quantities**: Inventory, On_Order, Demand (all in lbs)
- **Dates**: Ship dates, PO expected dates (standardize format)
- **Costs**: Cost_Pound for procurement optimization

## Recommended Integration Architecture

### 1. Data Layer:
- Normalize all CSV files into a unified schema
- Create lookup tables for Yarns, Styles, Suppliers
- Implement fact tables for Orders, Inventory, Demand

### 2. Business Logic Layer:
- BOM explosion engine
- Inventory netting logic
- Supplier selection algorithm
- Safety stock calculations

### 3. Output Layer:
- Procurement recommendations
- Exception reports
- Time-phased planning views
- Cost optimization reports