"""
Service layer for making API calls to other OCS microservices
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime

# Service URLs - use environment variables in production
TICKETS_API_URL = os.getenv("TICKETS_API_URL", "http://ocs-tickets-api:8000")
INVENTORY_API_URL = os.getenv("INVENTORY_API_URL", "http://ocs-inventory-api:8000")
REQUISITION_API_URL = os.getenv("REQUISITION_API_URL", "http://ocs-requisition-api:8000")

class TicketsService:
    """Service for interacting with the Tickets API"""
    
    def __init__(self):
        self.base_url = TICKETS_API_URL
        self.timeout = 30.0

    async def get_tech_tickets(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get technology tickets with latest update messages"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"status_filter": status_filter} if status_filter else {}
                response = await client.get(f"{self.base_url}/api/tickets/tech", params=params)
                response.raise_for_status()
                tickets = response.json()
                
                # Add latest update message to each ticket
                for ticket in tickets:
                    latest_update = await self.get_latest_update_message("tech", ticket["id"])
                    ticket["latest_update_message"] = latest_update
                
                return tickets
        except httpx.RequestError as e:
            print(f"Error fetching tech tickets: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching tech tickets: {e}")
            return []

    async def get_tech_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific technology ticket"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/tech/{ticket_id}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            print(f"Error fetching tech ticket {ticket_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching tech ticket {ticket_id}: {e}")
            return None

    async def create_tech_ticket(self, ticket_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new technology ticket"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/tickets/tech", json=ticket_data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error creating tech ticket: {e}")
            return None

    async def update_tech_ticket_status(self, ticket_id: int, status: str) -> bool:
        """Update technology ticket status"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                data = {"status": status}
                response = await client.put(f"{self.base_url}/api/tickets/tech/{ticket_id}/status", data=data)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error updating tech ticket status: {e}")
            return False

    async def update_tech_ticket_comprehensive(self, ticket_id: int, update_data: Dict[str, Any]) -> bool:
        """Update technology ticket with status and message"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(f"{self.base_url}/api/tickets/tech/{ticket_id}", json=update_data)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error updating tech ticket comprehensively: {e}")
            return False

    async def get_maintenance_tickets(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get maintenance tickets with latest update messages"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"status_filter": status_filter} if status_filter else {}
                response = await client.get(f"{self.base_url}/api/tickets/maintenance", params=params)
                response.raise_for_status()
                tickets = response.json()
                
                # Add latest update message to each ticket
                for ticket in tickets:
                    latest_update = await self.get_latest_update_message("maintenance", ticket["id"])
                    ticket["latest_update_message"] = latest_update
                
                return tickets
        except httpx.RequestError as e:
            print(f"Error fetching maintenance tickets: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching maintenance tickets: {e}")
            return []

    async def get_maintenance_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific maintenance ticket"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/maintenance/{ticket_id}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            print(f"Error fetching maintenance ticket {ticket_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching maintenance ticket {ticket_id}: {e}")
            return None

    async def create_maintenance_ticket(self, ticket_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new maintenance ticket"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/tickets/maintenance", json=ticket_data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error creating maintenance ticket: {e}")
            return None

    async def update_maintenance_ticket_status(self, ticket_id: int, status: str) -> bool:
        """Update maintenance ticket status"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                data = {"status": status}
                response = await client.put(f"{self.base_url}/api/tickets/maintenance/{ticket_id}/status", data=data)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error updating maintenance ticket status: {e}")
            return False

    async def update_maintenance_ticket_comprehensive(self, ticket_id: int, update_data: Dict[str, Any]) -> bool:
        """Update maintenance ticket with status and message"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(f"{self.base_url}/api/tickets/maintenance/{ticket_id}", json=update_data)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error updating maintenance ticket comprehensively: {e}")
            return False

    async def get_buildings(self) -> List[Dict[str, Any]]:
        """Get all buildings from the database"""
        try:
            from database import get_db
            from ocs_shared_models import Building
            
            # Get database session
            db = next(get_db())
            
            # Query buildings directly from database
            buildings = db.query(Building).order_by(Building.name).all()
            
            # Convert to list of dictionaries
            buildings_data = [
                {
                    "id": building.id,
                    "name": building.name
                }
                for building in buildings
            ]
            
            db.close()
            return buildings_data
        except Exception as e:
            print(f"Error fetching buildings from database: {e}")
            return []

    async def get_building_rooms(self, building_id: int) -> List[Dict[str, Any]]:
        """Get rooms for a specific building from the database"""
        try:
            from database import get_db
            from ocs_shared_models import Room
            
            # Get database session
            db = next(get_db())
            
            # Query rooms for the specific building
            rooms = db.query(Room).filter(Room.building_id == building_id).order_by(Room.name).all()
            
            # Convert to list of dictionaries
            rooms_data = [
                {
                    "id": room.id,
                    "name": room.name,
                    "building_id": room.building_id
                }
                for room in rooms
            ]
            
            db.close()
            return rooms_data
        except Exception as e:
            print(f"Error fetching building rooms from database: {e}")
            return []

    async def get_ticket_updates(self, ticket_type: str, ticket_id: int) -> List[Dict[str, Any]]:
        """Get update history for a ticket"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/{ticket_type}/{ticket_id}/updates")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching ticket updates: {e}")
            return []

    async def get_latest_update_message(self, ticket_type: str, ticket_id: int) -> Optional[str]:
        """Get the latest update message for a ticket"""
        try:
            updates = await self.get_ticket_updates(ticket_type, ticket_id)
            if updates:
                # Sort by created_at descending and get the first one with a message
                for update in sorted(updates, key=lambda x: x.get('created_at', ''), reverse=True):
                    if update.get('update_message'):
                        return update['update_message']
            return None
        except Exception as e:
            print(f"Error fetching latest update message: {e}")
            return None

    async def clear_all_tech_tickets(self) -> Dict[str, Any]:
        """Clear all technology tickets"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(f"{self.base_url}/api/tickets/tech/clear")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error clearing tech tickets: {e}")
            return {"success": False, "message": f"Error clearing tech tickets: {str(e)}"}

    async def clear_all_maintenance_tickets(self) -> Dict[str, Any]:
        """Clear all maintenance tickets"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(f"{self.base_url}/api/tickets/maintenance/clear")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error clearing maintenance tickets: {e}")
            return {"success": False, "message": f"Error clearing maintenance tickets: {str(e)}"}

    async def export_tech_tickets_csv(self) -> bytes:
        """Export tech tickets to CSV and return file content"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/tech/export")
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"Error exporting tech tickets: {e}")
            raise Exception(f"Error exporting tech tickets: {str(e)}")

    async def export_maintenance_tickets_csv(self) -> bytes:
        """Export maintenance tickets to CSV and return file content"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/maintenance/export")
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"Error exporting maintenance tickets: {e}")
            raise Exception(f"Error exporting maintenance tickets: {str(e)}")

# Create service instances
tickets_service = TicketsService()

class InventoryService:
    """Service for interacting with the Inventory API"""
    
    def __init__(self):
        self.base_url = INVENTORY_API_URL
        self.timeout = 30.0

    # TODO: Add inventory service methods when needed

class RequisitionService:
    """Service for interacting with the Requisition API"""
    
    def __init__(self):
        self.base_url = REQUISITION_API_URL
        self.timeout = 30.0

    # TODO: Add requisition service methods when needed
