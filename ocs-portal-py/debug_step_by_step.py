#!/usr/bin/env python3
"""
Test auth_service imports step by step
"""

print("Starting import test...")

try:
    print("Step 1: Importing basic modules...")
    import msal
    import requests
    import jwt
    from datetime import datetime, timedelta
    from typing import Optional, Dict, List, Any
    from sqlalchemy.orm import Session
    import sys
    import os
    print("✓ Basic modules imported")
    
    print("Step 2: Setting up paths...")
    # Add the parent directory to path for ocs_shared_models
    parent_dir = os.path.join(os.path.dirname(__file__), '..')
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    print(f"✓ Added {parent_dir} to sys.path")
    
    print("Step 3: Importing shared models...")
    from ocs_shared_models.models import UserSession, GroupRole, AuditLog
    print("✓ Shared models imported")
    
    print("Step 4: Importing auth config...")
    from auth_config import AuthConfig
    print("✓ Auth config imported")
    
    print("Step 5: Testing class definition...")
    class TestAuthenticationService:
        def __init__(self, db: Session):
            self.db = db
            print("✓ Test class instantiated successfully")
    
    print("Step 6: Testing with actual auth service imports...")
    # Now try importing the actual module
    import importlib
    import auth_service
    importlib.reload(auth_service)
    print(f"auth_service contents: {[x for x in dir(auth_service) if not x.startswith('_')]}")
    
except Exception as e:
    print(f"Error at step: {e}")
    import traceback
    traceback.print_exc()
