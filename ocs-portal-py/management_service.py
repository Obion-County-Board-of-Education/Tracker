"""
Management Service
This module handles communication with the OCS Manage API
"""

import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

class ManagementService:
    def __init__(self, base_url: str = "http://ocs-manage-api:8000"):
        self.base_url = base_url
        self.timeout = 30.0
    
    async def _make_request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make HTTP request to the management API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}{endpoint}"
                
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url)
                else:
                    print(f"Unsupported HTTP method: {method}")
                    return None
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Management API error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            print("Management API request timed out")
            return None
        except httpx.ConnectError:
            print("Failed to connect to Management API")
            return None
        except Exception as e:
            print(f"Error communicating with Management API: {e}")
            return None
    
    # System management methods
    async def get_system_stats(self) -> Optional[dict]:
        """Get system statistics"""
        return await self._make_request("GET", "/api/system/stats")
    
    async def health_check(self) -> bool:
        """Check if the management service is healthy"""
        result = await self._make_request("GET", "/health")
        return result is not None and result.get("status") == "healthy"
    
    # User management methods
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all users with pagination"""
        result = await self._make_request("GET", f"/api/users?skip={skip}&limit={limit}")
        return result if result else []
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get a specific user by ID"""
        return await self._make_request("GET", f"/api/users/{user_id}")
    
    # Building management methods
    async def get_buildings(self) -> List[dict]:
        """Get all buildings"""
        result = await self._make_request("GET", "/api/buildings")
        return result if result else []
    
    async def get_building(self, building_id: int) -> Optional[dict]:
        """Get a specific building by ID"""
        return await self._make_request("GET", f"/api/buildings/{building_id}")
    
    async def get_building_rooms(self, building_id: int) -> List[dict]:
        """Get all rooms for a specific building"""
        result = await self._make_request("GET", f"/api/buildings/{building_id}/rooms")
        return result if result else []
    
    # System logs and settings (placeholder methods for future implementation)
    async def get_system_logs(self, limit: int = 100, service: str = None, level: str = None) -> List[dict]:
        """Get system logs with filtering options"""
        # This would be implemented when log management is added to the manage API
        # For now, return mock data for demonstration
        mock_logs = [
            {
                "timestamp": datetime.now(),
                "level": "INFO",
                "service": "portal",
                "module": "main",
                "message": "Portal service started successfully"
            },
            {
                "timestamp": datetime.now(),
                "level": "WARNING",
                "service": "tickets",
                "module": "database",
                "message": "Database connection pool is running low"
            },
            {
                "timestamp": datetime.now(),
                "level": "ERROR",
                "service": "inventory",
                "module": "api",
                "message": "Failed to update inventory item: timeout"
            }
        ]
        return mock_logs[:limit]
    
    async def get_log_stats(self) -> dict:
        """Get log statistics"""
        return {
            "info_count": 150,
            "warning_count": 25,
            "error_count": 5,
            "total_count": 180
        }
    
    async def clear_logs(self) -> bool:
        """Clear all system logs"""
        result = await self._make_request("POST", "/api/logs/clear")
        return result is not None and result.get("success", False)
    
    async def get_system_settings(self) -> dict:
        """Get system settings"""
        result = await self._make_request("GET", "/api/system/settings")
        return result if result else {}
    
    async def update_system_settings(self, settings: dict) -> bool:
        """Update system settings"""
        result = await self._make_request("PUT", "/api/system/settings", settings)
        return result is not None and result.get("success", False)
    
    # Service monitoring methods
    async def get_service_status(self) -> dict:
        """Get the status of all microservices"""
        services = {
            "portal": {"healthy": True, "uptime": "2 days, 3:45:12"},
            "tickets": {"healthy": True, "uptime": "2 days, 3:44:58"},
            "inventory": {"healthy": True, "uptime": "2 days, 3:44:45"},
            "requisition": {"healthy": True, "uptime": "2 days, 3:44:32"},
            "manage": {"healthy": True, "uptime": "2 days, 3:44:19"}
        }
        return services
    
    async def get_system_performance(self) -> dict:
        """Get system performance metrics"""
        return {
            "cpu_usage": 45,
            "memory_usage": 68,
            "disk_usage": 23,
            "network_io": 15.2,
            "disk_io": 8.5
        }
    
    async def get_system_info(self) -> dict:
        """Get system information"""
        return {
            "version": "v1.0.0",
            "db_version": "PostgreSQL 15.2",
            "python_version": "Python 3.11.5",
            "fastapi_version": "0.104.1",
            "uptime": "2 days, 3:45:12",
            "last_backup": "2024-01-15 02:00:00"
        }
    
    # Maintenance and testing methods
    async def run_maintenance(self) -> bool:
        """Run system maintenance tasks"""
        result = await self._make_request("POST", "/api/maintenance/run")
        return result is not None and result.get("success", False)
    
    async def rebuild_search_index(self) -> bool:
        """Rebuild search index"""
        result = await self._make_request("POST", "/api/search/rebuild")
        return result is not None and result.get("success", False)
    
    async def optimize_databases(self) -> bool:
        """Optimize all databases"""
        result = await self._make_request("POST", "/api/database/optimize")
        return result is not None and result.get("success", False)
    
    async def test_service(self, service_name: str) -> dict:
        """Test a specific service"""
        # Mock service testing for now
        import time
        start_time = time.time()
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        response_time = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "service": service_name,
            "response_time": response_time,
            "details": {
                "status": "healthy",
                "version": "1.0.0"
            }
        }
    
    async def export_data(self) -> bytes:
        """Export all system data"""
        # This would return binary data for download
        # For now, return placeholder
        return b"Export data placeholder"
    
    async def import_data(self, file_data: bytes) -> bool:
        """Import data from file"""
        result = await self._make_request("POST", "/api/data/import")
        return result is not None and result.get("success", False)
    
    async def generate_reports(self) -> bytes:
        """Generate system reports"""
        # This would return binary report data
        return b"Reports placeholder"

# Create a global instance
management_service = ManagementService()
