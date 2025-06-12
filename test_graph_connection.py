#!/usr/bin/env python
"""
MS Graph API Connection Test Script

This script tests the connection to Microsoft Graph API using the credentials from .env file
and verifies access to specific Azure AD groups: All_Staff, All_Students, Technology Department,
Director of Schools, and Finance.

Usage:
    python test_graph_connection.py
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("ocs-portal-py/.env")

# Get Azure AD credentials from environment variables
client_id = os.environ.get("AZURE_CLIENT_ID")
client_secret = os.environ.get("AZURE_CLIENT_SECRET")
tenant_id = os.environ.get("AZURE_TENANT_ID")

# Target groups to check by name (we'll use name matching since IDs may be different)
TARGET_GROUPS = [
    "All_Staff", 
    "All Staff",
    "All_Students",
    "All Students",
    "Technology",
    "Technology Department",
    "Director",
    "Director of Schools",
    "Finance"
]

def get_access_token():
    """
    Get an access token for Microsoft Graph API using client credentials flow.
    """
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    print(f"Requesting access token for tenant: {tenant_id}...")
    print(f"Client ID: {client_id[:5]}...{client_id[-5:]} (redacted for security)")
    
    try:
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code == 200:
            token_json = token_response.json()
            access_token = token_json.get('access_token')
            print("✅ Successfully obtained access token")
            
            # Print token details (not the token itself)
            try:
                import jwt
                # Try to decode the token to get more information
                token_parts = access_token.split('.')
                if len(token_parts) >= 2:
                    # Decode middle part without verification
                    padded = token_parts[1] + "=" * (4 - len(token_parts[1]) % 4)
                    import base64
                    decoded = base64.b64decode(padded)
                    token_claims = json.loads(decoded)
                    print(f"   Token issued for: {token_claims.get('aud', 'unknown')}")
                    print(f"   Token scopes: {token_claims.get('scp', token_claims.get('roles', 'No scopes/roles found'))}")
                    if 'exp' in token_claims:
                        from datetime import datetime
                        exp_time = datetime.fromtimestamp(token_claims['exp'])
                        print(f"   Token expires: {exp_time}")
                    print("   If no roles are listed, your app may not have application permissions properly granted.")
            except ImportError:
                print("   Note: Install PyJWT package for token details")
            except Exception as e:
                print(f"   Could not decode token details: {str(e)}")
                
            return access_token
        else:
            print("❌ Failed to obtain access token")
            print(f"   Status code: {token_response.status_code}")
            print(f"   Error details: {token_response.text}")
            
            if token_response.status_code == 401:
                print("   This may indicate incorrect client credentials or tenant ID")
            elif "invalid_scope" in token_response.text:
                print("   This may indicate a permission issue - check API permissions")
            elif "AADSTS500011" in token_response.text or "AADSTS700016" in token_response.text:
                print("   This may indicate the application has not been properly consented")
                
            return None
    except Exception as e:
        print(f"❌ Exception during token request: {str(e)}")
        return None

def list_all_groups(access_token):
    """
    List all groups in the Azure AD tenant using pagination to get more than the default limit.
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    graph_url = "https://graph.microsoft.com/v1.0/groups?$top=999"  # Request maximum allowed in one page
    all_groups = []
    
    print("\nFetching all groups from Azure AD (with pagination)...")
    print(f"Request URL: {graph_url}")
    print("Request Headers: Authorization: Bearer [REDACTED]")
    
    try:
        # Continue fetching groups until there are no more pages
        while graph_url:
            response = requests.get(graph_url, headers=headers)
            
            if response.status_code == 200:
                groups_data = response.json()
                page_groups = groups_data.get('value', [])
                all_groups.extend(page_groups)
                print(f"  Retrieved {len(page_groups)} groups in this page")
                
                # Check if there are more pages
                graph_url = groups_data.get('@odata.nextLink')
            else:
                graph_url = None
                raise Exception(f"Failed to retrieve groups: {response.status_code}")
        
        print(f"✅ Successfully retrieved a total of {len(all_groups)} groups")
        
        # Let's also filter for groups that might contain staff, students, etc.
        print("\nSearching for potentially relevant groups:")
        keywords = ['staff', 'student', 'tech', 'director', 'finance', 'admin']
        relevant_groups = []
        
        for group in all_groups:
            name = group.get('displayName', '').lower()
            if any(keyword in name for keyword in keywords):
                relevant_groups.append(group)
        
        print(f"Found {len(relevant_groups)} potentially relevant groups")
        if relevant_groups:
            print("Relevant groups:")
            for i, group in enumerate(relevant_groups[:20], 1):
                print(f"   {i}. {group.get('displayName')} (ID: {group.get('id')})")
                
        # Print the first 10 groups to help with debugging
        print("\nFirst 10 groups in the tenant:")
        for i, group in enumerate(all_groups[:10], 1):
            print(f"   {i}. {group.get('displayName')} (ID: {group.get('id')})")
            
        return all_groups
    else:
            print("❌ Failed to retrieve groups")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 401:
                print("   ERROR: Unauthorized - Token might be invalid or expired")
            elif response.status_code == 403:
                print("   ERROR: Forbidden - Application doesn't have Group.Read.All permission")
                print("   Solution: Make sure Group.Read.All permission is granted and admin consent is provided")
                print("   Admin consent URL: https://login.microsoftonline.com/{tenant_id}/adminconsent?client_id={client_id}")
            
            # Try an alternative endpoint to check basic connectivity
            print("\nAttempting to call /me endpoint to check basic API access...")
            try:
                me_response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
                print(f"   /me Status code: {me_response.status_code}")
                print(f"   /me Response: {me_response.text}")
                if "client_credentials" in me_response.text or me_response.status_code == 401:
                    print("   Note: The /me endpoint doesn't work with application permissions (only delegated)")
            except Exception as e:
                print(f"   Error checking /me endpoint: {str(e)}")
                
            return []
    except Exception as e:
        print(f"❌ Exception while fetching groups: {str(e)}")
        return []

