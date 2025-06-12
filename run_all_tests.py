#!/usr/bin/env python3
"""
OCS Portal Test Suite Runner
============================

This script provides a unified way to run all tests in the OCS Portal system.
All testing scripts have been properly organized into the tests/ folder structure.

Usage:
    python run_all_tests.py [test_category]

Test Categories:
    - unit: Run unit tests
    - portal: Run portal-specific tests  
    - api: Run API tests
    - integration: Run integration tests
    - csv: Run CSV import/export tests
    - utilities: Run utility verification scripts
    - all: Run all tests (default)
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Test directory structure
TESTS_DIR = Path(__file__).parent / "tests"
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "portal": "tests/portal", 
    "api": "tests/api",
    "integration": "tests/integration",
    "csv": "tests/csv",
    "utilities": "tests/utilities"
}

def run_python_tests(category_path):
    """Run all Python test files in a category"""
    test_files = list(Path(category_path).glob("test_*.py"))
    if not test_files:
        print(f"  No test files found in {category_path}")
        return True
        
    success = True
    for test_file in test_files:
        print(f"  Running {test_file.name}...")
        try:
            result = subprocess.run([sys.executable, str(test_file)], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"    ✅ PASSED")
            else:
                print(f"    ❌ FAILED: {result.stderr.strip()}")
                success = False
        except subprocess.TimeoutExpired:
            print(f"    ⏰ TIMEOUT")
            success = False
        except Exception as e:
            print(f"    ❌ ERROR: {e}")
            success = False
    
    return success

def run_verification_scripts(category_path):
    """Run verification scripts in a category"""
    verify_files = list(Path(category_path).glob("verify_*.py"))
    if not verify_files:
        return True
        
    success = True
    for verify_file in verify_files:
        print(f"  Running {verify_file.name}...")
        try:
            result = subprocess.run([sys.executable, str(verify_file)], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"    ✅ VERIFIED")
            else:
                print(f"    ❌ VERIFICATION FAILED: {result.stderr.strip()}")
                success = False
        except subprocess.TimeoutExpired:
            print(f"    ⏰ TIMEOUT")
            success = False
        except Exception as e:
            print(f"    ❌ ERROR: {e}")
            success = False
    
    return success

def run_category_tests(category):
    """Run all tests in a specific category"""
    if category not in TEST_CATEGORIES:
        print(f"❌ Unknown test category: {category}")
        return False
        
    category_path = Path(TEST_CATEGORIES[category])
    if not category_path.exists():
        print(f"❌ Test directory not found: {category_path}")
        return False
        
    print(f"\n🧪 Running {category.upper()} tests...")
    print("=" * 50)
    
    success = True
    
    # Run Python tests
    if not run_python_tests(category_path):
        success = False
        
    # Run verification scripts
    if not run_verification_scripts(category_path):
        success = False
        
    return success

def show_test_organization():
    """Display the current test organization"""
    print("\n📁 Test Organization Summary")
    print("=" * 50)
    
    for category, path in TEST_CATEGORIES.items():
        category_path = Path(path)
        if category_path.exists():
            test_files = list(category_path.glob("*.py"))
            print(f"📁 {category.upper()}: {len(test_files)} files")
        else:
            print(f"📁 {category.upper()}: Directory not found")
    
    print(f"\n✅ All testing scripts are properly organized in the tests/ folder")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="OCS Portal Test Suite Runner")
    parser.add_argument("category", nargs="?", default="all", 
                       choices=list(TEST_CATEGORIES.keys()) + ["all", "organization"],
                       help="Test category to run")
    
    args = parser.parse_args()
    
    print("🚀 OCS Portal Test Suite Runner")
    print("=" * 50)
    
    if args.category == "organization":
        show_test_organization()
        return
        
    if args.category == "all":
        print("Running ALL test categories...")
        overall_success = True
        for category in TEST_CATEGORIES.keys():
            if not run_category_tests(category):
                overall_success = False
                
        if overall_success:
            print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ Some tests failed. Check output above.")
            sys.exit(1)
    else:
        success = run_category_tests(args.category)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
