#!/usr/bin/env python3
"""
Test File Organization Analysis
Analyzes which test files are properly organized vs scattered in root directory
"""

import os
from pathlib import Path

def analyze_test_organization():
    """Analyze the current test file organization"""
    print("🔍 Test File Organization Analysis")
    print("=" * 50)
    
    root_dir = Path(r"c:\Users\JordanHowell\OneDrive - Obion County Schools\Documents\Projects\Tracker")
    tests_dir = root_dir / "tests"
    
    # Find all test-related files in root directory
    root_test_files = []
    
    # Patterns to identify test files
    patterns = [
        "test_*.py",
        "*test*.py", 
        "verify_*.py",
        "validate_*.py",
        "debug_*.py",
        "check_*.py",
        "*verification*.py"
    ]
    
    for pattern in patterns:
        for file in root_dir.glob(pattern):
            if file.is_file() and file.suffix == '.py':
                root_test_files.append(file.name)
    
    # Remove duplicates and sort
    root_test_files = sorted(list(set(root_test_files)))
    
    # Find all test files already in tests directory
    organized_test_files = []
    if tests_dir.exists():
        for file in tests_dir.rglob("*.py"):
            organized_test_files.append(file.name)
    
    organized_test_files = sorted(list(set(organized_test_files)))
    
    print(f"📊 Summary:")
    print(f"  Test files in root directory: {len(root_test_files)}")
    print(f"  Test files organized in tests/: {len(organized_test_files)}")
    
    print(f"\n📁 Test files still in root directory ({len(root_test_files)}):")
    for i, file in enumerate(root_test_files, 1):
        print(f"  {i:2d}. {file}")
    
    # Check for duplicates (files that exist in both root and tests)
    root_names = set(root_test_files)
    organized_names = set(organized_test_files)
    duplicates = root_names.intersection(organized_names)
    
    if duplicates:
        print(f"\n⚠️  Duplicate files (exist in both root and tests/): {len(duplicates)}")
        for file in sorted(duplicates):
            print(f"    {file}")
    
    # Categorize root files by type
    categories = {
        "Unit Tests": [f for f in root_test_files if f.startswith("test_") and 
                      any(word in f for word in ["unit", "function", "module"])],
        "API Tests": [f for f in root_test_files if f.startswith("test_") and 
                     any(word in f for word in ["api", "endpoint", "service"])],
        "Integration Tests": [f for f in root_test_files if f.startswith("test_") and 
                            any(word in f for word in ["integration", "comprehensive", "cycle", "end_to_end"])],
        "Portal Tests": [f for f in root_test_files if f.startswith("test_") and 
                        any(word in f for word in ["portal", "route", "page", "user", "building"])],
        "CSV Tests": [f for f in root_test_files if f.startswith("test_") and 
                     any(word in f for word in ["csv", "import", "export"])],
        "Verification Scripts": [f for f in root_test_files if f.startswith("verify_")],
        "Debug Scripts": [f for f in root_test_files if f.startswith("debug_")],
        "Check Scripts": [f for f in root_test_files if f.startswith("check_")],
        "Validation Scripts": [f for f in root_test_files if f.startswith("validate_")],
        "Other Test Files": []
    }
    
    # Categorize remaining files
    categorized = set()
    for category, files in categories.items():
        if category != "Other Test Files":
            categorized.update(files)
    
    categories["Other Test Files"] = [f for f in root_test_files if f not in categorized]
    
    print(f"\n📋 Root test files by category:")
    for category, files in categories.items():
        if files:
            print(f"\n  {category} ({len(files)}):")
            for file in files:
                print(f"    • {file}")
    
    # Recommend organization structure
    print(f"\n💡 Recommended organization:")
    print(f"  tests/")
    print(f"    ├── unit/           # Unit tests for individual components")
    print(f"    ├── integration/    # Integration and comprehensive tests") 
    print(f"    ├── api/           # API endpoint tests")
    print(f"    ├── portal/        # Portal route and UI tests")
    print(f"    ├── csv/           # CSV import/export tests")
    print(f"    ├── utilities/     # Debug, check, verify scripts")
    print(f"    ├── data/          # Test data files")
    print(f"    └── results/       # Test result outputs")
    
    return len(root_test_files) == 0

if __name__ == "__main__":
    is_organized = analyze_test_organization()
    print(f"\n🏁 Test Organization Status: {'✅ COMPLETE' if is_organized else '⚠️ NEEDS WORK'}")
