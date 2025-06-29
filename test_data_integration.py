"""
Beverly Knits Data Integration Test Suite
=========================================
Comprehensive tests to validate data integration and relationships
"""

import pandas as pd
import numpy as np
from beverly_knits_data_integration import BeverlyKnitsDataIntegrator
import unittest
from datetime import datetime


class DataIntegrationTests:
    """Test suite for validating data integration"""
    
    def __init__(self, data_path="data/"):
        self.integrator = BeverlyKnitsDataIntegrator(data_path)
        self.test_results = []
        
    def run_all_tests(self):
        """Run all data validation tests"""
        print("="*60)
        print("Beverly Knits Data Integration Test Suite")
        print("="*60)
        
        # Load data first
        self.integrator.load_all_data()
        self.integrator.clean_and_standardize_data()
        
        # Run tests
        self.test_data_loading()
        self.test_key_relationships()
        self.test_data_consistency()
        self.test_calculations()
        self.test_business_rules()
        
        # Print summary
        self.print_test_summary()
        
    def test_data_loading(self):
        """Test that all required files are loaded"""
        print("\n1. Testing Data Loading...")
        
        required_files = [
            'sales_orders', 'yarn_demand_by_style', 'style_bom',
            'yarn_master', 'yarn_inventory', 'suppliers',
            'sales_history'
        ]
        
        for file_key in required_files:
            if file_key in self.integrator.data:
                rows = len(self.integrator.data[file_key])
                self._add_result(f"Load {file_key}", True, f"{rows} rows loaded")
            else:
                self._add_result(f"Load {file_key}", False, "File not loaded")
                
    def test_key_relationships(self):
        """Test that key relationships are valid"""
        print("\n2. Testing Key Relationships...")
        
        # Test 1: Style_ID relationships
        if 'style_bom' in self.integrator.data and 'yarn_demand_by_style' in self.integrator.data:
            bom_styles = set(self.integrator.data['style_bom']['Style_ID'].unique())
            demand_styles = set(self.integrator.data['yarn_demand_by_style']['Style'].unique())
            
            common_styles = bom_styles.intersection(demand_styles)
            coverage = len(common_styles) / len(bom_styles) * 100 if len(bom_styles) > 0 else 0
            
            self._add_result(
                "Style_ID coverage", 
                coverage > 80, 
                f"{coverage:.1f}% of BOM styles have demand data"
            )
            
        # Test 2: Yarn_ID relationships
        if 'style_bom' in self.integrator.data and 'yarn_master' in self.integrator.data:
            bom_yarns = set(self.integrator.data['style_bom']['Yarn_ID'].unique())
            master_yarns = set(self.integrator.data['yarn_master']['Yarn_ID'].unique())
            
            missing_yarns = bom_yarns - master_yarns
            
            self._add_result(
                "Yarn_ID integrity", 
                len(missing_yarns) == 0, 
                f"{len(missing_yarns)} yarns in BOM not found in master"
            )
            
        # Test 3: Supplier relationships
        if 'yarn_master' in self.integrator.data and 'suppliers' in self.integrator.data:
            yarn_suppliers = set(self.integrator.data['yarn_master']['Supplier'].dropna().unique())
            master_suppliers = set(self.integrator.data['suppliers']['Supplier'].unique())
            
            unmatched_suppliers = yarn_suppliers - master_suppliers
            
            self._add_result(
                "Supplier integrity", 
                len(unmatched_suppliers) < 5, 
                f"{len(unmatched_suppliers)} suppliers not in master"
            )
            
    def test_data_consistency(self):
        """Test data consistency and quality"""
        print("\n3. Testing Data Consistency...")
        
        # Test 1: BOM percentages sum to 1
        if 'style_bom' in self.integrator.data:
            bom = self.integrator.data['style_bom']
            style_totals = bom.groupby('Style_ID')['BOM_Percentage'].sum()
            
            # Check if totals are close to 1 (allowing for rounding)
            valid_boms = ((style_totals > 0.99) & (style_totals < 1.01)).sum()
            total_styles = len(style_totals)
            
            self._add_result(
                "BOM percentage totals", 
                valid_boms == total_styles, 
                f"{valid_boms}/{total_styles} styles have valid BOM totals"
            )
            
        # Test 2: Inventory values consistency
        if 'yarn_inventory' in self.integrator.data:
            inv = self.integrator.data['yarn_inventory']
            
            # Check for negative inventory
            negative_inv = (inv['Inventory'] < 0).sum()
            
            self._add_result(
                "Inventory values", 
                negative_inv < 10, 
                f"{negative_inv} yarns have negative inventory"
            )
            
        # Test 3: Date format consistency
        if 'sales_orders' in self.integrator.data:
            orders = self.integrator.data['sales_orders']
            
            # Check if dates can be parsed
            try:
                if 'Ship Date' in orders.columns:
                    valid_dates = pd.to_datetime(orders['Ship Date'], errors='coerce').notna().sum()
                    total_dates = orders['Ship Date'].notna().sum()
                    
                    self._add_result(
                        "Date formats", 
                        valid_dates == total_dates, 
                        f"{valid_dates}/{total_dates} valid ship dates"
                    )
            except:
                self._add_result("Date formats", False, "Error parsing dates")
                
    def test_calculations(self):
        """Test calculation accuracy"""
        print("\n4. Testing Calculations...")
        
        # Create integrated data
        self.integrator.create_integrated_yarn_master()
        self.integrator.calculate_total_yarn_demand()
        
        # Test 1: Demand calculation
        if 'total_yarn_demand' in self.integrator.integrated_data:
            demand = self.integrator.integrated_data['total_yarn_demand']
            
            # Check for reasonable demand values
            valid_demand = ((demand['Total_Demand'] >= 0) & 
                          (demand['Total_Demand'] < 1000000)).sum()
            
            self._add_result(
                "Demand calculations", 
                valid_demand == len(demand), 
                f"{valid_demand}/{len(demand)} yarns have valid demand"
            )
            
        # Test 2: Net requirements
        self.integrator.calculate_net_requirements()
        
        if 'net_requirements' in self.integrator.integrated_data:
            net_req = self.integrator.integrated_data['net_requirements']
            
            # Verify net requirement calculation
            calc_check = net_req['Total_Demand'] - net_req['Available_Supply']
            calc_match = (abs(calc_check - net_req['Net_Requirement']) < 0.01).sum()
            
            self._add_result(
                "Net requirement calc", 
                calc_match == len(net_req), 
                f"{calc_match}/{len(net_req)} calculations correct"
            )
            
    def test_business_rules(self):
        """Test business rule implementation"""
        print("\n5. Testing Business Rules...")
        
        # Generate procurement plan
        self.integrator.generate_procurement_plan()
        
        if 'procurement_plan' in self.integrator.integrated_data:
            proc = self.integrator.integrated_data['procurement_plan']
            
            # Test 1: MOQ compliance
            moq_check = proc[proc['Supplier_MOQ'].notna()]
            moq_compliant = (moq_check['Order_Quantity'] >= moq_check['Supplier_MOQ']).sum()
            
            self._add_result(
                "MOQ compliance", 
                moq_compliant == len(moq_check), 
                f"{moq_compliant}/{len(moq_check)} orders meet MOQ"
            )
            
            # Test 2: Safety stock applied
            safety_applied = (proc['Safety_Stock'] > 0).sum()
            
            self._add_result(
                "Safety stock", 
                safety_applied == len(proc), 
                f"{safety_applied}/{len(proc)} items have safety stock"
            )
            
            # Test 3: Urgency classification
            urgency_set = proc['Urgency'].notna().sum()
            
            self._add_result(
                "Urgency classification", 
                urgency_set == len(proc), 
                f"{urgency_set}/{len(proc)} items have urgency set"
            )
            
    def _add_result(self, test_name, passed, message):
        """Add test result"""
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name} - {message}")
        
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests < total_tests:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")
                    
        # Save results
        results_df = pd.DataFrame(self.test_results)
        results_df.to_csv('test_results.csv', index=False)
        print("\nTest results saved to test_results.csv")


