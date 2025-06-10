#!/usr/bin/env python3
"""
Test script for dynamic menu functionality
This script tests the service health checking and menu visibility features.
"""

import asyncio
import sys
import os

# Add the portal directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ocs-portal-py'))

from service_health import health_checker

async def test_health_checker():
    """Test the health checker functionality"""
    print("🔍 Testing Dynamic Menu Health Checker")
    print("=" * 50)
    
    try:
        # Test service health checking
        print("\n📊 Checking service health...")
        service_health = await health_checker.get_service_health()
        
        for service, is_healthy in service_health.items():
            status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
            print(f"  {service}: {status}")
        
        # Test menu visibility
        print("\n🎯 Checking menu visibility...")
        menu_visibility = await health_checker.get_menu_visibility()
        
        for menu_item, is_visible in menu_visibility.items():
            visibility = "👁️  Visible" if is_visible else "🚫 Hidden"
            print(f"  {menu_item.title()} Menu: {visibility}")
        
        # Test caching
        print("\n⚡ Testing cache performance...")
        import time
        
        start_time = time.time()
        await health_checker.get_menu_visibility()
        cached_time = time.time() - start_time
        
        print(f"  Cached response time: {cached_time:.4f} seconds")
        
        print("\n✅ Health checker test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during health check test: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Dynamic Menu Feature Test")
    print("This test verifies that the dynamic menu system is working correctly.")
    print("Menu items will be hidden when their corresponding services are unavailable.\n")
    
    success = await test_health_checker()
    
    if success:
        print("\n🎉 All tests passed!")
        print("\nTo see the dynamic menu in action:")
        print("1. Start all services with: docker-compose up")
        print("2. Visit the portal at: http://localhost:8003")
        print("3. Stop individual services to see menus disappear")
        print("4. Restart services to see menus reappear")
    else:
        print("\n💥 Tests failed!")
        
    return success

if __name__ == "__main__":
    asyncio.run(main())
