#!/usr/bin/env python3
"""
Debug script to test menu context rendering
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import Request
from fastapi.templating import Jinja2Templates
import asyncio

# Initialize templates
templates = Jinja2Templates(directory="templates")

async def get_menu_context():
    """Test menu context function"""
    print("🔧 Testing menu context function")
    return {"menu_visibility": {
        "tickets": True,
        "inventory": True,
        "manage": True,
        "requisitions": True,
        "admin": True
    }}

async def render_template(template_name: str, context: dict):
    """Test render template function"""
    print(f"🔧 Testing render_template with {template_name}")
    print(f"   Context keys: {list(context.keys())}")
    
    menu_context = await get_menu_context()
    print(f"   Menu context keys: {list(menu_context.keys())}")
    
    final_context = {**context, **menu_context}
    print(f"   Final context keys: {list(final_context.keys())}")
    
    # Check if menu_visibility is in final context
    if 'menu_visibility' in final_context:
        print(f"   ✅ menu_visibility found: {final_context['menu_visibility']}")
    else:
        print(f"   ❌ menu_visibility missing!")
    
    return templates.TemplateResponse(template_name, final_context)

async def test_context():
    """Test the context generation"""
    print("🔍 Testing menu context generation...")
    
    # Mock request object
    class MockRequest:
        def __init__(self):
            self.url = "http://localhost:8003/users/list"
    
    request = MockRequest()
    
    # Test the render_template function
    try:
        context = {"request": request, "users": []}
        result = await render_template("users.html", context)
        print("✅ Template rendering successful")
    except Exception as e:
        print(f"❌ Template rendering failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_context())
