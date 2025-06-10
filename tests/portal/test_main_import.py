#!/usr/bin/env python3
"""
Test script to isolate main.py import issues
"""
import sys
import os

print("Current working directory:", os.getcwd())
print("Python path before modification:", sys.path[:3])

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
print("Python path after modification:", sys.path[:5])

try:
    print("Testing ocs_shared_models import...")
    from ocs_shared_models import User, Building, Room, SystemMessage
    print("✅ ocs_shared_models import successful")
except Exception as e:
    print(f"❌ ocs_shared_models import failed: {e}")
    sys.exit(1)

try:
    print("Testing database import...")
    from database import get_db, init_database
    print("✅ database import successful")
except Exception as e:
    print(f"❌ database import failed: {e}")

try:
    print("Testing services import...")
    from services import tickets_service
    print("✅ services import successful")
except Exception as e:
    print(f"❌ services import failed: {e}")

try:
    print("Testing management_service import...")
    from management_service import management_service
    print("✅ management_service import successful")
except Exception as e:
    print(f"❌ management_service import failed: {e}")

try:
    print("Testing service_health import...")
    from service_health import health_checker
    print("✅ service_health import successful")
except Exception as e:
    print(f"❌ service_health import failed: {e}")

try:
    print("Testing FastAPI imports...")
    from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
    from fastapi.responses import RedirectResponse, Response
    from fastapi.templating import Jinja2Templates
    from fastapi.staticfiles import StaticFiles
    from sqlalchemy.orm import Session
    from datetime import datetime
    print("✅ FastAPI imports successful")
except Exception as e:
    print(f"❌ FastAPI imports failed: {e}")

print("All imports tested successfully!")
