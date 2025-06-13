"""
Service layer for making API calls to other OCS microservices
"""
import httpx
import os
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

    async def get_closed_tickets_count(self, ticket_type: str) -> int:
        """Get count of closed tickets for a specific type (tech or maintenance)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                endpoint = f"{self.base_url}/api/tickets/{ticket_type}"
                params = {"status_filter": "closed"}
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                tickets = response.json()
                return len(tickets)
        except Exception as e:
            print(f"Error fetching closed {ticket_type} tickets count: {e}")
            return 0

    async def get_tech_archives(self) -> List:
        """Get list of available tech ticket archives"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tickets/tech/archives")
                response.raise_for_status()
                data = response.json()
                return data.get("archives", [])
        except Exception as e:
            print(f"Error fetching tech archives: {e}")
            return []
    
    async def get_tech_archive_tickets(self, archive_name: str, status_filter: Optional[str] = None) -> Dict:
        """Get tickets from a specific tech ticket archive"""
        try:
            url = f"{self.base_url}/api/tickets/tech/archives/{archive_name}"
            if status_filter:
                url += f"?status_filter={status_filter}"
                
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching tech archive tickets: {e}")
            return {"tickets": [], "archive_name": archive_name, "count": 0}
    
    async def get_maintenance_archives(self) -> List:
        """Get list of available maintenance ticket archives"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tickets/maintenance/archives")
                response.raise_for_status()
                data = response.json()
                return data.get("archives", [])
        except Exception as e:
            print(f"Error fetching maintenance archives: {e}")
            return []
    
    async def get_maintenance_archive_tickets(self, archive_name: str, status_filter: Optional[str] = None) -> Dict:
        """Get tickets from a specific maintenance ticket archive"""
        try:
            url = f"{self.base_url}/api/tickets/maintenance/archives/{archive_name}"
            if status_filter:
                url += f"?status_filter={status_filter}"
                
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching maintenance archive tickets: {e}")
            return {"tickets": [], "archive_name": archive_name, "count": 0}

    async def roll_tech_database(self, archive_name: str) -> Dict:
        """Roll tech database - archive current tickets and create new table"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/tickets/tech/roll-database?archive_name={archive_name}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error rolling tech database: {e}")
            return {"success": False, "message": str(e)}
    
    async def roll_maintenance_database(self, archive_name: str) -> Dict:
        """Roll maintenance database - archive current tickets and create new table"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/tickets/maintenance/roll-database?archive_name={archive_name}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error rolling maintenance database: {e}")
            return {"success": False, "message": str(e)}

    async def export_tech_tickets_csv(self) -> str:
        """Export tech tickets to CSV"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/tech/export")
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Error exporting tech tickets CSV: {e}")
            raise

    async def export_maintenance_tickets_csv(self) -> str:
        """Export maintenance tickets to CSV"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/maintenance/export")
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Error exporting maintenance tickets CSV: {e}")
            raise

    async def import_tech_tickets_csv(self, file_content: str, operation: str) -> Dict:
        """Import tech tickets from CSV"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/tickets/tech/import",
                    data={"operation": operation},
                    files={"file": ("tickets.csv", file_content, "text/csv")}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error importing tech tickets CSV: {e}")
            raise

    async def clear_all_tech_tickets(self) -> Dict:
        """Clear all tech tickets"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/tickets/tech/clear")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error clearing tech tickets: {e}")
            raise

    async def clear_all_maintenance_tickets(self) -> Dict:
        """Clear all maintenance tickets"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/tickets/maintenance/clear")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error clearing maintenance tickets: {e}")
            raise

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

class PurchasingService:
    """Service for interacting with the Purchasing API"""
    
    def __init__(self):
        self.base_url = os.getenv("PURCHASING_API_URL", "http://ocs-purchasing-api:8000")
        self.timeout = 30.0

    async def get_requisitions(self, status_filter: Optional[str] = None, department: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get requisitions with optional filtering"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if status_filter:
                    params["status"] = status_filter
                if department:
                    params["department"] = department
                if priority:
                    params["priority"] = priority
                    
                response = await client.get(f"{self.base_url}/api/requisitions", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            print(f"Error fetching requisitions: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching requisitions: {e}")
            return []

    async def get_purchase_orders(self, status_filter: Optional[str] = None, vendor: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get purchase orders with optional filtering"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if status_filter:
                    params["status"] = status_filter
                if vendor:
                    params["vendor"] = vendor
                    
                response = await client.get(f"{self.base_url}/api/purchase-orders", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            print(f"Error fetching purchase orders: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching purchase orders: {e}")
            return []

# Create service instances
tickets_service = TicketsService()
purchasing_service = PurchasingService()
