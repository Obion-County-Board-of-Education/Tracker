#!/usr/bin/env python3
"""
Test script to verify GroupRole automatic initialization.
This script tests the complete GroupRole initialization process.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add parent directory to path for shared models access
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

def run_docker_command(command, description):
    """Run a docker command and return the result"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    
    try:
        if sys.platform == "win32":
            # Use PowerShell on Windows
            result = subprocess.run(
                ["powershell", "-Command", command], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
        else:
            # Use bash on Unix-like systems
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
        
        if result.returncode == 0:
            print(f"✅ Success: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            print(f"❌ Error: {result.stderr.strip()}")
            return None
            
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
        return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def check_grouproles_in_db():
    """Check GroupRoles directly in the database"""
    command = 'docker-compose exec -T db psql -U ocs_user -d ocs_portal -c "SELECT group_name, access_level FROM group_roles ORDER BY group_name;"'
    return run_docker_command(command, "Checking GroupRoles in database")

def delete_grouproles():
    """Delete all GroupRoles from database"""
    command = 'docker-compose exec -T db psql -U ocs_user -d ocs_portal -c "DELETE FROM group_roles;"'
    return run_docker_command(command, "Deleting GroupRoles for testing")

def restart_portal_service():
    """Restart the portal service to trigger initialization"""
    command = "docker-compose restart ocs-portal-py"
    return run_docker_command(command, "Restarting portal service")

def check_portal_logs():
    """Check portal logs for initialization messages"""
    command = "docker-compose logs ocs-portal-py --tail=50"
    return run_docker_command(command, "Checking portal logs")

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 TESTING GROUPROLE AUTOMATIC INITIALIZATION")
    print("=" * 60)
    
    # Step 1: Check initial state
    print("\n1️⃣ CHECKING INITIAL STATE")
    initial_state = check_grouproles_in_db()
    
    # Step 2: Delete GroupRoles
    print("\n2️⃣ CLEARING GROUPROLES FOR TESTING")
    delete_result = delete_grouproles()
    
    # Step 3: Verify deletion
    print("\n3️⃣ VERIFYING DELETION")
    after_delete = check_grouproles_in_db()
    
    # Step 4: Restart portal service
    print("\n4️⃣ RESTARTING PORTAL SERVICE")
    restart_result = restart_portal_service()
    
    # Step 5: Wait a moment for initialization
    print("\n⏳ Waiting for initialization to complete...")
    import time
    time.sleep(5)
    
    # Step 6: Check logs for initialization messages
    print("\n5️⃣ CHECKING LOGS FOR INITIALIZATION MESSAGES")
    logs = check_portal_logs()
    
    # Step 7: Verify GroupRoles were recreated
    print("\n6️⃣ VERIFYING GROUPROLES WERE RECREATED")
    final_state = check_grouproles_in_db()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if final_state and "All_Staff" in final_state:
        print("✅ SUCCESS: GroupRoles were automatically recreated!")
        print("✅ The initialization system is working correctly.")
        
        # Check for specific log messages
        if logs:
            if "Group roles already exist" in logs:
                print("✅ Found 'Group roles already exist' message in logs")
            elif "Setting up essential group role mappings" in logs:
                print("✅ Found GroupRole creation messages in logs")
            else:
                print("⚠️  GroupRoles exist but creation messages not found in recent logs")
        
        print("\n🎯 EXPECTED GROUPROLES FOUND:")
        if final_state:
            for line in final_state.split('\n'):
                if '|' in line and 'group_name' not in line and '---' not in line:
                    print(f"   • {line.strip()}")
    else:
        print("❌ FAILURE: GroupRoles were not recreated automatically")
        print("❌ The initialization system may have issues")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
