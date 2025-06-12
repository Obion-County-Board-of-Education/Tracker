#!/usr/bin/env python
"""
Azure AD Group Search Script

This script searches for specific keywords in Azure AD groups to help identify
the correct groups for use in the OCS Tracker application.

Usage:
    python search_ad_groups.py
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

# Keywords to search for in group names
SEARCH_KEYWORDS = [
    "staff", "teacher", "faculty", 
    "student", "pupil", 
    "technology", "tech", "it", 
    "director", "principal", 
    "finance", "accounting", "budget",
    "admin", "administrator"
]

def get_access_token():
    """Get an access token for Microsoft Graph API using client credentials flow."""
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    print(f"Requesting access token for tenant: {tenant_id}...")
    
    try:
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code == 200:
            token_json = token_response.json()
            access_token = token_json.get('access_token')
            print("✅ Successfully obtained access token")
            return access_token
        else:
            print("❌ Failed to obtain access token")
            print(f"   Status code: {token_response.status_code}")
            print(f"   Error details: {token_response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception during token request: {str(e)}")
        return None

def search_groups_by_keyword(access_token):
    """Search for groups containing specific keywords."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Get all groups with pagination
    graph_url = "https://graph.microsoft.com/v1.0/groups?$top=999"
    all_groups = []
    
    print("\nFetching all groups from Azure AD...")
    
    try:
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
                print(f"Failed to retrieve more groups: {response.status_code}")
                break
        
        print(f"✅ Successfully retrieved a total of {len(all_groups)} groups")
        
        # Search for groups matching our keywords
        matching_groups = {}
        
        for keyword in SEARCH_KEYWORDS:
            matching_groups[keyword] = []
            
            for group in all_groups:
                name = group.get('displayName', '').lower()
                if keyword in name:
                    matching_groups[keyword].append(group)
        
        # Print results
        print("\nSearch Results:")
        print("=" * 50)
        
        for keyword, groups in matching_groups.items():
            if groups:
                print(f"\nGroups containing '{keyword}' ({len(groups)}):")
                for i, group in enumerate(groups[:10], 1):
                    print(f"   {i}. {group.get('displayName')} (ID: {group.get('id')})")
                
                if len(groups) > 10:
                    print(f"   ... and {len(groups) - 10} more")
            else:
                print(f"\nNo groups containing '{keyword}' found.")
        
        return all_groups, matching_groups
    
    except Exception as e:
        print(f"❌ Exception while searching groups: {str(e)}")
        return [], {}

def main():
    """Main function to search for relevant groups."""
    print("=" * 80)
    print("AZURE AD GROUP SEARCH TOOL")
    print("=" * 80)
    
    # Validate environment variables
    if not all([client_id, client_secret, tenant_id]):
        print("❌ Missing required environment variables. Please check your .env file.")
        return
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        return
    
    # Search for groups by keyword
    all_groups, matching_groups = search_groups_by_keyword(access_token)
    
    # Summary
    print("\n" + "=" * 80)
    print("SEARCH SUMMARY")
    print("=" * 80)
    
    total_matches = sum(len(groups) for groups in matching_groups.values())
    print(f"Total groups in Azure AD: {len(all_groups)}")
    print(f"Total matching groups found: {total_matches}")
    
    print("\nSuggested groups for OCS Tracker:")
    
    # Find best matches for the required roles
    required_roles = {
        "all_staff": ["staff", "teacher", "faculty"],
        "all_students": ["student", "pupil"],
        "technology": ["technology", "tech", "it"],
        "director": ["director", "principal"],
        "finance": ["finance", "accounting", "budget"]
    }
    
    print("\nRecommended groups for OCS Tracker roles:")
    print("-" * 60)
    
    for role, keywords in required_roles.items():
        potential_groups = []
        
        for keyword in keywords:
            potential_groups.extend(matching_groups.get(keyword, []))
        
        if potential_groups:
            print(f"\n{role.upper()} role:")
            # Remove duplicates
            seen_ids = set()
            unique_groups = []
            for group in potential_groups:
                group_id = group.get('id')
                if group_id not in seen_ids:
                    seen_ids.add(group_id)
                    unique_groups.append(group)
            
            # Sort by name length (shorter names are often more general groups)
            unique_groups.sort(key=lambda g: len(g.get('displayName', '')))
            
            for i, group in enumerate(unique_groups[:5], 1):
                print(f"   {i}. {group.get('displayName')} (ID: {group.get('id')})")
        else:
            print(f"\n{role.upper()} role: No suitable groups found")
    
    print("\n" + "=" * 80)
    print("NOTE: Update TARGET_GROUPS in test_graph_connection.py with the appropriate IDs")
    print("=" * 80)

if __name__ == "__main__":
    main()
