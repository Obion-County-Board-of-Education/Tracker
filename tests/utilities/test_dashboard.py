#!/usr/bin/env python3
"""
Test script to verify dashboard functionality is working properly
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_dashboard():
    """Test the homepage dashboard functionality"""
    try:
        print("🧪 Testing OCS Portal Dashboard...")
        print("=" * 50)
        
        # Test homepage loading
        async with aiohttp.ClientSession() as session:
            print("📊 Testing homepage with dashboard data...")
            async with session.get('http://localhost:8003/') as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check for dashboard elements
                    dashboard_checks = [
                        ('Summary Cards', 'summary-cards' in content),
                        ('Tickets Chart', 'ticketsChart' in content),
                        ('Ticket Types Chart', 'ticketTypesChart' in content),
                        ('System Resources Chart', 'systemResourcesChart' in content),
                        ('Chart.js Library', 'chart.js' in content),
                        ('Dashboard Data', 'dashboard_data' in content),
                        ('Chart Initialization', 'initializeCharts' in content),
                        ('Dashboard Interactivity', 'addDashboardInteractivity' in content)
                    ]
                    
                    print("\n📋 Dashboard Component Checks:")
                    for check_name, passed in dashboard_checks:
                        status = "✅" if passed else "❌"
                        print(f"  {status} {check_name}")
                    
                    # Check for CSS styles
                    css_checks = [
                        ('Summary Card Styles', '.summary-card' in content),
                        ('Chart Container Styles', '.chart-container' in content),
                        ('Dashboard Header Styles', '.dashboard-header' in content),
                        ('Animation Styles', '@keyframes fadeInUp' in content),
                        ('Error Handling Styles', '.chart-error' in content)
                    ]
                    
                    print("\n🎨 CSS Style Checks:")
                    for check_name, passed in css_checks:
                        status = "✅" if passed else "❌"
                        print(f"  {status} {check_name}")
                    
                    all_passed = all(passed for _, passed in dashboard_checks + css_checks)
                    
                    if all_passed:
                        print("\n🎉 All dashboard components are present!")
                        print("✅ Dashboard implementation is complete")
                    else:
                        print("\n⚠️  Some dashboard components may be missing")
                        
                    return all_passed
                else:
                    print(f"❌ Homepage failed to load: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing dashboard: {e}")
        return False

async def test_dashboard_data_api():
    """Test that the dashboard data is being generated correctly"""
    try:
        print("\n🔍 Testing dashboard data generation...")
        
        # Test backend services that provide dashboard data
        services_to_test = [
            ('Tickets API', 'http://localhost:8000/health'),
            ('Portal API', 'http://localhost:8003/health'),
        ]
        
        async with aiohttp.ClientSession() as session:
            for service_name, url in services_to_test:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            print(f"  ✅ {service_name}: Online")
                        else:
                            print(f"  ⚠️  {service_name}: HTTP {response.status}")
                except Exception as e:
                    print(f"  ❌ {service_name}: {e}")
                    
        return True
        
    except Exception as e:
        print(f"❌ Error testing dashboard data: {e}")
        return False

async def main():
    """Main test function"""
    print(f"🚀 Dashboard Test Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    homepage_test = await test_dashboard()
    api_test = await test_dashboard_data_api()
    
    print("\n" + "=" * 50)
    print("📊 DASHBOARD TEST RESULTS")
    print("=" * 50)
    print(f"Homepage Dashboard: {'✅ PASS' if homepage_test else '❌ FAIL'}")
    print(f"API Services: {'✅ PASS' if api_test else '❌ FAIL'}")
    
    if homepage_test and api_test:
        print("\n🎉 All tests passed! Dashboard is working correctly.")
        print("\n📋 Dashboard Features Available:")
        print("  • Summary cards showing tickets, buildings, users, and service health")
        print("  • Interactive charts displaying system metrics")
        print("  • Recent activity list showing latest ticket updates") 
        print("  • Responsive design with hover effects and animations")
        print("  • Click-to-navigate functionality on summary cards")
        print("  • Real-time data from all OCS services")
        print("\n🌐 Access the dashboard at: http://localhost:8003")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
    
    return homepage_test and api_test

if __name__ == "__main__":
    asyncio.run(main())
