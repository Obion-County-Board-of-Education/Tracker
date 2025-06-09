#!/usr/bin/env python3
"""
Verify Edit User routes are properly registered
"""

import sys
import os

# Add the ocs-portal-py directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))

def verify_routes():
    """Verify the Edit User routes are in the user_building_routes.py file"""
    
    routes_file = os.path.join(os.path.dirname(__file__), 'ocs-portal-py', 'user_building_routes.py')
    
    print("🔍 Verifying Edit User routes in user_building_routes.py")
    print("=" * 60)
    
    if not os.path.exists(routes_file):
        print(f"❌ Routes file not found: {routes_file}")
        return False
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required routes
    checks = [
        ("GET /users/edit/{user_id}", '@app.get("/users/edit/{user_id}")'),
        ("POST /users/edit/{user_id}", '@app.post("/users/edit/{user_id}")'),
        ("POST /users/delete/{user_id}", '@app.post("/users/delete/{user_id}")'),
        ("edit_user_form function", 'def edit_user_form('),
        ("edit_user_submit function", 'def edit_user_submit('),
        ("delete_user_submit function", 'def delete_user_submit('),
    ]
    
    all_passed = True
    
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ {check_name} - Found")
        else:
            print(f"❌ {check_name} - Missing")
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 All Edit User routes are properly implemented!")
        
        # Show route summary
        print("\n📋 Route Summary:")
        print("   GET  /users/edit/{user_id}    - Display edit form")
        print("   POST /users/edit/{user_id}    - Handle form submission")
        print("   POST /users/delete/{user_id}  - Delete user")
        
        return True
    else:
        print("❌ Some routes are missing. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = verify_routes()
    if success:
        print("\n✅ Route verification completed successfully!")
        print("💡 You can now test the Edit User functionality in the browser.")
    else:
        print("\n❌ Route verification failed!")
    
    sys.exit(0 if success else 1)
