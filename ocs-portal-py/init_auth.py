"""
Initialize default group roles for OCS authentication system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ocs_shared_models'))

from sqlalchemy.orm import Session
from models import GroupRole
from database import get_db

def create_default_group_roles():
    """Create the default group role mappings as specified in auth.md"""
    
    db = next(get_db())
    
    try:
        # Check if roles already exist
        existing_roles = db.query(GroupRole).count()
        
        if existing_roles > 0:
            print(f"Found {existing_roles} existing group roles. Skipping initialization.")
            return
        
        # Default group role mappings
        default_roles = [
            {
                "group_name": "Technology Department",
                "access_level": "super_admin",
                "tickets_access": "admin",
                "inventory_access": "admin", 
                "purchasing_access": "admin",
                "forms_access": "admin",
                "allowed_departments": ["All"]
            },
            {
                "group_name": "Director of Schools",
                "azure_user_attribute": "extensionAttribute10",
                "azure_user_attribute_value": "Director of Schools",
                "access_level": "super_admin",
                "tickets_access": "admin",
                "inventory_access": "admin",
                "purchasing_access": "admin", 
                "forms_access": "admin",
                "allowed_departments": ["All"]
            },
            {
                "group_name": "Finance",
                "access_level": "super_admin",
                "tickets_access": "admin",
                "inventory_access": "admin",
                "purchasing_access": "admin",
                "forms_access": "admin",
                "allowed_departments": ["All"]
            },
            {
                "group_name": "All_Staff",
                "access_level": "staff",
                "tickets_access": "write",
                "inventory_access": "read",
                "purchasing_access": "write",
                "forms_access": "write",
                "allowed_departments": []
            },
            {
                "group_name": "All_Students",
                "access_level": "student", 
                "tickets_access": "write",
                "inventory_access": "none",
                "purchasing_access": "none",
                "forms_access": "none",
                "allowed_departments": []
            }
        ]
        
        # Create group roles
        for role_data in default_roles:
            group_role = GroupRole(**role_data)
            db.add(group_role)
            print(f"Created group role: {role_data['group_name']}")
        
        db.commit()
        print("✅ Default group roles created successfully!")
        
        # Display created roles
        print("\n📋 Created Group Roles:")
        print("-" * 80)
        roles = db.query(GroupRole).all()
        for role in roles:
            print(f"Group: {role.group_name}")
            print(f"  Access Level: {role.access_level}")
            print(f"  Tickets: {role.tickets_access}")
            print(f"  Inventory: {role.inventory_access}")
            print(f"  Purchasing: {role.purchasing_access}")
            print(f"  Forms: {role.forms_access}")
            if role.azure_user_attribute:
                print(f"  Attribute Match: {role.azure_user_attribute}={role.azure_user_attribute_value}")
            print()
            
    except Exception as e:
        print(f"❌ Error creating group roles: {str(e)}")
        db.rollback()
        
    finally:
        db.close()

if __name__ == "__main__":
    create_default_group_roles()
