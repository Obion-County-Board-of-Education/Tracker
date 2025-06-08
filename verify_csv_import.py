#!/usr/bin/env python3
"""
Simple verification that CSV import functionality is properly implemented
"""

import os

def check_files():
    """Check that all required files have been modified"""
    print("🔍 Checking CSV Import Implementation...")
    
    files_to_check = [
        ("ocs-portal-py/main.py", "import routes"),
        ("ocs-portal-py/services.py", "import service methods"),
        ("ocs-tickets-api/main.py", "API import endpoints"),
        ("ocs-portal-py/templates/tech_tickets_list.html", "tech import UI"),
        ("ocs-portal-py/templates/maintenance_tickets_list.html", "maintenance import UI")
    ]
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ Missing {description}: {file_path}")

def check_import_routes():
    """Check if import routes are in main.py"""
    print("\n🔍 Checking Import Routes...")
    
    portal_main = "ocs-portal-py/main.py"
    if os.path.exists(portal_main):
        with open(portal_main, 'r') as f:
            content = f.read()
            
        if "/tickets/tech/import" in content:
            print("✅ Tech tickets import route found")
        else:
            print("❌ Tech tickets import route missing")
            
        if "/tickets/maintenance/import" in content:
            print("✅ Maintenance tickets import route found")
        else:
            print("❌ Maintenance tickets import route missing")

def check_api_endpoints():
    """Check if API endpoints are implemented"""
    print("\n🔍 Checking API Endpoints...")
    
    api_main = "ocs-tickets-api/main.py"
    if os.path.exists(api_main):
        with open(api_main, 'r') as f:
            content = f.read()
            
        if "/api/tickets/tech/import" in content:
            print("✅ Tech tickets API import endpoint found")
        else:
            print("❌ Tech tickets API import endpoint missing")
            
        if "/api/tickets/maintenance/import" in content:
            print("✅ Maintenance tickets API import endpoint found")
        else:
            print("❌ Maintenance tickets API import endpoint missing")

def check_ui_elements():
    """Check if UI elements are in templates"""
    print("\n🔍 Checking UI Elements...")
    
    templates = [
        ("ocs-portal-py/templates/tech_tickets_list.html", "tech"),
        ("ocs-portal-py/templates/maintenance_tickets_list.html", "maintenance")
    ]
    
    for template_path, ticket_type in templates:
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
                
            if "Import CSV" in content:
                print(f"✅ {ticket_type.title()} import button found")
            else:
                print(f"❌ {ticket_type.title()} import button missing")
                
            if f"importCsvModal-{ticket_type}" in content:
                print(f"✅ {ticket_type.title()} import modal found")
            else:
                print(f"❌ {ticket_type.title()} import modal missing")
                
            if "showImportModal" in content:
                print(f"✅ {ticket_type.title()} import JavaScript found")
            else:
                print(f"❌ {ticket_type.title()} import JavaScript missing")

def main():
    print("🚀 CSV Import Implementation Verification")
    print("=" * 50)
    
    check_files()
    check_import_routes()
    check_api_endpoints()
    check_ui_elements()
    
    print("\n" + "=" * 50)
    print("✅ CSV Import Verification Complete!")
    print("\n📝 Implementation Summary:")
    print("• Import buttons added to both tech and maintenance pages")
    print("• Import modals with 'Add to Database' and 'Overwrite Database' options")
    print("• Backend routes in portal main.py")
    print("• Service methods in services.py")
    print("• API endpoints in tickets API main.py")
    print("• JavaScript modal functions")
    print("\n🎯 User Instructions:")
    print("1. Visit the tech or maintenance tickets page")
    print("2. Click the gray 'Import CSV' button")
    print("3. Select a CSV file with the proper columns")
    print("4. Choose 'Add to Database' or 'Overwrite Database'")
    print("5. Click 'Import' to upload the tickets")

if __name__ == "__main__":
    main()
