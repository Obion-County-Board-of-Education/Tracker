#!/usr/bin/env python3
"""
Architecture Compliance Verification Script
Verifies that the OCS microservices follow proper architecture patterns
"""

import os
import sys
import re
from pathlib import Path

def check_direct_database_violations():
    """Check for direct database access violations in portal code"""
    violations = []
    portal_path = Path("ocs-portal-py")
    
    # Patterns that indicate direct database access to tickets
    violation_patterns = [
        r'db\.query\(.*Ticket',
        r'session\.query\(.*Ticket',
        r'from.*Ticket.*import',
        r'import.*Ticket',
        r'\.filter\(.*Ticket\.',
        r'Ticket\s*\(',
    ]
    
    if not portal_path.exists():
        return ["Portal directory not found"]
    
    python_files = list(portal_path.glob("*.py"))
    
    for file_path in python_files:
        if file_path.name in ['services.py', 'management_service.py']:
            continue  # Skip service layer files
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern in violation_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(f"{file_path}:{line_num} - {line.strip()}")
        except Exception as e:
            violations.append(f"Error reading {file_path}: {e}")
    
    return violations

def check_service_layer_usage():
    """Check that portal uses service layer for API communication"""
    correct_patterns = []
    portal_main = Path("ocs-portal-py/main.py")
    
    if not portal_main.exists():
        return ["Portal main.py not found"], []
    
    try:
        with open(portal_main, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for service layer usage
        service_patterns = [
            r'tickets_service\.',
            r'management_service\.',
            r'await.*service\.',
        ]
        
        for line_num, line in enumerate(content.split('\n'), 1):
            for pattern in service_patterns:
                if re.search(pattern, line):
                    correct_patterns.append(f"Line {line_num}: {line.strip()}")
                    
    except Exception as e:
        return [f"Error reading main.py: {e}"], []
    
    return [], correct_patterns

def check_docker_database_separation():
    """Check Docker Compose for proper database separation"""
    docker_compose = Path("docker-compose.yml")
    
    if not docker_compose.exists():
        return ["docker-compose.yml not found"]
    
    try:
        with open(docker_compose, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for separate database configurations
        databases = [
            'ocs_portal',
            'ocs_tickets', 
            'ocs_inventory',
            'ocs_requisition',
            'ocs_manage'
        ]
        
        missing_dbs = []
        for db in databases:
            if db not in content:
                missing_dbs.append(db)
        
        return missing_dbs
        
    except Exception as e:
        return [f"Error reading docker-compose.yml: {e}"]

def main():
    """Run architecture compliance verification"""
    print("🔍 OCS Microservices Architecture Compliance Check")
    print("=" * 60)
    
    # Check for direct database violations
    print("\n1. Checking for direct database access violations...")
    violations = check_direct_database_violations()
    
    if violations:
        print("❌ VIOLATIONS FOUND:")
        for violation in violations[:10]:  # Limit output
            print(f"   {violation}")
        if len(violations) > 10:
            print(f"   ... and {len(violations) - 10} more")
    else:
        print("✅ No direct database access violations found")
    
    # Check service layer usage
    print("\n2. Checking service layer usage...")
    errors, correct_usage = check_service_layer_usage()
    
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"   {error}")
    else:
        print("✅ Service layer properly implemented")
        if correct_usage:
            print("   Examples of correct usage:")
            for example in correct_usage[:5]:  # Show first 5 examples
                print(f"   {example}")
    
    # Check Docker database separation
    print("\n3. Checking Docker database separation...")
    missing_dbs = check_docker_database_separation()
    
    if missing_dbs:
        print("❌ MISSING DATABASE CONFIGURATIONS:")
        for db in missing_dbs:
            print(f"   {db}")
    else:
        print("✅ All databases properly configured in Docker Compose")
    
    # Overall assessment
    print("\n" + "=" * 60)
    total_issues = len(violations) + len(errors) + len(missing_dbs)
    
    if total_issues == 0:
        print("🎉 ARCHITECTURE COMPLIANCE: PASSED")
        print("   All microservices follow proper architecture patterns")
    else:
        print(f"⚠️  ARCHITECTURE COMPLIANCE: {total_issues} ISSUES FOUND")
        print("   Review the issues above and ensure proper microservices patterns")
    
    return total_issues == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