def check_target_groups(groups):
    """
    Check if target groups exist in the retrieved groups list using name matching.
    """
    print("\nChecking for target groups by name:")
    found_groups = []
    group_ids = {}
    
    # Create a list of all display names for easier searching
    all_groups_by_name = {group.get('displayName', '').lower(): group for group in groups}
    
    # Try to find exact or partial matches
    for target in TARGET_GROUPS:
        target_lower = target.lower()
        found = False
        
        # First try exact match
        if target_lower in all_groups_by_name:
            group = all_groups_by_name[target_lower]
            found = True
        else:
            # Try partial match
            for display_name, group in all_groups_by_name.items():
                if target_lower in display_name or display_name in target_lower:
                    found = True
                    break
        
        if found:
            group_id = group.get('id')
            display_name = group.get('displayName')
            found_groups.append(target)
            group_ids[target] = group_id
            print(f"✅ Found group: {display_name} (ID: {group_id})")
        else:
            print(f"❌ Could not find group: {target}")
    
    # Print potential groups that might be what we're looking for
    if len(found_groups) < len(TARGET_GROUPS):
        print("\nPotential groups that might match (showing first 20 groups):")
        for i, group in enumerate(groups[:20], 1):
            print(f"   {i}. {group.get('displayName')} (ID: {group.get('id')})")
    
    return found_groups, group_ids

def check_group_members(access_token, group_ids):
    """
    Check access to members of each found group.
    """
    if not group_ids:
        print("\n❌ No groups found to check members")
        return
    
    print("\nChecking access to group members:")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    for group_name, group_id in group_ids.items():
        graph_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members?$top=5"
        
        print(f"\nFetching members for group '{group_name}' (limited to 5)...")
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            members_data = response.json()
            members = members_data.get('value', [])
            member_count = len(members)
            
            print(f"✅ Successfully accessed members for '{group_name}'")
            print(f"   Retrieved {member_count} members (limited to 5)")
            
            if member_count > 0:
                print("   Sample members:")
                for i, member in enumerate(members[:3], 1):
                    print(f"   {i}. {member.get('displayName', 'Unknown')} ({member.get('userPrincipalName', 'No UPN')})")
                if member_count > 3:
                    print(f"   ... and {member_count - 3} more")
        else:
            print(f"❌ Failed to access members for '{group_name}'")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text}")

