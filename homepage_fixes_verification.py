#!/usr/bin/env python3
"""
Verification script for homepage fixes:
1. Recent Activity section removed
2. Edit Message button has white text
"""

import requests
from datetime import datetime

def test_homepage_fixes():
    """Test the homepage fixes"""
    print("🔧 Homepage Fixes Verification")
    print("=" * 40)
    
    try:
        # Test homepage loading
        response = requests.get('http://localhost:8003/', timeout=10)
        print(f"📱 Homepage Status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Homepage failed to load")
            return False
            
        content = response.text
        
        # Test 1: Recent Activity section removed
        print("\n🧹 Testing Recent Activity Removal:")
        recent_activity_checks = [
            ('Recent Activity Title', 'Recent Activity' not in content),
            ('Activity Container Class', 'activity-container' not in content),
            ('Activity List', 'activity-list' not in content),
            ('Activity Item', 'activity-item' not in content),
            ('No Activity Message', 'No recent activity' not in content)
        ]
        
        recent_activity_removed = True
        for check_name, passed in recent_activity_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                recent_activity_removed = False
        
        # Test 2: Edit Message button styling
        print("\n🎨 Testing Edit Message Button Styling:")
        button_styling_checks = [
            ('Edit Message Button Present', 'editMessageBtn' in content),
            ('Button has btn-outline class', 'btn btn-outline btn-sm' in content),
            ('White text styling', 'color: white' in content and '.btn-outline' in content)
        ]
        
        button_styling_correct = True
        for check_name, passed in button_styling_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                button_styling_correct = False
        
        # Test 3: Dashboard still present
        print("\n📊 Testing Dashboard Still Present:")
        dashboard_checks = [
            ('Dashboard Section', 'dashboard-section' in content),
            ('Summary Cards', 'summary-cards' in content),
            ('Charts Section', 'charts-section' in content),
            ('Chart.js Library', 'chart.js' in content.lower())
        ]
        
        dashboard_present = True
        for check_name, passed in dashboard_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                dashboard_present = False
        
        # Test 4: Specific CSS checks
        print("\n🎨 Testing CSS Changes:")
        css_checks = [
            ('Activity CSS Removed', '.activity-container' not in content),
            ('Activity Item CSS Removed', '.activity-item' not in content),
            ('No Activity CSS Removed', '.no-activity' not in content),
            ('Button White Text CSS', 'color: white' in content)
        ]
        
        css_correct = True
        for check_name, passed in css_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                css_correct = False
        
        # Final assessment
        print("\n" + "=" * 40)
        print("🏁 VERIFICATION RESULTS")
        print("=" * 40)
        
        recent_status = "✅ REMOVED" if recent_activity_removed else "❌ STILL PRESENT"
        button_status = "✅ FIXED" if button_styling_correct else "❌ NEEDS FIX"
        dashboard_status = "✅ WORKING" if dashboard_present else "❌ BROKEN"
        css_status = "✅ CLEAN" if css_correct else "❌ NEEDS CLEANUP"
        
        print(f"Recent Activity Removal: {recent_status}")
        print(f"Edit Message Button Text: {button_status}")
        print(f"Dashboard Functionality: {dashboard_status}")
        print(f"CSS Cleanup: {css_status}")
        
        overall_success = (recent_activity_removed and 
                          button_styling_correct and 
                          dashboard_present and 
                          css_correct)
        
        if overall_success:
            print("\n🎉 SUCCESS! All fixes applied correctly!")
            print("\n📋 Changes Completed:")
            print("  ✅ Recent Activity section completely removed")
            print("  ✅ Edit Message button now has white text")
            print("  ✅ Dashboard functionality preserved")
            print("  ✅ Unused CSS cleaned up")
            print("\n🌐 Updated homepage available at: http://localhost:8003")
        else:
            print("\n⚠️  Some fixes may need attention.")
            print("Please check the failed items above.")
        
        return overall_success
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print(f"🚀 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_homepage_fixes()
    
    print(f"\n⏰ Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏆 Result: {'SUCCESS' if success else 'NEEDS ATTENTION'}")
