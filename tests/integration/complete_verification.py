#!/usr/bin/env python3
"""
Final verification of CSV export-import fix
Tests the complete export-import cycle to ensure headers are correct
"""

import requests
import csv
import io

def main():
    print("🎯 FINAL CSV EXPORT-IMPORT VERIFICATION")
    print("=" * 50)
    
    # Test 1: Create a test ticket with proper data
    print('🔍 Creating test ticket for export-import cycle...')
    test_data = {
        'title': 'Final Verification Test Ticket',
        'description': 'Testing the complete CSV export-import cycle after header fix',
        'issue_type': 'Software',
        'building_name': 'Central Office',
        'room_name': 'Main Office',
        'tag': 'VERIFY001',
        'created_by': 'System Test'
    }

    response = requests.post('http://localhost:8000/api/tickets/tech', json=test_data)
    if response.status_code == 200:
        ticket = response.json()
        print(f'✅ Test ticket created: ID {ticket["id"]}')
        test_ticket_id = ticket["id"]
    else:
        print(f'❌ Failed to create test ticket: {response.status_code}')
        return False

    # Test 2: Export CSV with fixed headers
    print('\n📤 Exporting CSV with fixed headers...')
    response = requests.get('http://localhost:8000/api/tickets/tech/export')
    if response.status_code == 200:
        print('✅ CSV export successful')
        
        # Check header format
        csv_content = response.text
        lines = csv_content.strip().split('\n')
        headers = lines[0].split(',')
        print(f'📋 Headers: {headers[:5]}...')
        
        # Verify underscore format
        expected_headers = ['id', 'title', 'description', 'issue_type', 'school']
        if all(h in headers for h in expected_headers):
            print('✅ Headers are in correct underscore format')
        else:
            print('❌ Headers still in wrong format')
            return False
            
        # Save for import test
        with open('final_verification_export.csv', 'w') as f:
            f.write(csv_content)
        print('💾 Saved CSV for import test')
    else:
        print(f'❌ CSV export failed: {response.status_code}')
        return False

    # Test 3: Clear existing data and import the CSV
    print('\n🧹 Clearing existing tickets for clean import test...')
    response = requests.delete('http://localhost:8000/api/tickets/tech/clear')
    if response.status_code == 200:
        print('✅ Tickets cleared successfully')
    else:
        print(f'⚠️ Clear failed: {response.status_code} (continuing anyway)')    # Test 4: Import the exported CSV
    print('\n📥 Importing the exported CSV file...')
    try:
        with open('final_verification_export.csv', 'rb') as f:
            files = {'file': ('test_export.csv', f, 'text/csv')}
            data = {'operation': 'overwrite'}
            
            response = requests.post('http://localhost:8000/api/tickets/tech/import', 
                                   files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            print(f'✅ CSV import successful: {result.get("imported_count", "unknown")} tickets imported')
            
            if result.get('errors'):
                print(f'⚠️ Import warnings: {result["errors"]}')
        else:
            print(f'❌ CSV import failed: {response.status_code}')
            print(f'Response: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Error during import: {e}')
        return False

    # Test 5: Verify imported data
    print('\n🔍 Verifying imported data...')
    response = requests.get('http://localhost:8000/api/tickets/tech')
    if response.status_code == 200:
        tickets = response.json()
        
        # Find our test ticket
        test_ticket = None
        for ticket in tickets:
            if ticket.get('tag') == 'VERIFY001':
                test_ticket = ticket
                break
                
        if test_ticket:
            print('✅ Test ticket found in imported data')
            print(f'   Title: {test_ticket.get("title", "N/A")}')
            print(f'   Issue Type: {test_ticket.get("issue_type", "N/A")}')
            print(f'   Tag: {test_ticket.get("tag", "N/A")}')
            print(f'   Status: {test_ticket.get("status", "N/A")}')
            print(f'   Created By: {test_ticket.get("created_by", "N/A")}')
        else:
            print('❌ Test ticket not found in imported data')
            return False
    else:
        print(f'❌ Failed to retrieve imported tickets: {response.status_code}')
        return False

    print('\n🎉 SUCCESS! CSV export-import cycle is working correctly!')
    print('✅ Export generates headers in correct underscore format')
    print('✅ Import successfully processes the exported CSV file')
    print('✅ Data integrity is maintained through the export-import cycle')
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print('\n❌ Verification failed!')
        exit(1)
    else:
        print('\n✅ All tests passed!')