def validate_data_quality():
    """Run data quality validation checks"""
    
    print("\nData Quality Validation Report")
    print("="*60)
    
    integrator = BeverlyKnitsDataIntegrator(data_path="data/")
    integrator.load_all_data()
    
    quality_report = []
    
    for file_key, df in integrator.data.items():
        print(f"\n{file_key}:")
        
        # Basic statistics
        total_rows = len(df)
        total_cols = len(df.columns)
        
        # Check for nulls
        null_counts = df.isnull().sum()
        cols_with_nulls = null_counts[null_counts > 0]
        
        # Check for duplicates
        if not df.empty:
            duplicates = df.duplicated().sum()
        else:
            duplicates = 0
            
        print(f"  - Shape: {total_rows} rows × {total_cols} columns")
        print(f"  - Duplicates: {duplicates}")
        
        if len(cols_with_nulls) > 0:
            print(f"  - Columns with nulls:")
            for col, count in cols_with_nulls.items():
                pct = count / total_rows * 100
                print(f"    • {col}: {count} ({pct:.1f}%)")
                
        quality_report.append({
            'file': file_key,
            'rows': total_rows,
            'columns': total_cols,
            'duplicates': duplicates,
            'null_columns': len(cols_with_nulls)
        })
        
    # Save quality report
    quality_df = pd.DataFrame(quality_report)
    quality_df.to_csv('data_quality_report.csv', index=False)
    print("\nData quality report saved to data_quality_report.csv")


if __name__ == "__main__":
    # Run all tests
    tester = DataIntegrationTests()
    tester.run_all_tests()
    
    # Run data quality validation
    validate_data_quality()