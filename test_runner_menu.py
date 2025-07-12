#!/usr/bin/env python3
"""
Beverly Knits Test Runner Menu
Interactive test selection
"""

import sys
import subprocess
from pathlib import Path

def show_menu():
    """Show test menu"""
    
    print("🧪 Beverly Knits Test Runner")
    print("=" * 40)
    print("Choose which tests to run:")
    print()
    print("1. Quick System Health Check")
    print("2. System Functionality Test")
    print("3. Setup Tests")
    print("4. Run All Tests")
    print("Q. Quit")
    print()

def run_test(choice):
    """Run selected test"""
    
    test_files = {
        '1': 'quick_system_health_check.py',
        '2': 'system_functionality_test.py',
        '3': 'setup_tests.py',
        '4': 'test_runner.py'
    }
    
    if choice in test_files:
        test_file = test_files[choice]
        print(f"\n🚀 Running {test_file}...")
        print("-" * 40)
        
        try:
            result = subprocess.run([sys.executable, test_file], timeout=300)
            return result.returncode
        except subprocess.TimeoutExpired:
            print("⏰ Test timed out")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    else:
        print("❌ Invalid choice")
        return 1

def main():
    """Main menu loop"""
    
    if not Path('main.py').exists():
        print("❌ Error: Please run from Beverly Knits project directory")
        return 1
    
    while True:
        show_menu()
        choice = input("Enter your choice (1-4, Q): ").strip()
        
        if choice.upper() == 'Q':
            print("👋 Goodbye!")
            break
        
        if choice in ['1', '2', '3', '4']:
            exit_code = run_test(choice)
            print(f"\nTest completed with exit code: {exit_code}")
            print("\nPress Enter to continue...")
            input()
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()