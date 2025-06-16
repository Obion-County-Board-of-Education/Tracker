#!/usr/bin/env python3
"""
Check existing GroupRole mappings in the database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))

from database import get_db_session
from ocs_shared_models.models import GroupRole

def check_group_roles():
    try:
        with get_db_session() as db:
            # Check all existing group roles
            roles = db.query(GroupRole).all()
            print('Existing GroupRole mappings:')
            if not roles:
                print('  No GroupRole mappings found in database!')
            else:
                for role in roles:
                    print(f'  Group: "{role.group_name}" -> Access: {role.access_level}, Tickets: {role.tickets_access}, Purchasing: {role.purchasing_access}')
            
            # Check specifically for variations of staff group
            staff_variations = ['All_Staff', 'all_staff', 'ALL_STAFF', 'All Staff', 'all staff']
            print('\nChecking for staff group variations:')
            found_staff = False
            for variation in staff_variations:
                role = db.query(GroupRole).filter(GroupRole.group_name == variation).first()
                if role:
                    print(f'  Found: "{variation}" -> Access: {role.access_level}, Tickets: {role.tickets_access}, Purchasing: {role.purchasing_access}')
                    found_staff = True
            
            if not found_staff:
                print('  No staff group variations found!')
                
    except Exception as e:
        print(f"Error checking group roles: {e}")

if __name__ == "__main__":
    check_group_roles()
