#!/usr/bin/env python3
"""
Script to validate main.py syntax and identify any issues that might prevent routes from being registered.
"""

import sys
import ast
import traceback

def validate_syntax(file_path):
    """Validate Python syntax of a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Try to parse the AST
        ast.parse(content)
        print(f"✅ Syntax validation passed for {file_path}")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax Error in {file_path}:")
        print(f"   Line {e.lineno}: {e.text.strip() if e.text else 'Unknown'}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def try_import_main():
    """Try to import main.py and catch any import errors"""
    try:
        print("\n🔄 Attempting to import main.py...")
        
        # Add current directory to path
        sys.path.insert(0, '/home/nimda/Projects/Tracker/ocs-portal-py')
        
        import main
        print("✅ main.py imported successfully")
        
        # Check how many routes are registered
        if hasattr(main, 'app'):
            routes = main.app.routes
            print(f"📊 Found {len(routes)} routes registered in FastAPI app")
            
            # List all routes
            for route in routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    print(f"   {route.methods} {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Validating main.py syntax and imports...")
    
    # First validate syntax
    syntax_ok = validate_syntax('/home/nimda/Projects/Tracker/ocs-portal-py/main.py')
    
    if syntax_ok:
        # Then try importing
        import_ok = try_import_main()
        
        if not import_ok:
            print("\n💡 Import failed - this explains why routes aren't being registered!")
    else:
        print("\n💡 Syntax error found - this explains why routes aren't being registered!")
