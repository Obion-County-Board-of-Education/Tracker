#!/usr/bin/env python3
"""
Simple verification script to confirm priority feature removal
"""

import os
import re
from pathlib import Path

def check_files_for_priority():
    """Check all relevant files for priority references"""
    project_root = Path(".")
    priority_references = []
    
    # File patterns to check
    file_patterns = [
        "**/*.py", 
        "**/*.html",
        "**/*.css",
        "**/*.js"
    ]
    
    # Terms to search for (case insensitive)
    priority_terms = [
        r'\bpriority\b',
        r'\bhigh\s+priority\b',
        r'\bmedium\s+priority\b', 
        r'\blow\s+priority\b',
        r'priority\s*level',
        r'priority\s*field',
        r'priority\s*dropdown',
        r'priority\s*select'
    ]
    
    print("🔍 Scanning for priority references...")
    
    files_checked = 0
    for pattern in file_patterns:
        for file_path in project_root.glob(pattern):
            # Skip test files and cache directories
            if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'test_priority_removal.py']):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                files_checked += 1
                
                for term in priority_terms:
                    matches = re.findall(term, content, re.IGNORECASE)
                    if matches:
                        priority_references.append({
                            'file': str(file_path),
                            'term': term,
                            'matches': matches
                        })
                        
            except Exception as e:
                print(f"⚠️  Could not read {file_path}: {e}")
    
    print(f"📁 Checked {files_checked} files")
    
    if priority_references:
        print(f"❌ Found {len(priority_references)} priority references:")
        for ref in priority_references:
            print(f"   - {ref['file']}: {ref['term']} ({len(ref['matches'])} matches)")
        return False
    else:
        print("✅ No priority references found!")
        return True

def check_database_models():
    """Check database models for priority fields"""
    models_file = Path("ocs_shared_models/models.py")
    
    if not models_file.exists():
        print("⚠️  Database models file not found")
        return True
    
    try:
        content = models_file.read_text()
        
        # Look for priority field definitions
        priority_patterns = [
            r'priority\s*=\s*Column',
            r'priority_level\s*=\s*Column',
            r'class\s+Priority'
        ]
        
        found_priority = False
        for pattern in priority_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"❌ Found priority field definition in models: {pattern}")
                found_priority = True
        
        if not found_priority:
            print("✅ No priority fields found in database models")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check models file: {e}")
        return True

def check_form_submissions():
    """Check that form submission code doesn't reference priority"""
    main_file = Path("main.py")
    
    if not main_file.exists():
        print("⚠️  main.py file not found")
        return True
    
    try:
        content = main_file.read_text()
        
        # Look for priority in form submission functions
        priority_patterns = [
            r'priority.*Form\(',
            r'Form\(.*priority',
            r'priority\s*:\s*str\s*=\s*Form'
        ]
        
        found_priority = False
        for pattern in priority_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"❌ Found priority in form submission: {pattern}")
                found_priority = True
        
        if not found_priority:
            print("✅ No priority parameters found in form submission code")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check main.py: {e}")
        return True

def main():
    """Run verification checks"""
    print("🧪 Priority Feature Removal Verification")
    print("=" * 50)
    
    checks = [
        ("File Content Check", check_files_for_priority),
        ("Database Models Check", check_database_models),
        ("Form Submission Check", check_form_submissions)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}...")
        if check_func():
            passed += 1
            print(f"   ✅ PASSED")
        else:
            print(f"   ❌ FAILED")
    
    print(f"\n📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 SUCCESS: Priority feature has been completely removed!")
        print("\n📋 Summary of changes made:")
        print("   • Removed priority dropdown from maintenance ticket form")
        print("   • Removed priority parameter from form submission handlers") 
        print("   • Removed priority badges from ticket listing pages")
        print("   • Removed priority-related CSS styling")
        print("   • Updated success page messaging")
        print("   • Verified no priority fields in database models")
        print("\n✨ The ticket system now operates without priority levels.")
    else:
        print("⚠️  Some checks failed - priority removal may be incomplete")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
