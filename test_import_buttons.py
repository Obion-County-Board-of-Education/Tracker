#!/usr/bin/env python3
"""
Test to check if import buttons are present in the served HTML
"""

import requests
from bs4 import BeautifulSoup

def check_import_buttons():
    """Check if import buttons are present in the served HTML"""
    print("🔍 Checking Import Buttons in Served HTML...")
    
    try:
        # Test tech tickets page
        response = requests.get("http://localhost:8003/tickets/tech/open")
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            import_btn = soup.find('button', class_='import-csv-btn')
            if import_btn:
                print("✅ Tech tickets import button found in served HTML")
                print(f"   Button text: {import_btn.get_text().strip()}")
                print(f"   Button classes: {import_btn.get('class')}")
                print(f"   Button onclick: {import_btn.get('onclick')}")
            else:
                print("❌ Tech tickets import button NOT found in served HTML")
                # Check if action-buttons div exists
                action_buttons = soup.find('div', class_='action-buttons')
                if action_buttons:
                    print("   action-buttons div found, checking content:")
                    print(f"   {action_buttons}")
                else:
                    print("   action-buttons div NOT found")
        else:
            print(f"❌ Failed to load tech tickets page: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking tech tickets page: {e}")
    
    try:
        # Test maintenance tickets page
        response = requests.get("http://localhost:8003/tickets/maintenance/open")
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            import_btn = soup.find('button', class_='import-csv-btn')
            if import_btn:
                print("✅ Maintenance tickets import button found in served HTML")
                print(f"   Button text: {import_btn.get_text().strip()}")
                print(f"   Button classes: {import_btn.get('class')}")
                print(f"   Button onclick: {import_btn.get('onclick')}")
            else:
                print("❌ Maintenance tickets import button NOT found in served HTML")
                # Check if action-buttons div exists
                action_buttons = soup.find('div', class_='action-buttons')
                if action_buttons:
                    print("   action-buttons div found, checking content:")
                    print(f"   {action_buttons}")
                else:
                    print("   action-buttons div NOT found")
        else:
            print(f"❌ Failed to load maintenance tickets page: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking maintenance tickets page: {e}")

if __name__ == "__main__":
    print("🧪 Testing Import Button Visibility")
    print("=" * 50)
    check_import_buttons()
    print("\n" + "=" * 50)
    print("💡 If buttons are not found:")
    print("1. Check browser cache (hard refresh with Ctrl+F5)")
    print("2. Check browser developer tools for JavaScript errors")
    print("3. Verify CSS is not hiding the buttons")
    print("4. Check if templates are being served correctly")
