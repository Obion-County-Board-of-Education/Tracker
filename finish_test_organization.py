#!/usr/bin/env python3
"""
Finish Test File Organization Script
Moves remaining test files from root directory to appropriate tests/ subdirectories
"""

import os
import shutil
from pathlib import Path

def finish_test_organization():
    """Move remaining test files to appropriate locations"""
    print("🚀 Finishing Test File Organization")
    print("=" * 50)
    
    root_dir = Path(r"c:\Users\JordanHowell\OneDrive - Obion County Schools\Documents\Projects\Tracker")
    tests_dir = root_dir / "tests"
    
    # Get all test files still in root
    test_patterns = ["test_*.py", "*test*.py", "verify_*.py", "validate_*.py", "debug_*.py", "check_*.py"]
    
    remaining_files = []
    for pattern in test_patterns:
        for file in root_dir.glob(pattern):
            if file.is_file() and file.suffix == '.py':
                # Skip organization scripts
                if file.name not in ["analyze_test_organization.py", "organize_test_files.py", "finish_test_organization.py"]:
                    remaining_files.append(file)
    
    print(f"Found {len(remaining_files)} test files still in root directory")
    
    # Categorize remaining files
    moved_count = 0
    
    for file_path in remaining_files:
        filename = file_path.name
        target_subdir = None
        
        # Categorization logic
        if any(x in filename.lower() for x in ['csv', 'import', 'export']):
            target_subdir = "csv"
        elif any(x in filename.lower() for x in ['portal', 'route', 'user', 'edit']):
            target_subdir = "portal"  
        elif any(x in filename.lower() for x in ['api', 'service', 'update']):
            target_subdir = "api"
        elif any(x in filename.lower() for x in ['verify', 'check', 'debug', 'validate', 'quick']):
            target_subdir = "utilities"
        elif any(x in filename.lower() for x in ['comprehensive', 'complete', 'final', 'integration']):
            target_subdir = "integration"
        elif filename.startswith('test_') and any(x in filename.lower() for x in ['menu', 'timezone', 'dynamic', 'status']):
            target_subdir = "unit"
        else:
            # Default to utilities for miscellaneous test files
            target_subdir = "utilities"
        
        target_dir = tests_dir / target_subdir
        target_path = target_dir / filename
        
        try:
            if not target_path.exists():
                shutil.move(str(file_path), str(target_path))
                print(f"  ✅ {filename} → tests/{target_subdir}/")
                moved_count += 1
            else:
                print(f"  ⚠️  {filename} already exists in {target_subdir}/, skipping")
        except Exception as e:
            print(f"  ❌ Error moving {filename}: {e}")
    
    # Move CSV test data files
    csv_files = list(root_dir.glob("*.csv"))
    test_csv_files = [f for f in csv_files if any(x in f.name.lower() for x in ['test', 'debug', 'cycle', 'import'])]
    
    if test_csv_files:
        print(f"\n📄 Moving CSV test data files:")
        data_dir = tests_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        for csv_file in test_csv_files:
            target_path = data_dir / csv_file.name
            try:
                if not target_path.exists():
                    shutil.move(str(csv_file), str(target_path))
                    print(f"  ✅ {csv_file.name} → tests/data/")
                else:
                    print(f"  ⚠️  {csv_file.name} already exists in data/")
            except Exception as e:
                print(f"  ❌ Error moving {csv_file.name}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"  Files moved: {moved_count}")
    print(f"  Total test files processed: {len(remaining_files)}")
    
    # Check what's left
    final_check = []
    for pattern in test_patterns:
        for file in root_dir.glob(pattern):
            if file.is_file() and file.suffix == '.py':
                if file.name not in ["analyze_test_organization.py", "organize_test_files.py", "finish_test_organization.py"]:
                    final_check.append(file.name)
    
    if final_check:
        print(f"\n⚠️  Files still in root ({len(final_check)}):")
        for file in sorted(final_check):
            print(f"    • {file}")
    else:
        print(f"\n🎉 All test files successfully organized!")
    
    return moved_count > 0

if __name__ == "__main__":
    success = finish_test_organization()
    print(f"\n🏁 Test Organization: {'✅ COMPLETED' if success else '⚠️ NO CHANGES MADE'}")
