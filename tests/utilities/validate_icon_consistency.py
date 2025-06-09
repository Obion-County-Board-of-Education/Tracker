#!/usr/bin/env python3
"""
Script to validate that all "Closed" status icons are consistent across templates
"""
import os
import re
from pathlib import Path

def check_icon_consistency():
    """Check all HTML templates for consistent closed status icons"""
    templates_dir = Path("templates")
    if not templates_dir.exists():
        print("❌ Templates directory not found")
        return False
    
    inconsistent_files = []
    consistent_count = 0
    
    # Pattern to find closed status with non-lock icons
    bad_pattern = re.compile(r'closed.*[✅📁]|Closed.*[✅📁]', re.IGNORECASE)
    # Pattern to find closed status with lock icons (good)
    good_pattern = re.compile(r'closed.*🔒|Closed.*🔒', re.IGNORECASE)
    
    print("🔍 Checking template files for icon consistency...")
    
    for html_file in templates_dir.glob("**/*.html"):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for bad icons
        bad_matches = bad_pattern.findall(content)
        good_matches = good_pattern.findall(content)
        
        if bad_matches:
            inconsistent_files.append((str(html_file), bad_matches))
            print(f"❌ {html_file}: Found inconsistent icons: {bad_matches}")
        elif good_matches:
            consistent_count += 1
            print(f"✅ {html_file}: {len(good_matches)} consistent lock icons found")
    
    print(f"\n📊 Summary:")
    print(f"   Files with consistent icons: {consistent_count}")
    print(f"   Files with inconsistent icons: {len(inconsistent_files)}")
    
    if inconsistent_files:
        print(f"\n❌ Icon consistency check FAILED")
        return False
    else:
        print(f"\n✅ Icon consistency check PASSED - All closed status icons use 🔒")
        return True

if __name__ == "__main__":
    print("🚀 OCS Portal Icon Consistency Validator")
    print("="*50)
    
    success = check_icon_consistency()
    
    if success:
        print("\n🎉 Ready for testing! All templates have consistent closed status icons.")
        print("\n💡 To test the changes:")
        print("   1. Run: python run_server.py")
        print("   2. Open: http://localhost:8000")
        print("   3. Navigate to ticket lists and details to verify icons")
    else:
        print("\n🔧 Please fix the inconsistencies before testing.")
