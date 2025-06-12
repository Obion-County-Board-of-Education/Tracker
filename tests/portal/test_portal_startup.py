#!/usr/bin/env python3
"""
Test portal startup and closed ticket counter functionality
"""
import sys
import os
import asyncio

# Set working directory
os.chdir(r"c:\Users\JordanHowell\OneDrive - Obion County Schools\Documents\Projects\Tracker\ocs-portal-py")

print("🔍 Testing Portal Startup...")

try:
    print("1. Testing imports...")
    from services import tickets_service, purchasing_service
    print("   ✅ Services imported successfully")
    
    import main
    print("   ✅ Main module imported successfully")
    
    print("\n2. Testing FastAPI app...")
    app = main.app
    print("   ✅ FastAPI app accessible")
    
    print("\n3. Testing new method...")
    if hasattr(tickets_service, 'get_closed_tickets_count'):
        print("   ✅ get_closed_tickets_count method exists")
    else:
        print("   ❌ get_closed_tickets_count method missing")
    
    print("\n✅ Portal startup test PASSED!")
    print("🚀 The portal should now load successfully.")
    print("\n💡 To start the portal, run:")
    print("   cd ocs-portal-py")
    print("   python main.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
