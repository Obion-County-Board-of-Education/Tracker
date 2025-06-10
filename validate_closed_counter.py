#!/usr/bin/env python3
"""
Simple validation script for the closed ticket counter implementation
"""
import os
import re

def validate_implementation():
    """Validate that the closed ticket counter implementation is complete"""
    
    print("🔍 Validating Closed Ticket Counter Implementation...\n")
    
    # Paths to check
    portal_dir = "ocs-portal-py"
    main_py_path = os.path.join(portal_dir, "main.py")
    services_py_path = os.path.join(portal_dir, "services.py")
    tech_template_path = os.path.join(portal_dir, "templates", "tech_tickets_list.html")
    maintenance_template_path = os.path.join(portal_dir, "templates", "maintenance_tickets_list.html")
    
    results = []
    
    # 1. Check if get_closed_tickets_count method exists in services.py
    print("1. Checking services.py for get_closed_tickets_count method...")
    if os.path.exists(services_py_path):
        with open(services_py_path, 'r', encoding='utf-8') as f:
            services_content = f.read()
            if 'get_closed_tickets_count' in services_content:
                print("   ✅ get_closed_tickets_count method found in services.py")
                results.append(True)
            else:
                print("   ❌ get_closed_tickets_count method NOT found in services.py")
                results.append(False)
    else:
        print("   ❌ services.py file not found")
        results.append(False)
    
    # 2. Check if main.py calls get_closed_tickets_count in routes
    print("\n2. Checking main.py for closed_count usage...")
    if os.path.exists(main_py_path):
        with open(main_py_path, 'r', encoding='utf-8') as f:
            main_content = f.read()
            tech_route_has_closed_count = 'closed_count = await tickets_service.get_closed_tickets_count("tech")' in main_content
            maintenance_route_has_closed_count = 'closed_count = await tickets_service.get_closed_tickets_count("maintenance")' in main_content
            tech_template_has_closed_count = '"closed_count": closed_count' in main_content
            
            if tech_route_has_closed_count:
                print("   ✅ Tech route calls get_closed_tickets_count")
                results.append(True)
            else:
                print("   ❌ Tech route does NOT call get_closed_tickets_count")
                results.append(False)
                
            if maintenance_route_has_closed_count:
                print("   ✅ Maintenance route calls get_closed_tickets_count")
                results.append(True)
            else:
                print("   ❌ Maintenance route does NOT call get_closed_tickets_count")
                results.append(False)
                
            if tech_template_has_closed_count:
                print("   ✅ Templates receive closed_count parameter")
                results.append(True)
            else:
                print("   ❌ Templates do NOT receive closed_count parameter")
                results.append(False)
    else:
        print("   ❌ main.py file not found")
        results.extend([False, False, False])
    
    # 3. Check tech template for counter HTML
    print("\n3. Checking tech_tickets_list.html for counter HTML...")
    if os.path.exists(tech_template_path):
        with open(tech_template_path, 'r', encoding='utf-8') as f:
            tech_template_content = f.read()
            has_counter_section = 'closed-tickets-counter' in tech_template_content
            has_counter_check = "status_filter == 'open' and closed_count is defined" in tech_template_content
            
            if has_counter_section and has_counter_check:
                print("   ✅ Tech template has counter HTML with proper conditional")
                results.append(True)
            else:
                print("   ❌ Tech template missing counter HTML or conditional")
                results.append(False)
    else:
        print("   ❌ tech_tickets_list.html file not found")
        results.append(False)
    
    # 4. Check maintenance template for counter HTML
    print("\n4. Checking maintenance_tickets_list.html for counter HTML...")
    if os.path.exists(maintenance_template_path):
        with open(maintenance_template_path, 'r', encoding='utf-8') as f:
            maintenance_template_content = f.read()
            has_counter_section = 'closed-tickets-counter' in maintenance_template_content
            has_counter_check = "status_filter == 'open' and closed_count is defined" in maintenance_template_content
            
            if has_counter_section and has_counter_check:
                print("   ✅ Maintenance template has counter HTML with proper conditional")
                results.append(True)
            else:
                print("   ❌ Maintenance template missing counter HTML or conditional")
                results.append(False)
    else:
        print("   ❌ maintenance_tickets_list.html file not found")
        results.append(False)
    
    # 5. Check for CSS styles
    print("\n5. Checking templates for counter CSS styles...")
    counter_css_found = False
    for template_path in [tech_template_path, maintenance_template_path]:
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                if 'closed-tickets-counter' in template_content and '.counter-card' in template_content:
                    counter_css_found = True
                    break
    
    if counter_css_found:
        print("   ✅ Counter CSS styles found in templates")
        results.append(True)
    else:
        print("   ❌ Counter CSS styles NOT found in templates")
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Passed: {passed}/{total} checks")
    
    if passed == total:
        print("   🎉 ALL CHECKS PASSED! Closed ticket counter implementation is complete.")
        return True
    else:
        print(f"   ⚠️  {total - passed} checks failed. Implementation needs attention.")
        return False

if __name__ == "__main__":
    validate_implementation()
