#!/usr/bin/env python3
"""
Manual server startup script with detailed output
"""
import sys
import os
import asyncio
from fastapi import FastAPI

def main():
    print("🚀 OCS Portal Manual Startup")
    print("=" * 50)
    
    try:
        print("📦 Loading main application...")
        from main import app
        print("✅ Application loaded successfully!")
        
        print("🌐 Application is ready to serve requests")
        print("📍 To start the server manually, run:")
        print("   uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("🌍 Then visit: http://localhost:8000")
        
        # Test basic app functionality
        print("\n🔍 Testing basic app functions...")
        print(f"📊 App title: {app.title}")
        print(f"📋 Available routes:")
        for route in app.routes:
            if hasattr(route, 'path'):
                print(f"   - {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Application is ready! Start the server manually with uvicorn.")
    else:
        print("\n❌ Application startup failed. Check the errors above.")
        sys.exit(1)
