#!/usr/bin/env python3
"""
Force import with exception handling
"""
import sys
import os

try:
    # Set up the path first
    parent_dir = os.path.join(os.path.dirname(__file__), '..')
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    print("Attempting import...")
    
    # Try to execute the file directly
    exec(open('auth_service.py').read())
    
except Exception as e:
    print(f"Error during execution: {e}")
    import traceback
    traceback.print_exc()
