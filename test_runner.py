#!/usr/bin/env python3
"""
Simplified Test Runner for Beverly Knits
Executes basic test scenarios
"""

import sys
import subprocess
import time
import json
from pathlib import Path

def run_test_suite():
    """Run the basic test suite"""
    
    print("🚀 Beverly Knits Test Suite")
    print("=" * 40)
    
    # Test 1: Quick Health Check
    print("\n1️⃣ Running Quick Health Check...")
    try:
        result = subprocess.run([sys.executable, 'quick_system_health_check.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("   ⏰ Health check timed out")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: System Functionality
    print("\n2️⃣ Running System Functionality Test...")
    try:
        result = subprocess.run([sys.executable, 'system_functionality_test.py'], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("   ✅ System functionality test passed")
        else:
            print("   ❌ System functionality test failed")
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("   ⏰ System functionality test timed out")
    except Exception as e:
        print(f"   ❌ System functionality test error: {e}")
    
    # Test 3: Data Test (if data directory exists)
    if Path('data').exists():
        print("\n3️⃣ Running Data Test...")
        try:
            result = subprocess.run([sys.executable, 'execute_real_data_tests.py'], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("   ✅ Data test passed")
            else:
                print("   ❌ Data test failed")
                print(f"   Output: {result.stdout}")
                print(f"   Error: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            print("   ⏰ Data test timed out")
        except Exception as e:
            print(f"   ❌ Data test error: {e}")
    else:
        print("\n3️⃣ Data Test Skipped (no data directory)")
    
    print("\n" + "=" * 40)
    print("🏁 Test Suite Complete")
    print("=" * 40)

def main():
    """Main execution"""
    
    if not Path('main.py').exists():
        print("❌ Error: Please run from Beverly Knits project directory")
        return 1
    
    run_test_suite()
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)