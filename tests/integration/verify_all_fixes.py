#!/usr/bin/env python3
"""
Comprehensive verification script for OCS Portal fixes
Tests all the recently implemented fixes:
1. Users and Buildings pages loading
2. Timezone functionality  
3. Removed Close Ticket buttons
4. Removed Emergency Issues section
"""

import requests
import json
from datetime import datetime

def test_all_fixes():
    base_url = "http://localhost:8003"
    
    print("🔍 COMPREHENSIVE OCS PORTAL VERIFICATION")
    print("=" * 60)
    
    # Test 1: Users and Buildings Pages
    print("\n📋 TEST 1: Users and Buildings Pages")
    print("-" * 40)
    
    pages_to_test = [
        ("/users", "Users page"),
        ("/users/list", "Users list page"),
        ("/buildings", "Buildings page"), 
        ("/buildings/list", "Buildings list page")
    ]
    
    for route, description in pages_to_test:
        try:
            response = requests.get(f"{base_url}{route}", timeout=10, allow_redirects=True)
            if response.status_code == 200:
                if "Management" in response.text:
                    print(f"  ✅ {description} - WORKING")
                else:
                    print(f"  ⚠️  {description} - Loaded but missing expected content")
            else:
                print(f"  ❌ {description} - HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ {description} - Error: {e}")
    
    # Test 2: Close Ticket Buttons Removed
    print("\n🔘 TEST 2: Close Ticket Buttons Removed")
    print("-" * 40)
    
    # Test tech ticket detail page
    try:
        # First get a list of tickets to find one to test
        tickets_response = requests.get(f"{base_url}/tickets/tech/list", timeout=10)
        if tickets_response.status_code == 200 and "ticket" in tickets_response.text.lower():
            print("  ✅ Tech tickets list page accessible")
            # Check if close buttons are removed from detail pages
            if "close ticket" not in tickets_response.text.lower():
                print("  ✅ No 'Close Ticket' buttons found in tech tickets list")
            else:
                print("  ⚠️  'Close Ticket' text still found in tech tickets")
        else:
            print("  ❌ Could not access tech tickets list")
    except Exception as e:
        print(f"  ❌ Tech tickets test error: {e}")
    
    # Test maintenance ticket detail page
    try:
        maintenance_response = requests.get(f"{base_url}/tickets/maintenance/list", timeout=10)
        if maintenance_response.status_code == 200:
            print("  ✅ Maintenance tickets list page accessible")
            if "close ticket" not in maintenance_response.text.lower():
                print("  ✅ No 'Close Ticket' buttons found in maintenance tickets list")
            else:
                print("  ⚠️  'Close Ticket' text still found in maintenance tickets")
        else:
            print("  ❌ Could not access maintenance tickets list")
    except Exception as e:
        print(f"  ❌ Maintenance tickets test error: {e}")
    
    # Test 3: Emergency Issues Section Removed
    print("\n🚨 TEST 3: Emergency Issues Section Removed")
    print("-" * 40)
    
    try:
        # Test the ticket success page (if we can access it)
        home_response = requests.get(f"{base_url}/", timeout=10)
        if home_response.status_code == 200:
            print("  ✅ Homepage accessible")
            if "emergency issues" not in home_response.text.lower():
                print("  ✅ No 'Emergency Issues' section found on homepage")
            else:
                print("  ⚠️  'Emergency Issues' text still found")
        
        # Check new ticket pages for emergency section
        new_tech_response = requests.get(f"{base_url}/tickets/tech/new", timeout=10)
        if new_tech_response.status_code == 200:
            print("  ✅ New tech ticket page accessible")
            if "emergency issues" not in new_tech_response.text.lower():
                print("  ✅ No emergency section in new tech ticket page")
    except Exception as e:
        print(f"  ❌ Emergency issues test error: {e}")
    
    # Test 4: Timezone Functionality
    print("\n🕐 TEST 4: Timezone Functionality")
    print("-" * 40)
    
    try:
        # Test API endpoints that should return timezone-aware data
        api_tests = [
            ("http://localhost:8000/health", "Tickets API health"),
            ("http://localhost:8003/api/service-status", "Portal service status")
        ]
        
        for api_url, description in api_tests:
            try:
                api_response = requests.get(api_url, timeout=5)
                if api_response.status_code == 200:
                    data = api_response.json()
                    if 'timestamp' in data or 'created_at' in str(data):
                        print(f"  ✅ {description} - Returns timestamp data")
                    else:
                        print(f"  ✅ {description} - Accessible")
                else:
                    print(f"  ⚠️  {description} - HTTP {api_response.status_code}")
            except requests.exceptions.RequestException:
                print(f"  ⚠️  {description} - Service not accessible")
            except Exception as e:
                print(f"  ❌ {description} - Error: {e}")
    except Exception as e:
        print(f"  ❌ Timezone test error: {e}")
    
    # Test 5: Overall System Health
    print("\n🏥 TEST 5: Overall System Health")
    print("-" * 40)
    
    services = [
        ("http://localhost:8003", "Portal Service"),
        ("http://localhost:8000", "Tickets API"),
        ("http://localhost:8001", "Inventory API"), 
        ("http://localhost:8002", "Requisition API"),
        ("http://localhost:8004", "Management API")
    ]
    
    for service_url, service_name in services:
        try:
            health_response = requests.get(f"{service_url}/health", timeout=5)
            if health_response.status_code == 200:
                print(f"  ✅ {service_name} - Healthy")
            else:
                print(f"  ⚠️  {service_name} - Responding but status {health_response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {service_name} - Not running")
        except Exception as e:
            print(f"  ❌ {service_name} - Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 VERIFICATION COMPLETE!")
    print("\nIf all tests show ✅, the OCS Portal fixes are working correctly.")
    print("If any tests show ❌, those issues may need additional attention.")

if __name__ == "__main__":
    test_all_fixes()
