#!/usr/bin/env python3
"""
Debug script to test importing auth_service
"""

try:
    print("Attempting to import auth_service...")
    import auth_service
    print("Module imported successfully")
    print(f"Module contents: {dir(auth_service)}")
    
    if hasattr(auth_service, 'AuthenticationService'):
        print("AuthenticationService class found!")
    else:
        print("AuthenticationService class NOT found!")
        
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
