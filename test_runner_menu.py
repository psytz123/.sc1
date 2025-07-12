#!/usr/bin/env python3
"""
Beverly Knits Test Runner - Interactive Menu
Choose and run different types of tests for your system
"""

import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print the test runner banner"""
    print("🧪 Beverly Knits Test Runner")
    print("=" * 50)
    print("Choose which tests to run for your system")
    print()

def show_menu():
    """Show the test menu options"""
    
    print("📋 Available Tests:")
    print()
    
    print("🏥 SYSTEM HEALTH TESTS:")
    print("   1. Quick System Health Check (30 seconds)")
    print("      ✓ Validates all modules, imports, and core functionality")
    print("      ✓ Tests planning engine and workflow")
    print("      ✓ Perfect for: 'Does my system work?'")
    print()
    
    print("   2. Complete System Functionality Test (2-3 minutes)")
    print("      ✓ Comprehensive module and function testing")
    print("      ✓ Tests all components, methods, and integrations")
    print("      ✓ Perfect for: 'Are all my modules working correctly?'")
    print()
    
    print("📊 DATA TESTS:")
    print("   3. Quick Real Data Test (1 minute)")
    print("      ✓ Loads and validates your actual CSV files")
    print("      ✓ Finds data quality issues quickly")
    print("      ✓ Perfect for: 'Is my data ready to use?'")
    print()
    
    print("⚡ QUICK OPTIONS:")
    print("   A. Run All Essential Tests (System + Data)")
    print("   Q. Quit")
    print()

def run_test(test_choice):
    """Run the selected test"""
    
    test_commands = {
        '1': ('python quick_system_health_check.py', 'Quick System Health Check'),
        '2': ('python system_functionality_test.py', 'Complete System Functionality Test'),
        '3': ('python execute_real_data_tests.py', 'Quick Real Data Test')
    }
    
    if test_choice in test_commands:
        command, test_name = test_commands[test_choice]
        
        print(f"\n🚀 Running: {test_name}")
        print("-" * 50)
        
        try:
            start_time = time.time()
            result = subprocess.run(command.split(), capture_output=False, text=True)
            end_time = time.time()
            
            print(f"\n⏱️  Test completed in {end_time - start_time:.1f} seconds")
            
            if result.returncode == 0:
                print("✅ Test completed successfully!")
            else:
                print(f"⚠️  Test completed with exit code: {result.returncode}")
                
            return result.returncode
            
        except FileNotFoundError:
            print(f"❌ Test file not found: {command}")
            print("   Make sure you're running from the project root directory")
            return 1
            
        except Exception as e:
            print(f"❌ Error running test: {e}")
            return 1
    
    elif test_choice.upper() == 'A':
        # Run essential tests
        print("\n🚀 Running Essential Tests (System + Data)")
        print("=" * 50)
        
        essential_tests = ['1', '3']  # Health check + Quick data test
        
        for test in essential_tests:
            result = run_test(test)
            if result != 0:
                print(f"\n⚠️  Test {test} had issues. Continue anyway? (y/n): ", end="")
                response = input().strip().lower()
                if response != 'y':
                    return result
        
        print("\n🎉 Essential tests completed!")
        return 0
    
    else:
        print(f"❌ Invalid choice: {test_choice}")
        return 1

def main():
    """Main test runner interface"""
    
    print_banner()
    
    while True:
        show_menu()
        
        print("Enter your choice (1-3, A, or Q): ", end="")
        choice = input().strip()
        
        if choice.upper() == 'Q':
            print("\n👋 Goodbye!")
            break
        
        elif choice in ['1', '2', '3', 'A', 'a']:
            result = run_test(choice)
            
            print(f"\n" + "=" * 50)
            if result == 0:
                print("✅ Test completed successfully!")
            else:
                print("⚠️  Test completed with issues - check output above")
            
            print("\nPress Enter to return to menu...", end="")
            input()
            print()
            
        else:
            print(f"\n❌ Invalid choice '{choice}'. Please try again.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test runner interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        sys.exit(1)