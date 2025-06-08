#!/usr/bin/env python3
"""
Simple script to check if import buttons are in the HTML
"""

import urllib.request
import urllib.error

def check_html_content():
    """Check the actual HTML content served by the portal"""
    print("🔍 Checking HTML Content for Import Buttons...")
    
    try:
        # Check tech tickets page
        print("\n📄 Tech Tickets Page:")
        with urllib.request.urlopen("http://localhost:8003/tickets/tech/open") as response:
            html_content = response.read().decode('utf-8')
            
        if "Import CSV" in html_content:
            print("✅ 'Import CSV' text found in HTML")
        else:
            print("❌ 'Import CSV' text NOT found in HTML")
            
        if "import-csv-btn" in html_content:
            print("✅ 'import-csv-btn' class found in HTML")
        else:
            print("❌ 'import-csv-btn' class NOT found in HTML")
            
        if "action-buttons" in html_content:
            print("✅ 'action-buttons' div found in HTML")
        else:
            print("❌ 'action-buttons' div NOT found in HTML")
            
        # Count buttons in action-buttons section
        action_start = html_content.find('<div class="action-buttons">')
        if action_start != -1:
            action_end = html_content.find('</div>', action_start)
            action_section = html_content[action_start:action_end]
            button_count = action_section.count('<button')
            link_count = action_section.count('<a href')
            print(f"📊 Found {button_count} buttons and {link_count} links in action-buttons section")
            
            # Show the action-buttons section
            print(f"🔍 Action buttons section:")
            print(action_section[:500] + ("..." if len(action_section) > 500 else ""))
        
    except Exception as e:
        print(f"❌ Error checking tech tickets page: {e}")
    
    try:
        # Check maintenance tickets page
        print("\n📄 Maintenance Tickets Page:")
        with urllib.request.urlopen("http://localhost:8003/tickets/maintenance/open") as response:
            html_content = response.read().decode('utf-8')
            
        if "Import CSV" in html_content:
            print("✅ 'Import CSV' text found in HTML")
        else:
            print("❌ 'Import CSV' text NOT found in HTML")
            
        if "import-csv-btn" in html_content:
            print("✅ 'import-csv-btn' class found in HTML")
        else:
            print("❌ 'import-csv-btn' class NOT found in HTML")
            
    except Exception as e:
        print(f"❌ Error checking maintenance tickets page: {e}")

if __name__ == "__main__":
    check_html_content()
