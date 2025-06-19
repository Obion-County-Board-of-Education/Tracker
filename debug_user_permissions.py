#!/usr/bin/env python3
"""
Debug user permissions for jlewis and alewis
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))

from database import get_db_session
from ocs_shared_models.models import GroupRole
from auth_service import AuthenticationService

def debug_user_permissions():
    """Debug what permissions these users should have"""
    
    # Mock user data for testing
    test_users = {
        'jlewis@ocboe.com': {
            'user_data': {
                'mail': 'jlewis@ocboe.com',
                'displayName': 'Joseph Lewis',
                'extensionAttribute10': None
            },
            'groups_data': [
                {'id': 'staff-group-id', 'displayName': 'All_Staff'}
            ]
        },
        'alewis@ocboe.com': {
            'user_data': {
                'mail': 'alewis@ocboe.com', 
                'displayName': 'Adam Lewis',
                'extensionAttribute10': None
            },
            'groups_data': [
                {'id': 'staff-group-id', 'displayName': 'All_Staff'}
            ]
        }
    }
    
    try:
        with get_db_session() as db:
            auth_service = AuthenticationService(db)
            
            for email, data in test_users.items():
                print(f"\n=== Testing {email} ===")
                
                user_data = data['user_data']
                groups_data = data['groups_data']
                
                # Test permission determination
                permissions = auth_service.determine_user_permissions(user_data, groups_data)
                
                print(f"Permissions: {permissions}")
                
                # Test menu visibility logic manually
                access_level = permissions.get('access_level', 'none')
                
                menu_visibility = {
                    'tickets': permissions.get('tickets_access', 'none') != 'none',
                    'purchasing': permissions.get('purchasing_access', 'none') != 'none',
                    'inventory': permissions.get('inventory_access', 'none') != 'none' and access_level in ['admin', 'super_admin'],
                    'forms': permissions.get('forms_access', 'none') != 'none' and access_level in ['admin', 'super_admin'],
                    'manage': access_level in ['admin', 'super_admin'],
                    'admin': access_level in ['admin', 'super_admin']
                }
                
                print(f"Menu visibility: {menu_visibility}")
                
                # Check what should be visible
                visible_items = [item for item, visible in menu_visibility.items() if visible]
                print(f"Should see: {visible_items}")
                
                if not visible_items:
                    print("❌ NO MENU ITEMS VISIBLE - This is the problem!")
                    
                    # Debug further
                    print("\nDebugging...")
                    print(f"  Access level: {access_level}")
                    print(f"  Tickets access: {permissions.get('tickets_access')}")
                    print(f"  Purchasing access: {permissions.get('purchasing_access')}")
                    print(f"  Matched groups: {permissions.get('matched_groups')}")
                else:
                    print(f"✅ Should see {len(visible_items)} menu items: {visible_items}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def check_group_role_setup():
    """Check if the GroupRole setup is correct"""
    print("\n=== Checking GroupRole Setup ===")
    
    try:
        with get_db_session() as db:
            all_staff_role = db.query(GroupRole).filter(GroupRole.group_name == 'All_Staff').first()
            
            if all_staff_role:
                print(f"✅ All_Staff role found:")
                print(f"  Group name: {all_staff_role.group_name}")
                print(f"  Access level: {all_staff_role.access_level}")
                print(f"  Tickets access: {all_staff_role.tickets_access}")
                print(f"  Purchasing access: {all_staff_role.purchasing_access}")
                print(f"  Inventory access: {all_staff_role.inventory_access}")
                print(f"  Forms access: {all_staff_role.forms_access}")
                print(f"  Azure group ID: {all_staff_role.azure_group_id}")
            else:
                print("❌ All_Staff role not found!")
                
            # Check all roles
            all_roles = db.query(GroupRole).all()
            print(f"\nAll {len(all_roles)} roles in database:")
            for role in all_roles:
                print(f"  {role.group_name}: {role.access_level} / tickets:{role.tickets_access} / purchasing:{role.purchasing_access}")
                
    except Exception as e:
        print(f"Error checking group roles: {e}")

if __name__ == "__main__":
    check_group_role_setup()
    debug_user_permissions()
