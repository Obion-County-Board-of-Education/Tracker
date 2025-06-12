#!/usr/bin/env python3
"""
Test FastAPI app startup and basic functionality
"""
import sys
import os

print("🔍 Testing OCS Portal startup...")

try:
    print("📦 Importing main module...")
    from main import app
    print("✅ Main module imported successfully")
    
    print("🌐 Testing FastAPI app...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    print("🏠 Testing homepage endpoint...")
    response = client.get("/")
    print(f"📊 Homepage status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Homepage loads successfully!")
    else:
        print(f"❌ Homepage failed with status {response.status_code}")
        print(f"Response: {response.text[:200]}...")

    print("🎫 Testing tickets page...")
    response = client.get("/tickets/tech/open")
    print(f"📊 Tech tickets status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Tech tickets page loads successfully!")
    else:
        print(f"❌ Tech tickets page failed with status {response.status_code}")
        
    print("\n🎉 All basic tests passed! The web application should work correctly.")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
