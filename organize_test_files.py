#!/usr/bin/env python3
"""
Test File Organization Script
Moves all test files from root directory to appropriate tests/ subdirectories
"""

import os
import shutil
from pathlib import Path

def organize_test_files():
    """Organize test files into proper directory structure"""
    print("🚀 Organizing Test Files")
    print("=" * 50)
    
    root_dir = Path(r"c:\Users\JordanHowell\OneDrive - Obion County Schools\Documents\Projects\Tracker")
    tests_dir = root_dir / "tests"
    
    # Create subdirectories if they don't exist
    subdirs = [
        "unit",
        "integration", 
        "api",
        "portal",
        "csv",
        "utilities",
        "data",
        "results"
    ]
    
    for subdir in subdirs:
        (tests_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Define file categorization rules
    file_mappings = {
        # Unit tests
        "unit": [
            "test_dynamic_menu.py",
            "test_menu_context_fix.py", 
            "test_menu_error.py",
            "test_timezone.py",
            "test_open_status_issue.py"
        ],
        
        # API tests
        "api": [
            "test_api_timezone.py",
            "test_auto_update.py",
            "test_clear_functionality.py",
            "test_maintenance_update.py",
            "test_update.py",
            "check_services.py",
            "simple_api_test.py"
        ],
        
        # Integration tests
        "integration": [
            "test_comprehensive_verification.py",
            "test_data_integrity.py",
            "complete_fix_verification.py",
            "complete_verification.py", 
            "final_verification.py",
            "final_verification_complete.py",
            "maintenance_verification.py",
            "quick_test.py",
            "verify_all_fixes.py"
        ],
        
        # Portal tests
        "portal": [
            "test_edit_user_routes.py",
            "test_import_buttons.py",
            "test_pages_final.py",
            "test_portal_detailed.py",
            "test_portal_import.py",
            "test_portal_issue.py",
            "test_portal_startup.py",
            "test_route_availability.py",
            "test_routes_simple.py",
            "test_user_building_routes.py",
            "check_routes_detailed.py",
            "debug_route_registration.py",
            "debug_routes_final.py",
            "debug_routes_test.py",
            "detailed_route_test.py",
            "quick_route_test.py",
            "simple_route_test.py"
        ],
        
        # CSV tests
        "csv": [
            "test_csv_export_functionality.py",
            "test_csv_headers.py",
            "test_csv_import.py",
            "test_csv_import_feedback.py",
            "test_cycle_import.py",
            "test_debug_import.py",
            "test_export_for_import_routes.py",
            "test_export_import_cycle.py",
            "test_export_routes.py",
            "test_immediate_import.py",
            "test_import_fixed.py",
            "test_import_functionality.py",
            "test_import_ready_export.py",
            "test_import_ready_exports.py",
            "test_proper_import.py",
            "test_simple_import.py",
            "test_status_mapping_fix.py",
            "final_csv_export_test.py",
            "final_csv_import_verification.py",
            "final_import_csv_verification.py",
            "final_import_test.py",
            "debug_csv_import.py",
            "debug_detailed_import.py",
            "debug_import_cycle.py"
        ],
        
        # Utilities (debug, check, verify scripts)
        "utilities": [
            "check_buildings.py",
            "check_html_content.py",
            "check_tickets.py",
            "check_tickets_db.py",
            "create_test_ticket.py",
            "python_test_import.py",
            "quick_final_verification.py",
            "quick_fix_test.py",
            "quick_verify.py",
            "simple_import_test.py",
            "simple_parameter_test.py",
            "simple_test.py",
            "simple_test_script.py",
            "test_parameter_directly.py",
            "test_python_execution.py",
            "validate_closed_counter.py",
            "verify_architecture_compliance.py",
            "verify_csv_import.py",
            "verify_csv_import_after_overwrites.py",
            "verify_edit_user_routes.py",
            "verify_feedback_system.py",
            "verify_import_buttons.py",
            "verify_timezone_fix.py",
            "clean_export_for_import_routes.py",
            "test_closed_counter.py",
            "dashboard_verification.py",
            "homepage_fixes_verification.py"
        ]
    }
    
    # Move files according to mappings
    moved_count = 0
    skipped_count = 0
    
    for category, files in file_mappings.items():
        print(f"\n📁 Moving {category} files:")
        target_dir = tests_dir / category
        
        for filename in files:
            source_path = root_dir / filename
            target_path = target_dir / filename
            
            if source_path.exists():
                try:
                    # Check if file already exists in target
                    if target_path.exists():
                        print(f"  ⚠️  {filename} already exists in {category}/, skipping")
                        skipped_count += 1
                    else:
                        shutil.move(str(source_path), str(target_path))
                        print(f"  ✅ {filename} → tests/{category}/")
                        moved_count += 1
                except Exception as e:
                    print(f"  ❌ Error moving {filename}: {e}")
            else:
                print(f"  ⚠️  {filename} not found in root")
    
    # Find any remaining test files in root
    remaining_files = []
    patterns = ["test_*.py", "*test*.py", "verify_*.py", "validate_*.py", "debug_*.py", "check_*.py"]
    
    for pattern in patterns:
        for file in root_dir.glob(pattern):
            if file.is_file() and file.suffix == '.py':
                # Skip the organization scripts we just created
                if file.name not in ["analyze_test_organization.py", "organize_test_files.py"]:
                    remaining_files.append(file.name)
    
    remaining_files = sorted(list(set(remaining_files)))
    
    if remaining_files:
        print(f"\n📋 Remaining test files in root ({len(remaining_files)}):")
        print("  These may need manual categorization:")
        for file in remaining_files:
            print(f"    • {file}")
    
    # Move CSV test data files
    print(f"\n📄 Moving CSV test data files:")
    csv_data_files = list(root_dir.glob("*.csv"))
    test_csv_files = [f for f in csv_data_files if 'test' in f.name.lower() or 'debug' in f.name.lower()]
    
    for csv_file in test_csv_files:
        target_path = tests_dir / "data" / csv_file.name
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
    print(f"  Files skipped (duplicates): {skipped_count}")
    print(f"  Remaining in root: {len(remaining_files)}")
    
    # Create a README for the tests directory
    readme_content = """# Tests Directory

This directory contains all test files organized by category:

## Structure

- **unit/** - Unit tests for individual components and functions
- **integration/** - Integration tests and comprehensive verification scripts  
- **api/** - API endpoint and service tests
- **portal/** - Portal route, UI, and user interface tests
- **csv/** - CSV import/export functionality tests
- **utilities/** - Debug scripts, check scripts, and verification utilities
- **data/** - Test data files (CSV, JSON, etc.)
- **results/** - Test execution results and reports

## Running Tests

- Individual tests: `python tests/unit/test_example.py`
- Category tests: `python -m pytest tests/unit/`
- All tests: `python -m pytest tests/`

## Test Categories

### Unit Tests
Tests for individual components, modules, and functions.

### Integration Tests  
End-to-end tests that verify complete workflows and system integration.

### API Tests
Tests for REST API endpoints and service functionality.

### Portal Tests
Tests for web portal routes, user interfaces, and portal-specific functionality.

### CSV Tests
Tests for CSV import/export functionality, data validation, and file processing.

### Utilities
Debug scripts, verification tools, and helper utilities for testing and development.
"""
    
    readme_path = tests_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\n📚 Created tests/README.md with organization documentation")
    
    return moved_count > 0

if __name__ == "__main__":
    success = organize_test_files()
    print(f"\n🏁 Test Organization: {'✅ COMPLETED' if success else '⚠️ NO CHANGES MADE'}")
    print(f"\n💡 Next steps:")
    print(f"  1. Review any remaining files in root directory")
    print(f"  2. Update any import paths in moved test files if needed") 
    print(f"  3. Test that moved files still execute correctly")
    print(f"  4. Update CI/CD scripts to use new test structure")
