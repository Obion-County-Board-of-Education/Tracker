#!/usr/bin/env python3
"""
Test script for dynamic menu functionality
This script tests the menu visibility based on service health status
"""

import sys
import os
import asyncio
import httpx

# Add the portal directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))

from service_health import health_checker

async def test_service_health():
    """Test individual service health checks"""
    print("🔍 Testing individual service health...")
    
    services = ["tickets", "inventory", "requisition", "manage"]
    
    for service in services:
        try:
            is_healthy = await health_checker.check_service_health(service)
            status = "✅ HEALTHY" if is_healthy else "❌ UNHEALTHY"
            print(f"  {service.capitalize()} Service: {status}")
        except Exception as e:
            print(f"  {service.capitalize()} Service: ❌ ERROR - {e}")

async def test_menu_visibility():
    """Test the menu visibility function"""
    print("\n🎯 Testing menu visibility...")
    
    try:
        menu_visibility = await health_checker.get_menu_visibility()
        print("Menu Visibility Results:")
        for menu_item, visible in menu_visibility.items():
            status = "👁️  VISIBLE" if visible else "🚫 HIDDEN"
            print(f"  {menu_item.capitalize()} Menu: {status}")
        
        return menu_visibility
    except Exception as e:
        print(f"❌ Error getting menu visibility: {e}")
        return None

async def test_portal_endpoint():
    """Test the portal's service status endpoint"""
    print("\n🌐 Testing portal service status endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8003/api/services/status")
            if response.status_code == 200:
                data = response.json()
                print("Portal Service Status:")
                for service, status in data.items():
                    emoji = "✅" if status else "❌"
                    print(f"  {service}: {emoji}")
            else:
                print(f"❌ Portal endpoint returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing portal endpoint: {e}")

async def main():
    print("🧪 Dynamic Menu Functionality Test")
    print("=" * 50)
    
    # Test individual services
    await test_service_health()
    
    # Test menu visibility logic
    menu_visibility = await test_menu_visibility()
    
    # Test portal endpoint if it exists
    await test_portal_endpoint()
    
    print("\n📋 Test Summary:")
    print("- The 'Manage' menu should be HIDDEN since ocs-manage-api is not running")
    print("- The 'Tickets', 'Inventory', and 'Requisitions' menus should be VISIBLE")
    print("- The 'Admin' menu should always be VISIBLE")
    
    if menu_visibility:
        expected_results = {
            "tickets": True,
            "inventory": True,
            "requisitions": True,
            "manage": False,  # This should be False since manage service is not running
            "admin": True
        }
        
        print("\n🎯 Expected vs Actual Results:")
        all_correct = True
        for menu_item, expected in expected_results.items():
            actual = menu_visibility.get(menu_item, False)
            match = "✅" if actual == expected else "❌"
            print(f"  {menu_item.capitalize()}: Expected {expected}, Got {actual} {match}")
            if actual != expected:
                all_correct = False
        
        if all_correct:
            print("\n🎉 SUCCESS: Dynamic menu is working correctly!")
        else:
            print("\n⚠️  ISSUE: Some menu items are not showing expected behavior")

if __name__ == "__main__":
    asyncio.run(main())
