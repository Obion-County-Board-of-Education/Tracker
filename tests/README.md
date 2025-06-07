# OCS Portal Test Suite

This directory contains all test files for the OCS Portal system, organized by test type and component.

## Test Organization

### 📁 `unit/` - Unit Tests
- **`test_timezone.py`** - Tests for Central Time timezone conversion utilities
- **`test_menu_context_fix.py`** - Tests for menu context helper functions
- **`test_menu_error.py`** - Tests for menu error handling
- **`test_dynamic_menu.py`** - Tests for dynamic menu generation

### 📁 `portal/` - Portal-Specific Tests
- **`test_route_accessibility.py`** - Tests route HTTP status and accessibility
- **`test_route_availability.py`** - Tests route registration and availability
- **`test_routes.py`** - General route testing
- **`test_pages_final.py`** - Tests for specific page functionality
- **`test_user_building_routes.py`** - Tests for user and building management routes
- **`test_users_function.py`** - Tests for user-related functions
- **`test_priority_removal.py`** - Tests for priority field removal feature
- **`test_portal_detailed.py`** - Detailed portal functionality tests
- **`test_menu_context_debug.py`** - Debug tests for menu context issues
- **`test_main_import.py`** - Tests for main module imports
- **`test_import.py`** - General import tests
- **`test_app.py`** - Application-level tests
- **`debug_routes_test.py`** - Route debugging utilities
- **`debug_routes_final.py`** - Final route debugging scripts
- **`simple_route_test.py`** - Simple route testing utilities
- **`verify_priority_removal.py`** - Priority removal feature verification

### 📁 `api/` - API Tests  
- **`test_api_timezone.py`** - Tests for API timezone handling
- **`test_maintenance_update.py`** - Tests for maintenance ticket API updates
- **`test_update.py`** - General update API tests
- **`check_services.py`** - Service health checking utility
- **`check_buildings.py`** - Buildings API verification

### 📁 `integration/` - Integration Tests
- **`test_comprehensive_verification.py`** - Full system verification tests
- **`final_verification.py`** - Final end-to-end verification

## Running Tests

### Prerequisites
```powershell
# Ensure containers are running
docker-compose up -d

# Install test dependencies if needed
pip install requests pytest
```

### Run Individual Tests
```powershell
# Run a specific test
python tests/portal/test_route_accessibility.py

# Run integration tests
python tests/integration/final_verification.py
```

### Run All Tests
```powershell
# Run all tests with pytest (if configured)
pytest tests/

# Run PowerShell test scripts
.\tests\Test-DynamicMenu.ps1
```

## Test Categories

- **🔧 Unit Tests**: Test individual functions and utilities in isolation
- **🌐 Portal Tests**: Test web interface functionality and routing
- **📡 API Tests**: Test REST API endpoints and data handling  
- **🔗 Integration Tests**: Test complete workflows and system interactions

## Test Data

Most tests use:
- **Mock data** for unit tests
- **Local test server** (localhost:8003) for integration tests
- **Fallback data** when database connections fail

## Notes

- Tests were created during the debugging and fix process for the OCS Portal system
- Many tests include both success and error path verification
- Integration tests require the Docker containers to be running
- Some tests include browser automation capabilities

## Recent Fixes Verified

These tests verify the following completed fixes:
- ✅ Timezone conversion to Central Time
- ✅ Close Ticket button removal
- ✅ Emergency Issues section removal  
- ✅ Users and Buildings page functionality
- ✅ Menu context error resolution

## Legacy Dynamic Menu Tests

### `test_dynamic_menu.py` (moved to unit/)
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
