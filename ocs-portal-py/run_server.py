#!/usr/bin/env python3
"""
Simple server starter for testing
"""
import sys
import os
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting OCS Portal server...")
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)
