#!/usr/bin/env python3
"""
Development Environment Setup
Run this script to set up your local development environment
"""
import os
import subprocess
import sys

def setup_development_environment():
    """Set up local development environment"""
    print("🚀 Setting up OCS Tracker Development Environment")
    print("=" * 50)
    
    # Check Python version
    print("🐍 Checking Python version...")
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    dependencies = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "sqlite",
        "jinja2",
        "python-multipart",
        "httpx",
        "python-dotenv"
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
    
    # Create .env file for local development
    print("\n⚙️ Creating local environment configuration...")
    env_content = """# Local Development Environment
# Database URLs for local development
TICKETS_API_URL=http://localhost:8000
INVENTORY_API_URL=http://localhost:8001
PURCHASING_API_URL=http://localhost:8002

# Database settings
DATABASE_URL=sqlite:///./tracker_dev.db

# Development settings
ENVIRONMENT=development
DEBUG=true
"""
    
    with open("ocs-portal-py/.env", "w") as f:
        f.write(env_content)
    print("✅ Created .env file")
    
    # Create local database
    print("\n🗃️ Setting up local database...")
    try:
        # Run the database setup script
        subprocess.check_call([sys.executable, "setup_dev_data.py"])
        print("✅ Database setup complete")
    except subprocess.CalledProcessError:
        print("❌ Database setup failed")
    
    print("\n🎉 Development environment setup complete!")
    print("\n📝 Next steps:")
    print("1. cd ocs-portal-py")
    print("2. python main.py")
    print("3. Open http://localhost:8080 in your browser")
    
    return True

if __name__ == "__main__":
    setup_development_environment()
