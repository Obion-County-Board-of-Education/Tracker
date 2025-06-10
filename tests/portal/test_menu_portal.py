#!/usr/bin/env python3
"""
Simple test for dynamic menu functionality
"""

import asyncio
from service_health import health_checker

async def main():
    print("🧪 Testing Dynamic Menu Functionality")
    print("=" * 50)
    
    # Test individual service health
    services = ["tickets", "inventory", "requisition", "manage"]
    
    print("🔍 Individual Service Health:")
    for service in services:
        try:
            is_healthy = await health_checker.check_service_health(service)
            status = "✅ HEALTHY" if is_healthy else "❌ UNHEALTHY"
            print(f"  {service}: {status}")
        except Exception as e:
            print(f"  {service}: ❌ ERROR - {e}")
    
    print("\n🎯 Menu Visibility:")
    try:
        menu_visibility = await health_checker.get_menu_visibility()
        for menu_item, visible in menu_visibility.items():
            status = "👁️  VISIBLE" if visible else "🚫 HIDDEN"
            print(f"  {menu_item}: {status}")
        
        # Check if manage menu is correctly hidden
        if not menu_visibility.get("manage", True):
            print("\n🎉 SUCCESS: Manage menu is correctly HIDDEN!")
        else:
            print("\n⚠️  ISSUE: Manage menu should be HIDDEN but shows as VISIBLE")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
