#!/usr/bin/env python3
"""
Debug script to test specific imports from auth_service
"""

try:
    print("Testing individual imports...")
    
    # Test MSAL
    print("Testing MSAL...")
    import msal
    print("✓ MSAL imported")
    
    # Test requests
    print("Testing requests...")
    import requests
    print("✓ requests imported")
    
    # Test JWT
    print("Testing JWT...")
    import jwt
    print("✓ JWT imported")
    
    # Test datetime
    print("Testing datetime...")
    from datetime import datetime, timedelta
    print("✓ datetime imported")
    
    # Test SQLAlchemy
    print("Testing SQLAlchemy...")
    from sqlalchemy.orm import Session
    print("✓ SQLAlchemy imported")
    
    # Test shared models
    print("Testing shared models...")
    try:
        from ocs_shared_models.models import UserSession, GroupRole, AuditLog
        print("✓ Shared models imported directly")
    except ImportError as e:
        print(f"✗ Direct import failed: {e}")
        print("Trying alternative import...")
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ocs_shared_models'))
        from models import UserSession, GroupRole, AuditLog
        print("✓ Shared models imported via alternative path")
    
    # Test auth config
    print("Testing auth config...")
    try:
        from auth_config import AuthConfig
        print("✓ Auth config imported")
    except ImportError as e:
        print(f"✗ Auth config import failed: {e}")
        
    print("\nAll imports successful, checking auth_service module import...")
    import auth_service
    print(f"auth_service module imported, contents: {[x for x in dir(auth_service) if not x.startswith('_')]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
