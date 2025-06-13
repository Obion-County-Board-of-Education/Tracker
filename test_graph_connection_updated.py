#!/usr/bin/env python
"""
MS Graph API Connection Test Script

This script tests the connection to Microsoft Graph API using the credentials from .env file
and verifies access to specific Azure AD groups needed for the OCS Tracker application.

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

# Target groups to check with their updated object IDs
# These were identified using the search_ad_groups.py script
TARGET_GROUPS = {
    "All_Staff": "1a5462fc-7e89-4517-be54-2ce79b44e12a",  # Found exact match
    "All_Students": "f4ee1bf4-901c-43bb-a380-935540b0832d",  # This might need updating
    "Technology Department": "fb4e15be-e9ac-4072-adac-898c9697e4cc",  # Found exact match
    "Finance": "630591da-b07e-4bce-8b3f-90b8f46dcdeb"  # Found exact match
}

# Special user roles identified by extensionAttribute10
EXTENSION_ATTRIBUTE_ROLES = {
    "Director of Schools": "Director of Schools",  # Value in extensionAttribute10
    "Admin Principal": "Building Administrator"    # Value in extensionAttribute10
}

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
    List all groups in the Azure AD tenant with pagination.
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    graph_url = "https://graph.microsoft.com/v1.0/groups?$top=999"
    all_groups = []
    
    print("\nFetching groups from Azure AD...")
    print(f"Request URL: {graph_url}")
    print("Request Headers: Authorization: Bearer [REDACTED]")
    
    try:
        # Continue fetching groups until there are no more pages
        page_count = 0
        while graph_url and page_count < 3:  # Limit to 3 pages for testing
            response = requests.get(graph_url, headers=headers)
            page_count += 1
            
            if response.status_code == 200:
                groups_data = response.json()
                page_groups = groups_data.get('value', [])
                all_groups.extend(page_groups)
                print(f"  Retrieved {len(page_groups)} groups in page {page_count}")
                
                # Check if there are more pages
                graph_url = groups_data.get('@odata.nextLink')
            else:
                graph_url = None
                print(f"Failed to retrieve more groups: {response.status_code}")
                break
        
        print(f"✅ Successfully retrieved a total of {len(all_groups)} groups")
        return all_groups
    except Exception as e:
        print(f"❌ Exception while fetching groups: {str(e)}")
        return []

def check_target_groups(groups, target_groups):
    """
    Check if target groups with the specified IDs exist in the retrieved groups list.
    """
    print("\nChecking for target groups using IDs:")
    found_groups = []
    group_ids = {}
    
    # Create a dictionary of groups by ID for faster lookup
    groups_by_id = {group.get('id', ''): group for group in groups}
    
    for target_name, target_id in target_groups.items():
        if target_id in groups_by_id:
            group = groups_by_id[target_id]
            display_name = group.get('displayName')
            found_groups.append(target_name)
            group_ids[target_name] = target_id
            print(f"✅ Found group: {display_name} (ID: {target_id})")
        else:
            print(f"❌ Could not find group: {target_name} (ID: {target_id})")
    
    # If we didn't find all groups, let's try a direct fetch for each specific ID
    if len(found_groups) < len(target_groups):
        print("\nAttempting direct fetch for missing groups:")
        missing_groups = {name: id for name, id in target_groups.items() if name not in found_groups}
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        for name, group_id in missing_groups.items():
            try:
                graph_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}"
                print(f"  Direct fetch for {name}: {graph_url}")
                
                response = requests.get(graph_url, headers=headers)
                if response.status_code == 200:
                    group = response.json()
                    display_name = group.get('displayName')
                    found_groups.append(name)
                    group_ids[name] = group_id
                    print(f"✅ Found group via direct fetch: {display_name} (ID: {group_id})")
                else:
                    print(f"❌ Direct fetch failed for {name}: Status {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ Error fetching group {name}: {str(e)}")
    
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
    Also search for Director of Schools based on extensionAttribute10 value or specific email.
    """
    print("\nChecking access to user attributes (extensionAttribute10 and officeLocation)...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # First fetch one user to test general attribute access
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
            
            # Now look for the Director of Schools (twatkins@ocboe.com) and check their attributes
            print("\nLooking for Director of Schools (twatkins@ocboe.com)...")
            
            # Get all users with the relevant attributes
            all_users_url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,mail,userPrincipalName,jobTitle,officeLocation,department,onPremisesExtensionAttributes&$top=999"
            
            try:
                all_users_response = requests.get(all_users_url, headers=headers)
                
                if all_users_response.status_code == 200:
                    all_users_data = all_users_response.json()
                    all_users = all_users_data.get('value', [])
                    
                    print(f"  Retrieved {len(all_users)} users to search")
                      # Look for the Director of Schools by email
                    director_email = "twatkins@ocboe.com"
                    director_found = False
                    
                    for user in all_users:
                        mail = user.get('mail', '')
                        upn = user.get('userPrincipalName', '')
                        
                        # Safe comparison handling None values
                        if (mail and mail.lower() == director_email.lower()) or (upn and upn.lower() == director_email.lower()):
                            director_found = True
                            print("✅ Found Director of Schools:")
                            print(f"   Name: {user.get('displayName')}")
                            print(f"   Email: {mail}")
                            print(f"   Job Title: {user.get('jobTitle', 'Not set')}")
                            print(f"   Office Location: {user.get('officeLocation', 'Not set')}")
                            
                            # Check extensionAttribute10
                            ext_attrs = user.get('onPremisesExtensionAttributes', {})
                            ext_attr10 = ext_attrs.get('extensionAttribute10', '')
                            print(f"   extensionAttribute10: {ext_attr10 if ext_attr10 else 'Not set'}")
                            
                            if not ext_attr10 or "Director of Schools" not in ext_attr10:
                                print("\n⚠️ The extensionAttribute10 does not contain 'Director of Schools'")
                                print("   This attribute should be updated for the role to be detected properly")
                            break
                    
                    if not director_found:
                        print(f"❌ Could not find Director of Schools with email {director_email}")
                          # Look for users with Director of Schools in their title
                        print("\nSearching for possible Director of Schools based on job title or name...")
                        possible_directors = []
                        
                        for user in all_users:
                            job_title = user.get('jobTitle', '').lower() if user.get('jobTitle') else ''
                            display_name = user.get('displayName', '').lower() if user.get('displayName') else ''
                            user_email = user.get('mail', '').lower() if user.get('mail') else ''
                            
                            # Check if name or job title contains relevant keywords OR has extensionAttribute10 set
                            ext_attrs = user.get('onPremisesExtensionAttributes', {})
                            ext_attr10 = ext_attrs.get('extensionAttribute10', '') if ext_attrs else ''
                            
                            # Check for matches based on keywords OR the extensionAttribute10
                            if (('director' in job_title and 'school' in job_title) or 
                                ('superintendent' in job_title) or 
                                ('tim' in display_name.lower() and 'watkins' in display_name.lower()) or 
                                ('watkins' in user_email) or
                                (ext_attr10 and 'director of schools' in ext_attr10.lower())):
                                possible_directors.append(user)
                        
                        if possible_directors:
                            print("Found potential matches based on job title, name, or extensionAttribute10:")
                            for i, director in enumerate(possible_directors, 1):
                                mail = director.get('mail', 'No email available')
                                job_title = director.get('jobTitle', 'Not set')
                                ext_attrs = director.get('onPremisesExtensionAttributes', {})
                                ext_attr10 = ext_attrs.get('extensionAttribute10', 'Not set') if ext_attrs else 'Not set'
                                
                                print(f"   {i}. {director.get('displayName')} ({mail})")
                                print(f"      Job Title: {job_title}")
                                print(f"      extensionAttribute10: {ext_attr10}")
                                
                                # Flag if this is a strong match based on extensionAttribute10
                                if ext_attr10 and 'director of schools' in ext_attr10.lower():
                                    print(f"      ✅ STRONG MATCH: extensionAttribute10 indicates Director of Schools role")
                        
                        # Show some sample extensionAttribute10 values
                        print("\nSample extensionAttribute10 values from users:")
                        sample_count = 0
                        
                        for user in all_users:
                            ext_attrs = user.get('onPremisesExtensionAttributes', {})
                            ext_attr10 = ext_attrs.get('extensionAttribute10', '')
                            
                            if ext_attr10:
                                print(f"   - {user.get('displayName')} ({user.get('mail')}): '{ext_attr10}'")
                                sample_count += 1
                            
                            if sample_count >= 5:  # Show up to 5 examples
                                break
                        
                        if sample_count == 0:
                            print("   No users found with any value in extensionAttribute10")
                else:
                    print("❌ Failed to search for users")
                    print(f"   Status code: {all_users_response.status_code}")
                    print(f"   Response: {all_users_response.text}")
            except Exception as e:
                print(f"❌ Exception during Director of Schools search: {str(e)}")
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
    global access_token
    access_token = get_access_token()
    if not access_token:
        return
        
    # Check API permissions (diagnostic)
    check_api_permissions(access_token)
    
    # List all groups (first few pages)
    groups = list_all_groups(access_token)
    
    # Check target groups
    found_groups, group_ids = check_target_groups(groups, TARGET_GROUPS)
    
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
        print("   You may need to update the TARGET_GROUPS dictionary in this script")
        print("   with correct group IDs from the search_ad_groups.py results.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
