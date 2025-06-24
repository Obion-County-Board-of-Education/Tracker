#!/usr/bin/env python3
"""
Test Runner for OCS Portal
Runs tests from the organized test structure
"""
import os
import sys
import subprocess
from pathlib import Path

def run_tests(category=None):
    """Run tests from specific category or all tests"""
    test_dir = Path("tests")
    
    if category:
        category_dir = test_dir / category
        if category_dir.exists():
            print(f"🧪 Running {category} tests...")
            test_files = list(category_dir.glob("test_*.py"))
            if not test_files:
                print(f"   No test files found in {category}/")
                return
                
            for test_file in test_files:
                print(f"\n📋 Running: {test_file.name}")
                print("-" * 50)
                try:
                    result = subprocess.run([sys.executable, str(test_file)], 
                                          capture_output=False, 
                                          text=True)
                    if result.returncode == 0:
                        print(f"✅ {test_file.name} passed")
                    else:
                        print(f"❌ {test_file.name} failed")
                except Exception as e:
                    print(f"❌ Error running {test_file}: {e}")
        else:
            print(f"❌ Category '{category}' not found")
            print("Available categories:", [d.name for d in test_dir.iterdir() if d.is_dir()])

def list_tests():
    """List all available tests"""
    test_dir = Path("tests")
    print("📋 Available Tests:")
    print("=" * 50)
    
    for category_dir in sorted(test_dir.iterdir()):
        if category_dir.is_dir() and category_dir.name not in ['__pycache__', '.git']:
            test_files = list(category_dir.glob("test_*.py"))
            script_files = list(category_dir.glob("*.py")) if category_dir.name == "utilities" else []
            ps_files = list(category_dir.glob("*.ps1")) if category_dir.name == "scripts" else []
            
            if test_files or script_files or ps_files:
                print(f"\n📁 {category_dir.name.upper()}")
                for test_file in sorted(test_files):
                    print(f"   🐍 {test_file.name}")
                for script_file in sorted(script_files):
                    if script_file.name.startswith(('debug_', 'verify_')):
                        print(f"   🔧 {script_file.name}")
                for ps_file in sorted(ps_files):
                    print(f"   📜 {ps_file.name}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_tests()
        else:
            category = sys.argv[1]
            run_tests(category)
    else:
        print("🚀 OCS Portal Test Runner")
        print("=" * 30)
        print("Usage:")
        print("  python run_tests.py           # Show usage")
        print("  python run_tests.py [category] # Run specific category")
        print("  python run_tests.py list      # List all tests")
        print()
        print("Categories: unit, integration, api, portal, csv, utilities")
        print()
        list_tests()
