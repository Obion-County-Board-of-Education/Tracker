"""
Service health checking for dynamic menu functionality
"""
import httpx
import asyncio
import os
from typing import Dict
from datetime import datetime, timedelta

# Service URLs and their corresponding menu items
SERVICE_CONFIG = {
    "tickets": {
        "url": os.getenv("TICKETS_API_URL", "http://host.docker.internal:8000"),
        "menu_item": "tickets",
        "check_endpoint": "/health"
    },
    "purchasing": {
        "url": os.getenv("PURCHASING_API_URL", "http://host.docker.internal:8002"),
        "menu_item": "purchasing",
        "check_endpoint": "/health"
    },
    "forms": {
        "url": os.getenv("FORMS_API_URL", "http://host.docker.internal:8005"),
        "menu_item": "forms",
        "check_endpoint": "/health"
    },
    "manage": {
        "url": os.getenv("MANAGE_API_URL", "http://host.docker.internal:8004"),
        "menu_item": "manage",
        "check_endpoint": "/health"
    }
}

class ServiceHealthChecker:
    """Checks the health status of microservices for dynamic menu visibility"""
    
    def __init__(self, cache_duration: int = 30):
        """
        Initialize the health checker
        
        Args:
            cache_duration: How long to cache health status in seconds
        """
        self.cache_duration = cache_duration
        self.health_cache = {}
        self.last_check = {}
        self.timeout = 5.0  # Faster timeout for health checks
    async def check_service_health(self, service_name: str, auth_token: str = None) -> bool:
        """
        Check if a specific service is healthy
        
        Args:
            service_name: Name of the service to check
            auth_token: Optional auth token to include in request
            
        Returns:
            bool: True if service is healthy, False otherwise
        """
        if service_name not in SERVICE_CONFIG:
            return False
            
        # Check cache first
        now = datetime.now()
        if (service_name in self.health_cache and 
            service_name in self.last_check and
            now - self.last_check[service_name] < timedelta(seconds=self.cache_duration)):
            return self.health_cache[service_name]
        
        # Perform health check
        config = SERVICE_CONFIG[service_name]
        health_url = f"{config['url']}{config['check_endpoint']}"
        
        # Setup headers if auth token is provided
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(health_url, headers=headers)
                is_healthy = response.status_code == 200
                
                # Cache the result
                self.health_cache[service_name] = is_healthy
                self.last_check[service_name] = now
                
                return is_healthy
                
        except httpx.TimeoutException:
            print(f"Health check timeout for {service_name}")
            self.health_cache[service_name] = False
            self.last_check[service_name] = now
            return False
        except httpx.ConnectError:
            print(f"Connection error for {service_name}")
            self.health_cache[service_name] = False
            self.last_check[service_name] = now
            return False
        except Exception as e:
            print(f"Health check error for {service_name}: {e}")
            self.health_cache[service_name] = False
            self.last_check[service_name] = now
            return False
    async def check_all_services(self, auth_token: str = None) -> Dict[str, bool]:
        """
        Check health status of all configured services
        
        Args:
            auth_token: Optional auth token to include in request
            
        Returns:
            Dict mapping service names to their health status
        """
        tasks = []
        service_names = []
        
        for service_name in SERVICE_CONFIG.keys():
            tasks.append(self.check_service_health(service_name, auth_token))
            service_names.append(service_name)# Run all health checks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {}
        for service_name, result in zip(service_names, results):
            if isinstance(result, Exception):
                health_status[service_name] = False
            else:
                health_status[service_name] = result
                
        return health_status
    async def get_menu_visibility(self, auth_token: str = None) -> Dict[str, bool]:
        """
        Get menu visibility mapping based on service health
        
        Args:
            auth_token: Optional auth token to include in request
            
        Returns:
            Dict mapping menu items to their visibility status
        """
        health_status = await self.check_all_services(auth_token)
        
        menu_visibility = {}
        for service_name, config in SERVICE_CONFIG.items():
            menu_item = config["menu_item"]
            menu_visibility[menu_item] = health_status.get(service_name, False)
          # Admin menu is always visible (doesn't depend on external services)
        menu_visibility["admin"] = True
        return menu_visibility
    
    async def get_service_health(self, auth_token: str = None) -> Dict[str, bool]:
        """
        Get service health status (alias for check_all_services)
        
        Args:
            auth_token: Optional auth token to include in health check requests
            
        Returns:
            Dict mapping service names to their health status
        """
        return await self.check_all_services()
    
    def clear_cache(self):
        """Clear the health status cache"""
        self.health_cache.clear()
        self.last_check.clear()

# Global health checker instance
health_checker = ServiceHealthChecker()
