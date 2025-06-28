# Yarn Demand Analysis Summary

## File: Yarn_Demand_2025-06-27_0442.csv

### Structure Overview
The CSV file contains yarn demand and receipt planning data with the following columns:

1. **Yarn_ID**: Unique identifier for each yarn type
2. **Inventory**: Current inventory level (can be negative, indicating shortage)
3. **Total_Demand**: Total demand across all weeks
4. **Total_Receipt**: Total expected receipts across all weeks
5. **Balance**: Net balance (Inventory + Total_Receipt - Total_Demand)
6. **Past_Due_Receipts**: Overdue receipts that haven't arrived yet

### Weekly Breakdown (Weeks 27-34 + Later)
For each week, the file tracks:
- **Demand**: Expected yarn consumption for that week
- **Receipts**: Expected yarn deliveries for that week
- **Balance**: Running balance after that week's transactions

### Key Insights

1. **187 Yarn Types**: The file tracks 187 different yarn IDs

2. **Inventory Status**:
   - Many yarns show negative inventory (shortages)
   - Examples: Yarn 19050 (-634.1), Yarn 18870 (-670.6)
   - Some yarns have substantial positive inventory

3. **Receipt Planning**:
   - Large receipts scheduled for various yarns
   - Past due receipts indicate supply chain delays
   - Receipt timing varies by yarn type

4. **Demand Patterns**:
   - Some yarns have immediate demand ("This Week")
   - Others have demand spread across multiple weeks
   - "Demand Later" column captures long-term requirements

5. **Critical Yarns** (with significant negative balances):
   - Yarn 18870: Balance of -14,566.6
   - Yarn 11896: Balance of -339.5 with 3,832.5 past due
   - Yarn 18884: Balance of -5,944.9 with 14,617.6 past due

### Planning Considerations

1. **Urgent Orders Needed**: Yarns with negative balances and no scheduled receipts
2. **Supply Risk**: Yarns with large past-due receipts indicate supplier reliability issues
3. **Overstocked Items**: Yarns with large positive balances may tie up working capital
4. **Weekly Planning**: The week-by-week breakdown enables precise production scheduling

This data provides the foundation for:
- Raw material procurement decisions
- Production scheduling optimization
- Supplier performance evaluation
- Working capital management