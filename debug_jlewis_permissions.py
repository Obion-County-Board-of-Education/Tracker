#!/usr/bin/env python3
"""
Debug script to test permissions for jlewis@ocboe.com specifically
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))

from ocs_shared_models.models import GroupRole

# Import from the portal directory
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))
from database import SessionLocal
from auth_service import AuthenticationService

def test_jlewis_permissions():
    """Test what permissions jlewis@ocboe.com would get with different Azure AD attributes"""
    
    session = SessionLocal()
    auth_service = AuthenticationService(session)
    
    print("🔍 Debugging permissions for jlewis@ocboe.com")
    print("=" * 60)
    
    # First, let's see what roles exist in the database
    print("\n📋 Current Group Roles in Database:")
    roles = session.query(GroupRole).all()
    for role in roles:
        print(f"  - {role.group_name}: {role.access_level}")
        if role.azure_user_attribute:
            print(f"    Special attribute: {role.azure_user_attribute}={role.azure_user_attribute_value}")
        print(f"    Tickets: {role.tickets_access}, Inventory: {role.inventory_access}")
        print(f"    Purchasing: {role.purchasing_access}, Forms: {role.forms_access}")
        print()
    
    # Simulate user data for jlewis@ocboe.com
    user_data = {
        'id': 'test-user-id-jlewis',
        'mail': 'jlewis@ocboe.com',
        'userPrincipalName': 'jlewis@ocboe.com',
        'displayName': 'John Lewis',
        'extensionAttribute10': None  # Start with no special attribute
    }
    
    # Test scenarios
    scenarios = [
        {
            'name': 'No Groups, No Extension Attribute',
            'groups': [],
            'extension_attr': None
        },
        {
            'name': 'Director of Schools Extension Attribute',
            'groups': [],
            'extension_attr': 'Director of Schools'
        },
        {
            'name': 'Technology Department Group',
            'groups': [{'id': 'tech-group-id', 'displayName': 'Technology Department'}],
            'extension_attr': None
        },
        {
            'name': 'All Staff Group',
            'groups': [{'id': 'staff-group-id', 'displayName': 'All_Staff'}],
            'extension_attr': None
        },
        {
            'name': 'Finance Group',
            'groups': [{'id': 'finance-group-id', 'displayName': 'Finance'}],
            'extension_attr': None
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🧪 Testing Scenario: {scenario['name']}")
        print("-" * 40)
        
        # Update user data for this scenario
        test_user_data = user_data.copy()
        test_user_data['extensionAttribute10'] = scenario['extension_attr']
        
        # Determine permissions
        permissions = auth_service.determine_user_permissions(test_user_data, scenario['groups'])
        
        print(f"  Access Level: {permissions['access_level']}")
        print(f"  Tickets Access: {permissions['tickets_access']}")
        print(f"  Inventory Access: {permissions['inventory_access']}")
        print(f"  Purchasing Access: {permissions['purchasing_access']}")
        print(f"  Forms Access: {permissions['forms_access']}")
        print(f"  Matched Groups: {permissions['matched_groups']}")
        print(f"  Services: {permissions['services']}")
        
        if permissions['access_level'] == 'super_admin':
            print("  ✅ Super Admin Access Granted!")
        elif permissions['access_level'] == 'none':
            print("  ❌ No Access - User would be denied")
        else:
            print(f"  ⚠️  Limited Access: {permissions['access_level']}")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("🎯 Key Findings:")
    print("1. For super admin access, jlewis@ocboe.com needs either:")
    print("   - extensionAttribute10='Director of Schools' in Azure AD")
    print("   - Membership in 'Technology Department' Azure AD group")
    print("   - Membership in 'Finance' Azure AD group (admin level)")
    print("2. Check the actual Azure AD attributes for this user")
    print("3. Verify the user is in the correct Azure AD groups")

if __name__ == "__main__":
    test_jlewis_permissions()
