#!/usr/bin/env python3
"""
Azure AD User Diagnostic Script
This script helps diagnose what Azure AD attributes and groups a user has.
"""
import sys
import os

print("""
🔍 OCS Tracker - Azure AD User Permission Diagnostic
================================================================

This script helps diagnose why jlewis@ocboe.com might not have super admin access.

CURRENT ISSUE: User is not getting the expected super admin permissions

ROOT CAUSES & SOLUTIONS:
================================================================

1. 🎯 USER NEEDS AZURE AD EXTENSION ATTRIBUTE
   
   For "Director of Schools" super admin access:
   - User's extensionAttribute10 must be set to "Director of Schools"
   - This is configured in Azure AD user profile
   
   To fix in Azure AD:
   - Go to Azure AD > Users > jlewis@ocboe.com
   - Edit user profile
   - Set extensionAttribute10 = "Director of Schools"

2. 🎯 USER NEEDS AZURE AD GROUP MEMBERSHIP
   
   Alternative super admin access paths:
   - Add user to "Technology Department" Azure AD group (super_admin)
   - Add user to "Finance" Azure AD group (admin level)
   
   To fix in Azure AD:
   - Go to Azure AD > Groups
   - Find "Technology Department" group
   - Add jlewis@ocboe.com as member

3. 🎯 CHECK CURRENT USER ATTRIBUTES
   
   When user logs in, check the debug logs to see:
   - What groups they're actually in
   - What extension attributes they have
   - What permissions are calculated

VERIFICATION STEPS:
================================================================

1. In Azure AD Portal:
   ✅ Verify jlewis@ocboe.com exists
   ✅ Check extensionAttribute10 value
   ✅ Check group memberships
   ✅ Verify groups exist: "Technology Department", "Finance", "All_Staff"

2. In OCS Portal Logs:
   ✅ Look for DEBUG lines showing:
      - "Determining permissions for jlewis@ocboe.com"
      - "User groups: [...]"
      - "Extension attribute 10: '...'"
      - "Matched by..." or "No group matches found"

3. Test Login:
   ✅ Have user log in to OCS Portal
   ✅ Check what permissions they receive
   ✅ Verify access level in session

QUICK FIXES:
================================================================

OPTION A - Extension Attribute (Recommended for Director):
1. Azure AD > Users > jlewis@ocboe.com > Properties
2. Set extensionAttribute10 = "Director of Schools"
3. Save changes
4. User logs out and back in

OPTION B - Group Membership (Alternative):
1. Azure AD > Groups > Technology Department
2. Add jlewis@ocboe.com as member
3. User logs out and back in

OPTION C - Check Current Status:
1. Start OCS Portal with DEBUG logging
2. Have user attempt login
3. Check logs for permission calculation
4. Verify what Azure AD is returning

================================================================
Next Steps: Choose Option A or B above to grant super admin access.
""")

if __name__ == "__main__":
    print("Run this script to see the diagnostic information above.")
    print("No code execution required - this is a reference guide.")
