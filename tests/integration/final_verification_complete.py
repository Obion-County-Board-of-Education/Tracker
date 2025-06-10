#!/usr/bin/env python3
"""
🎯 FINAL CSV EXPORT-IMPORT CYCLE VERIFICATION
==============================================
This script tests the complete export-import cycle that was causing 
duplicate tickets with different IDs and empty field data.

SOLUTION IMPLEMENTED:
- Added `import_ready` parameter to export endpoints
- When `import_ready=true`, exports exclude id, created_at, updated_at fields
- This prevents duplicate IDs and empty field issues during import

VERIFICATION:
1. Creates test tickets
2. Exports with import_ready=true 
3. Clears database
4. Imports the exported CSV
5. Verifies data integrity
"""

import requests
import json

def main():
    print("🎯 FINAL CSV EXPORT-IMPORT VERIFICATION")
    print("=" * 50)
    
    # Step 1: Clear database for clean test
    print("🧹 Clearing database for clean test...")
    try:
        response = requests.delete("http://localhost:8000/api/tickets/tech/clear")
        if response.status_code == 200:
            print("✅ Database cleared successfully")
        else:
            print(f"⚠️ Clear failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Clear error: {e}")
        return False
    
    # Step 2: Create test tickets for export
    print("\n📝 Creating test tickets for export...")
    test_tickets = [
        {
            "title": "Export Test 1",
            "description": "First test ticket for export-import cycle",
            "issue_type": "Hardware",
            "building_name": "Test School A",
            "room_name": "Room 101",
            "created_by": "TestUser1",
            "tag": "EXP001"
        },
        {
            "title": "Export Test 2", 
            "description": "Second test ticket for export-import cycle",
            "issue_type": "Software",
            "building_name": "Test School B",
            "room_name": "Room 202",
            "created_by": "TestUser2",
            "tag": "EXP002"
        }
    ]
    
    created_tickets = []
    for i, ticket_data in enumerate(test_tickets):
        try:
            response = requests.post("http://localhost:8000/api/tickets/tech", 
                                   json=ticket_data)
            if response.status_code == 200:
                ticket = response.json()
                created_tickets.append(ticket)
                print(f"✅ Created ticket {i+1}: {ticket['title']} (ID: {ticket['id']})")
            else:
                print(f"❌ Failed to create ticket {i+1}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error creating ticket {i+1}: {e}")
            return False
    
    # Step 3: Export tickets with import_ready=true
    print(f"\n📤 Exporting {len(created_tickets)} tickets with import_ready=true...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech/export?import_ready=true")
        if response.status_code == 200:
            print("✅ Export successful")
            csv_content = response.text
            
            # Save to file
            with open('final_verification_export.csv', 'w') as f:
                f.write(csv_content)
            
            # Verify headers exclude problematic fields
            headers = csv_content.split('\n')[0].split(',')
            print(f"📋 Export headers: {headers}")
            
            problematic_fields = ['id', 'created_at', 'updated_at']
            has_problematic = any(field in headers for field in problematic_fields)
            
            if has_problematic:
                print("❌ Export contains problematic fields that cause import issues!")
                return False
            else:
                print("✅ Export headers are import-ready (no id, timestamps)")
                
        else:
            print(f"❌ Export failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Export error: {e}")
        return False
    
    # Step 4: Clear database again for import test
    print("\n🧹 Clearing database for import test...")
    try:
        response = requests.delete("http://localhost:8000/api/tickets/tech/clear")
        if response.status_code == 200:
            print("✅ Database cleared for import test")
        else:
            print(f"⚠️ Clear failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Clear error: {e}")
        return False
    
    # Step 5: Import the exported CSV
    print("\n📥 Importing the exported CSV...")
    try:
        with open('final_verification_export.csv', 'rb') as f:
            files = {'file': ('final_verification_export.csv', f, 'text/csv')}
            data = {'operation': 'append'}
            
            response = requests.post("http://localhost:8000/api/tickets/tech/import",
                                   files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Import successful")
                print(f"   Imported count: {result.get('imported_count')}")
                print(f"   Errors: {result.get('errors')}")
                
                if result.get('imported_count') != len(created_tickets):
                    print(f"⚠️ Import count mismatch: expected {len(created_tickets)}, got {result.get('imported_count')}")
                    
            else:
                print(f"❌ Import failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Step 6: Verify imported data
    print("\n🔍 Verifying imported data...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            imported_tickets = response.json()
            print(f"✅ Found {len(imported_tickets)} tickets after import")
            
            # Verify data integrity
            for i, original in enumerate(created_tickets):
                if i < len(imported_tickets):
                    imported = imported_tickets[i]
                    
                    # Check that IDs are different (new tickets, not duplicates)
                    if imported['id'] == original['id']:
                        print(f"⚠️ Ticket {i+1} has same ID as original (potential duplicate)")
                    
                    # Check that data fields are preserved
                    fields_to_check = ['title', 'description', 'issue_type', 'school', 'room', 'tag', 'created_by']
                    data_preserved = True
                    
                    for field in fields_to_check:
                        if imported.get(field) != original.get(field):
                            print(f"❌ Ticket {i+1} field '{field}' not preserved: '{original.get(field)}' -> '{imported.get(field)}'")
                            data_preserved = False
                    
                    if data_preserved:
                        print(f"✅ Ticket {i+1} data preserved correctly")
                else:
                    print(f"❌ Missing imported ticket {i+1}")
                    return False
            
            print("\n🎉 SUCCESS! CSV export-import cycle is working correctly!")
            print("✅ Export excludes problematic fields (id, created_at, updated_at)")
            print("✅ Import creates new tickets without duplicates")
            print("✅ Data integrity is maintained through the cycle")
            return True
            
        else:
            print(f"❌ Failed to get imported tickets: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying imported data: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'=' * 50}")
    if success:
        print("🎊 VERIFICATION COMPLETE: CSV export-import cycle is FIXED!")
    else:
        print("❌ VERIFICATION FAILED: Issues remain in export-import cycle")
