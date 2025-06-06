# OCS Tracker - Tests

This directory contains test scripts for various features of the OCS Tracker system.

## Dynamic Menu Tests

### `test_dynamic_menu.py`
Python script that tests the dynamic menu functionality by:
- Checking individual service health endpoints
- Verifying menu visibility logic
- Testing cache performance
- Providing detailed output about service status

**Usage:**
```bash
cd tests
python test_dynamic_menu.py
```

### `Test-DynamicMenu.ps1`
PowerShell script that tests the dynamic menu functionality by:
- Testing all service health endpoints
- Checking the portal's service status API
- Displaying menu visibility status
- Providing instructions for manual testing

**Usage:**
```powershell
cd tests
powershell -ExecutionPolicy Bypass -File .\Test-DynamicMenu.ps1
```

## Dynamic Menu Feature Overview

The dynamic menu system automatically shows/hides menu items based on the health status of their corresponding microservices:

- **Tickets Menu** → `ocs-tickets-api` health
- **Inventory Menu** → `ocs-inventory-api` health  
- **Requisitions Menu** → `ocs-requisition-api` health
- **Manage Menu** → `ocs-manage-api` health
- **Admin Menu** → Always visible (no service dependency)

### API Endpoints
- `GET /api/services/status` - Returns service health and menu visibility status
- `GET /health` - Individual service health check (available on all APIs)

### Manual Testing
1. Start all services: `docker-compose up -d`
2. Visit portal: http://localhost:8003
3. Stop a service: `docker-compose stop ocs-tickets-api`
4. Refresh portal - corresponding menu should disappear
5. Restart service: `docker-compose start ocs-tickets-api`
6. Refresh portal - menu should reappear

### Caching
Service health checks are cached for 30 seconds to prevent overwhelming services with requests.