def test_user_attributes(access_token):
    """
    Test access to user attributes including extensionAttribute10 and officeLocation.
    """
    print("\nChecking access to user attributes (extensionAttribute10 and officeLocation)...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Fetch one user to test attribute access
    graph_url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,mail,jobTitle,officeLocation,department,accountEnabled,onPremisesExtensionAttributes&$top=1"
    
    response = requests.get(graph_url, headers=headers)
    
    if response.status_code == 200:
        users_data = response.json()
        users = users_data.get('value', [])
        
        if users:
            user = users[0]
            print("✅ Successfully accessed user attributes")
            print(f"   Sample user: {user.get('displayName')}")
            
            # Check for required attributes
            extension_attrs = user.get('onPremisesExtensionAttributes', {})
            if extension_attrs and 'extensionAttribute10' in extension_attrs:
                print("✅ Can access extensionAttribute10")
            else:
                print("❌ Cannot access extensionAttribute10")
            
            if 'officeLocation' in user:
                print(f"✅ Can access officeLocation: {user.get('officeLocation', 'Not set')}")
            else:
                print("❌ Cannot access officeLocation")
        else:
            print("⚠️ No users found to check attributes")
    else:
        print("❌ Failed to access user attributes")
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 403:
            print("   ERROR: Forbidden - Application doesn't have User.Read.All permission")
            print("   Solution: Make sure User.Read.All permission is granted and admin consent is provided")

def check_api_permissions(access_token):
    """
    Check which API permissions the application effectively has.
    """
    print("\nDiagnostic: Checking effective API permissions...")
    
    endpoints_to_test = [
        {
            "url": "https://graph.microsoft.com/v1.0/groups?$top=1",
            "description": "Read groups (requires Group.Read.All)",
            "permission": "Group.Read.All"
        },
        {
            "url": "https://graph.microsoft.com/v1.0/users?$top=1",
            "description": "Read users (requires User.Read.All)",
            "permission": "User.Read.All"
        },
        {
            "url": "https://graph.microsoft.com/v1.0/applications?$top=1",
            "description": "Read applications (requires Application.Read.All)",
            "permission": "Application.Read.All"
        }
    ]
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print("\nPermission Test Results:")
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(endpoint["url"], headers=headers)
            if response.status_code == 200:
                print(f"   ✅ {endpoint['description']}: SUCCESS")
            else:
                print(f"   ❌ {endpoint['description']}: FAILED ({response.status_code})")
                if response.status_code == 403:
                    print(f"      Missing permission: {endpoint['permission']}")
        except Exception as e:
            print(f"   ❌ {endpoint['description']}: ERROR - {str(e)}")

    print("\nIf groups access failed but users succeeded, you are missing Group.Read.All permission.")
    print("You must add this permission in the Azure Portal and grant admin consent.")

def main():
    """
    Main function to test Microsoft Graph API connectivity.
    """
    print("=" * 80)
    print("MICROSOFT GRAPH API CONNECTION TEST")
    print("=" * 80)
    
    # Validate environment variables
    if not all([client_id, client_secret, tenant_id]):
        print("❌ Missing required environment variables. Please check your .env file.")
        print(f"   AZURE_CLIENT_ID: {'✅ Set' if client_id else '❌ Missing'}")
        print(f"   AZURE_CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Missing'}")
        print(f"   AZURE_TENANT_ID: {'✅ Set' if tenant_id else '❌ Missing'}")
        return
    
    # Print diagnostic information
    print("\nEnvironment Information:")
    print(f"   Python version: {os.sys.version.split()[0]}")
    print(f"   Requests version: {requests.__version__}")
    print(f"   Environment file: ocs-portal-py/.env")
    
    # Verify environment variable length as a sanity check
    print("\nValidating credential format:")
    print(f"   Client ID format valid: {'✅ Yes' if len(client_id) > 20 else '❌ No - Unexpected length'}")
    print(f"   Client Secret format valid: {'✅ Yes' if len(client_secret) > 10 else '❌ No - Unexpected length'}")
    print(f"   Tenant ID format valid: {'✅ Yes' if len(tenant_id) > 20 else '❌ No - Unexpected length'}")
    
    print("\nRequired Permissions for this test:")
    print("   • Group.Read.All - For reading groups and memberships")
    print("   • User.Read.All - For reading user attributes")
    print("   Note: Admin consent must be granted for these permissions")
      # Get access token
    access_token = get_access_token()
    if not access_token:
        return
        
    # Check API permissions (diagnostic)
    check_api_permissions(access_token)
    
    # List all groups
    groups = list_all_groups(access_token)
    if not groups:
        print("\n❌ Failed to retrieve groups. This is likely due to permission issues.")
        print("Common solutions:")
        print("1. Verify Group.Read.All permission is added to the application")
        print("2. Ensure admin consent has been granted for the permission")
        print("3. Check that the groups actually exist in your Azure AD tenant")
        print("4. Verify the application is registered in the correct tenant")
        print("\nWould you like to continue testing other functions? (y/n)")
        response = input().lower().strip()
        if response != 'y':
            return
    
    # Check target groups
    found_groups, group_ids = check_target_groups(groups)
    
    # Check group members
    check_group_members(access_token, group_ids)
    
    # Test access to user attributes
    test_user_attributes(access_token)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total groups found: {len(groups)}")
    print(f"Target groups found: {len(found_groups)} of {len(TARGET_GROUPS)}")
    
    if len(found_groups) == len(TARGET_GROUPS):
        print("\n✅ SUCCESS: All required groups were found and accessible.")
    else:
        print("\n⚠️ WARNING: Some required groups could not be found.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
