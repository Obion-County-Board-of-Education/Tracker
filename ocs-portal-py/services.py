"""
Service layer for making API calls to other OCS microservices
"""
import httpx
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import Request

# Service URLs - use environment variables in production
TICKETS_API_URL = os.getenv("TICKETS_API_URL", "http://ocs-tickets-api:8000")
PURCHASING_API_URL = os.getenv("PURCHASING_API_URL", "http://ocs-purchasing-api:8000")
FORMS_API_URL = os.getenv("FORMS_API_URL", "http://ocs-forms-api:8000")
MANAGE_API_URL = os.getenv("MANAGE_API_URL", "http://ocs-manage-api:8000")

def get_service_for_request(request: Request):
    """Factory function to create service instances with authentication token"""
    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    
    # Create service instances with the token
    tickets = TicketsService(auth_token=session_token)
    purchasing = PurchasingService(auth_token=session_token)
    inventory = InventoryService(auth_token=session_token)
    forms = FormsService(auth_token=session_token)
    management = ManagementService(auth_token=session_token)
    
    return {
        "tickets": tickets,
        "purchasing": purchasing,
        "inventory": inventory,
        "forms": forms,
        "management": management
    }

class TicketsService:
    """Service for interacting with the Tickets API"""
    
    def __init__(self, auth_token: str = None):
        self.base_url = TICKETS_API_URL
        self.timeout = 30.0
        self.auth_token = auth_token
        
    def _get_headers(self):
        """Get headers with auth token if available"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def get_tech_tickets(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get technology tickets with latest update messages"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"status_filter": status_filter} if status_filter else {}
                response = await client.get(
                    f"{self.base_url}/api/tickets/tech", 
                    params=params,
                    headers=self._get_headers()
                )
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
                response = await client.get(f"{self.base_url}/api/tickets/tech/{ticket_id}", headers=self._get_headers())
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
                response = await client.post(f"{self.base_url}/api/tickets/tech", json=ticket_data, headers=self._get_headers())
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
                response = await client.put(f"{self.base_url}/api/tickets/tech/{ticket_id}/status", data=data, headers=self._get_headers())
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error updating tech ticket status: {e}")
            return False

    async def update_tech_ticket_comprehensive(self, ticket_id: int, update_data: Dict[str, Any]) -> bool:
        """Update technology ticket with status and message"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(f"{self.base_url}/api/tickets/tech/{ticket_id}", json=update_data, headers=self._get_headers())
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
                response = await client.get(f"{self.base_url}/api/tickets/maintenance", params=params, headers=self._get_headers())
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
                response = await client.get(f"{self.base_url}/api/tickets/maintenance/{ticket_id}", headers=self._get_headers())
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
                response = await client.post(f"{self.base_url}/api/tickets/maintenance", json=ticket_data, headers=self._get_headers())
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
                response = await client.put(f"{self.base_url}/api/tickets/maintenance/{ticket_id}/status", data=data, headers=self._get_headers())
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error updating maintenance ticket status: {e}")
            return False

    async def update_maintenance_ticket_comprehensive(self, ticket_id: int, update_data: Dict[str, Any]) -> bool:
        """Update maintenance ticket with status and message"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(f"{self.base_url}/api/tickets/maintenance/{ticket_id}", json=update_data, headers=self._get_headers())
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
                response = await client.get(f"{self.base_url}/api/tickets/{ticket_type}/{ticket_id}/updates", headers=self._get_headers())
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

    async def get_tech_archives(self) -> List:
        """Get list of available tech ticket archives"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/tech/archives", headers=self._get_headers())
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
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching tech archive tickets: {e}")
            return {"tickets": [], "archive_name": archive_name, "count": 0}

    async def delete_tech_archive(self, archive_name: str) -> Dict:
        """Delete a tech ticket archive"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/tech/archives/delete/{archive_name}", headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error deleting tech archive: {e}")
            return {"success": False, "message": f"Error deleting archive: {str(e)}"}

    async def get_maintenance_archives(self) -> List:
        """Get list of available maintenance ticket archives"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/maintenance/archives", headers=self._get_headers())
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
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching maintenance archive tickets: {e}")
            return {"tickets": [], "archive_name": archive_name, "count": 0}

    async def delete_maintenance_archive(self, archive_name: str) -> Dict:
        """Delete a maintenance ticket archive"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/maintenance/archives/delete/{archive_name}", headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error deleting maintenance archive: {e}")
            return {"success": False, "message": f"Error deleting archive: {str(e)}"}

    async def roll_tech_database(self, archive_name: str) -> Dict:
        """Roll tech database - archive current tickets and create new table"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/tickets/tech/roll-database?archive_name={archive_name}", headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error rolling tech database: {e}")
            return {"success": False, "message": str(e)}
    
    async def roll_maintenance_database(self, archive_name: str) -> Dict:
        """Roll maintenance database - archive current tickets and create new table"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/tickets/maintenance/roll-database?archive_name={archive_name}", headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error rolling maintenance database: {e}")
            return {"success": False, "message": str(e)}

    # Note: Clear operations are handled directly by portal proxy routes
    # Portal acts as thin proxy and delegates to tickets module for business logic

    async def get_tickets_count(self, ticket_type: str, status: str = "open") -> int:
        """Get count of tickets by type and status"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/api/tickets/{ticket_type}?status_filter={status}"
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                tickets = response.json()
                return len(tickets)
        except Exception as e:
            print(f"Error fetching {status} {ticket_type} tickets count: {e}")
            return 0

    async def get_closed_tickets_count(self, ticket_type: str) -> int:
        """Get count of closed tickets by type"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/api/tickets/{ticket_type}?status_filter=closed"
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                tickets = response.json()
                return len(tickets)
        except Exception as e:
            print(f"Error fetching closed {ticket_type} tickets count: {e}")
            return 0

    async def export_tech_tickets_csv(self) -> str:
        """Export tech tickets to CSV format"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/tech/export", headers=self._get_headers())
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Error exporting tech tickets CSV: {e}")
            return ""

    async def export_maintenance_tickets_csv(self) -> str:
        """Export maintenance tickets to CSV format"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tickets/maintenance/export", headers=self._get_headers())
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Error exporting maintenance tickets CSV: {e}")
            return ""

    async def import_tech_tickets_csv(self, file_content: bytes, filename: str, operation: str) -> Dict:
        """Import tech tickets from CSV"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare multipart form data
                files = {"file": (filename, file_content, "text/csv")}
                data = {"operation": operation}
                response = await client.post(
                    f"{self.base_url}/api/tickets/tech/import", 
                    files=files, 
                    data=data, 
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error importing tech tickets CSV: {e}")
            return {"success": False, "message": f"Import failed: {str(e)}"}

    async def import_maintenance_tickets_csv(self, file_content: bytes, filename: str, operation: str) -> Dict:
        """Import maintenance tickets from CSV"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare multipart form data
                files = {"file": (filename, file_content, "text/csv")}
                data = {"operation": operation}
                response = await client.post(
                    f"{self.base_url}/api/tickets/maintenance/import", 
                    files=files, 
                    data=data, 
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error importing maintenance tickets CSV: {e}")
            return {"success": False, "message": f"Import failed: {str(e)}"}

class InventoryService:
    """Service for interacting with the Inventory functionality via Manage API"""
    
    def __init__(self, auth_token: str = None):
        self.base_url = MANAGE_API_URL
        self.timeout = 30.0
        self.auth_token = auth_token
        
    def _get_headers(self):
        """Get headers with auth token if available"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    # TODO: Add inventory service methods when needed

class PurchasingService:
    """Service for interacting with the Purchasing API"""
    
    def __init__(self, auth_token: str = None):
        self.base_url = PURCHASING_API_URL
        self.timeout = 30.0
        self.auth_token = auth_token
        
    def _get_headers(self):
        """Get headers with auth token if available"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    # TODO: Add purchasing service methods when needed

class FormsService:
    """Service for interacting with the Forms API"""
    
    def __init__(self, auth_token: str = None):
        self.base_url = FORMS_API_URL
        self.timeout = 30.0
        self.auth_token = auth_token
        
    def _get_headers(self):
        """Get headers with auth token if available"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    # TODO: Add forms service methods when needed

class ManagementService:
    """Service for interacting with the Management API"""
    
    def __init__(self, auth_token: str = None):
        self.base_url = MANAGE_API_URL
        self.timeout = 30.0
        self.auth_token = auth_token
        
    def _get_headers(self):
        """Get headers with auth token if available"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    # TODO: Add management service methods when needed

    # Inventory management methods (delegated to manage API)
    async def get_inventory_items(self, school: str = None, sort: str = "newest"):
        """Get inventory items from manage API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if school:
                    params["school"] = school
                if sort:
                    params["sort"] = sort
                    
                response = await client.get(f"{self.base_url}/api/inventory", 
                                          params=params, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching inventory items: {e}")
            return []

    async def get_inventory_item(self, item_id: int):
        """Get specific inventory item"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/inventory/{item_id}", 
                                          headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching inventory item {item_id}: {e}")
            return None

    async def create_inventory_item(self, item_data: dict):
        """Create new inventory item"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/inventory", 
                                           json=item_data, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error creating inventory item: {e}")
            return {"success": False, "message": f"Failed: {str(e)}"}

    async def update_inventory_item(self, item_id: int, item_data: dict):
        """Update inventory item"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(f"{self.base_url}/api/inventory/{item_id}", 
                                          json=item_data, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error updating inventory item {item_id}: {e}")
            return {"success": False, "message": f"Failed: {str(e)}"}

    async def delete_inventory_item(self, item_id: int):
        """Delete inventory item"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(f"{self.base_url}/api/inventory/{item_id}", 
                                             headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error deleting inventory item {item_id}: {e}")
            return {"success": False, "message": f"Failed: {str(e)}"}

    async def search_inventory(self, tag: str = None, serial: str = None, po_number: str = None):
        """Search inventory items"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if tag:
                    params["tag"] = tag
                if serial:
                    params["serial"] = serial
                if po_number:
                    params["po_number"] = po_number
                    
                response = await client.get(f"{self.base_url}/api/inventory/search", 
                                          params=params, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error searching inventory: {e}")
            return []

    async def get_inventory_stats(self):
        """Get inventory statistics"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/inventory/stats", 
                                          headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching inventory stats: {e}")
            return {}

# Create default service instances (without authentication)
# These will be used for routes that don't require authentication
tickets_service = TicketsService()
purchasing_service = PurchasingService()
inventory_service = InventoryService()
forms_service = FormsService()
management_service = ManagementService()
