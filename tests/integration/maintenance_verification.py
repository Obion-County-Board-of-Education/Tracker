#!/usr/bin/env python3
"""
Maintenance tickets CSV export-import verification
"""

import requests

def main():
    print('🔍 Testing Maintenance Tickets CSV Export-Import...')

    # Create test maintenance ticket
    test_data = {
        'title': 'Maintenance CSV Test',
        'description': 'Testing maintenance tickets CSV export-import cycle',
        'issue_type': 'Electrical',
        'building_name': 'Central Office',
        'room_name': 'Main Office',
        'created_by': 'System Test'
    }

    response = requests.post('http://localhost:8000/api/tickets/maintenance', json=test_data)
    if response.status_code == 200:
        print('✅ Maintenance test ticket created')
    else:
        print(f'❌ Failed to create maintenance ticket: {response.status_code}')
        return False

    # Export maintenance tickets CSV
    response = requests.get('http://localhost:8000/api/tickets/maintenance/export')
    if response.status_code == 200:
        print('✅ Maintenance CSV export successful')
        
        # Check headers
        lines = response.text.strip().split('\n')
        headers = lines[0].split(',')
        print(f'📋 Headers: {headers[:5]}...')
        
        # Verify underscore format
        expected_headers = ['id', 'title', 'description', 'issue_type', 'school']
        if all(h in headers for h in expected_headers):
            print('✅ Maintenance headers are in correct underscore format')
        else:
            print('❌ Maintenance headers still in wrong format')
            return False
            
        # Save and import
        with open('maintenance_verification_export.csv', 'w') as f:
            f.write(response.text)
        print('💾 Saved maintenance CSV')
        
        # Clear and import
        requests.delete('http://localhost:8000/api/tickets/maintenance/clear')
        
        with open('maintenance_verification_export.csv', 'rb') as f:
            files = {'file': ('maintenance_test.csv', f, 'text/csv')}
            data = {'operation': 'overwrite'}
            
            response = requests.post('http://localhost:8000/api/tickets/maintenance/import', 
                                   files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Maintenance CSV import successful: {result.get("imported_count", "unknown")} tickets')
        else:
            print(f'❌ Maintenance CSV import failed: {response.status_code}')
            return False
            
    print('✅ Maintenance tickets CSV export-import cycle working correctly!')
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
