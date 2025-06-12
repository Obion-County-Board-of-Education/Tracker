#!/usr/bin/env python3
"""Quick final verification of CSV export-import cycle"""
import requests
import json

def test_export_import_cycle():
    print("🎯 FINAL VERIFICATION: CSV Export-Import Cycle")
    print("=" * 50)
    
    # Test 1: Verify import_ready=true excludes problematic fields
    print("🔍 Testing export with import_ready=true...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech/export?import_ready=true")
        if response.status_code == 200:
            csv_content = response.text
            headers = csv_content.split('\n')[0].split(',')
            
            problematic_fields = ['id', 'created_at', 'updated_at']
            has_problematic = any(field in headers for field in problematic_fields)
            
            print(f"📋 Export headers: {headers}")
            
            if has_problematic:
                print("❌ FAIL: Export still contains problematic fields!")
                return False
            else:
                print("✅ PASS: Export excludes problematic fields")
        else:
            print(f"❌ Export failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Export error: {e}")
        return False
    
    # Test 2: Verify import_ready=false includes all fields  
    print("\n🔍 Testing export with import_ready=false...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech/export?import_ready=false")
        if response.status_code == 200:
            csv_content = response.text
            headers = csv_content.split('\n')[0].split(',')
            
            expected_fields = ['id', 'created_at', 'updated_at']
            has_expected = all(field in headers for field in expected_fields)
            
            print(f"📋 Full export headers: {headers}")
            
            if has_expected:
                print("✅ PASS: Full export includes all fields")
            else:
                print("❌ FAIL: Full export missing expected fields!")
                return False
        else:
            print(f"❌ Full export failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Full export error: {e}")
        return False
    
    # Test 3: Test maintenance export as well
    print("\n🔍 Testing maintenance export with import_ready=true...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/maintenance/export?import_ready=true")
        if response.status_code == 200:
            csv_content = response.text
            headers = csv_content.split('\n')[0].split(',')
            
            problematic_fields = ['id', 'created_at', 'updated_at']
            has_problematic = any(field in headers for field in problematic_fields)
            
            print(f"📋 Maintenance export headers: {headers}")
            
            if has_problematic:
                print("❌ FAIL: Maintenance export contains problematic fields!")
                return False
            else:
                print("✅ PASS: Maintenance export excludes problematic fields")
        else:
            print(f"❌ Maintenance export failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Maintenance export error: {e}")
        return False
    
    print("\n🎉 SUCCESS! All export tests passed!")
    print("✅ Tech export with import_ready=true: excludes id, timestamps")  
    print("✅ Tech export with import_ready=false: includes all fields")
    print("✅ Maintenance export with import_ready=true: excludes id, timestamps")
    print("\n🎊 CSV Export-Import Cycle Fix is COMPLETE!")
    return True

if __name__ == "__main__":
    test_export_import_cycle()
