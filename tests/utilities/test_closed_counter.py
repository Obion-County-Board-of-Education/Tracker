#!/usr/bin/env python3
"""
Test script to verify the closed ticket counter functionality
"""
import sys
import os
import asyncio
import json

# Add the portal directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))

async def test_closed_counter():
    """Test the closed ticket counter functionality"""
    print("Testing closed ticket counter functionality...")
    
    try:
        # Import the services module
        from services import TicketsService
        
        # Create an instance of the service
        tickets_service = TicketsService()
        
        # Test getting closed tech tickets count
        print("\n1. Testing tech tickets closed count...")
        try:
            tech_closed_count = await tickets_service.get_closed_tickets_count("tech")
            print(f"   Tech closed tickets count: {tech_closed_count}")
        except Exception as e:
            print(f"   Error getting tech closed count: {e}")
        
        # Test getting closed maintenance tickets count
        print("\n2. Testing maintenance tickets closed count...")
        try:
            maintenance_closed_count = await tickets_service.get_closed_tickets_count("maintenance")
            print(f"   Maintenance closed tickets count: {maintenance_closed_count}")
        except Exception as e:
            print(f"   Error getting maintenance closed count: {e}")
        
        print("\n✅ Closed ticket counter functionality test completed!")
        
    except ImportError as e:
        print(f"❌ Error importing services: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_closed_counter())
