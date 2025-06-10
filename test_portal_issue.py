#!/usr/bin/env python3
"""
Simple test to isolate the issue with the portal not loading
"""
import sys
import os

# Set the working directory
os.chdir(r"c:\Users\JordanHowell\OneDrive - Obion County Schools\Documents\Projects\Tracker\ocs-portal-py")
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

print("🔍 Testing portal components...")

try:
    print("1. Testing imports...")
    from fastapi import FastAPI
    print("   ✅ FastAPI import successful")
    
    from services import tickets_service
    print("   ✅ tickets_service import successful")
    
    print("\n2. Testing services...")
    tickets_service_instance = tickets_service
    print("   ✅ tickets_service instance created")
    
    print("\n3. Testing new method exists...")
    if hasattr(tickets_service_instance, 'get_closed_tickets_count'):
        print("   ✅ get_closed_tickets_count method exists")
    else:
        print("   ❌ get_closed_tickets_count method missing")
    
    print("\n4. Testing FastAPI app creation...")
    from main import app
    print("   ✅ FastAPI app created successfully")
    
    print("\n✅ All tests passed! The issue might be elsewhere.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n🔧 If the portal still won't load, the issue might be:")
print("   - Dependencies not installed")
print("   - Port already in use")
print("   - Database connection issues")
print("   - Missing environment variables")
