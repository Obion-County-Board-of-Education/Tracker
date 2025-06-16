#!/usr/bin/env python3
"""
Setup script to create proper group role mappings in the database.
This ensures users get appropriate permissions based on their Azure AD groups.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))

from ocs_shared_models.models import GroupRole
# Import from the correct location 
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))
from database import SessionLocal

def setup_group_roles():
    """Set up the proper group role mappings"""
    session = SessionLocal()
    
    try:
        # Clear existing roles
        session.query(GroupRole).delete()
        
        # Define proper group roles based on auth.md
        group_roles = [
            # All Staff - Limited access to tickets and purchasing only
            {
                'group_name': 'All_Staff',
                'azure_group_id': None,  # Will be filled when we get the actual group ID
                'access_level': 'staff',
                'tickets_access': 'write',
                'inventory_access': 'none',
                'purchasing_access': 'write',
                'forms_access': 'none',
                'allowed_departments': []
            },
            
            # All Students - Very limited access, tickets only
            {
                'group_name': 'All_Students', 
                'azure_group_id': None,
                'access_level': 'student',
                'tickets_access': 'write',
                'inventory_access': 'none',
                'purchasing_access': 'none',
                'forms_access': 'none',
                'allowed_departments': []
            },
            
            # Technology Department - Full admin access
            {
                'group_name': 'Technology Department',
                'azure_group_id': None,
                'access_level': 'super_admin',
                'tickets_access': 'admin',
                'inventory_access': 'admin',
                'purchasing_access': 'admin',
                'forms_access': 'admin',
                'allowed_departments': ['Technology']
            },
            
            # Finance - Admin access to purchasing, tickets, and forms
            {
                'group_name': 'Finance',
                'azure_group_id': None,
                'access_level': 'admin',
                'tickets_access': 'read',
                'inventory_access': 'read',
                'purchasing_access': 'admin',
                'forms_access': 'admin',
                'allowed_departments': ['Finance']
            }
        ]
        
        # Special role for Director of Schools (via extensionAttribute10)
        director_role = GroupRole(
            group_name='Director of Schools',
            azure_group_id=None,
            azure_user_attribute='extensionAttribute10',
            azure_user_attribute_value='Director of Schools',
            access_level='super_admin',
            tickets_access='admin',
            inventory_access='admin',
            purchasing_access='admin',
            forms_access='admin',
            allowed_departments=['Administration']
        )
        
        # Add all group roles
        for role_data in group_roles:
            role = GroupRole(**role_data)
            session.add(role)
        
        # Add director role
        session.add(director_role)
        
        # Commit changes
        session.commit()
        
        print("✅ Group roles setup complete!")
        print("\nConfigured roles:")
        
        roles = session.query(GroupRole).all()
        for role in roles:
            print(f"  - {role.group_name}: {role.access_level} access")
            print(f"    Tickets: {role.tickets_access}, Purchasing: {role.purchasing_access}")
            if role.azure_user_attribute:
                print(f"    Special attribute: {role.azure_user_attribute}={role.azure_user_attribute_value}")
            print()
            
    except Exception as e:
        print(f"❌ Error setting up group roles: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    setup_group_roles()
