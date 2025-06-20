# OCS Microservices Architecture Documentation

## Overview
This document outlines the microservices architecture for the OCS (Obion County Schools) system, ensuring proper separation of concerns and service boundaries.

## Architecture Principles
✅ **Database Separation**: Each microservice has its own dedicated database
✅ **API-Only Communication**: Services communicate exclusively through HTTP APIs
✅ **No Direct Database Access**: Services cannot access other services' databases directly
✅ **Service Independence**: Each service can be deployed and scaled independently

## Service Overview

### 1. OCS Portal (Python) - Port 8003
- **Database**: `ocs_portal`
- **Responsibility**: User interface and orchestration
- **Communication**: Makes API calls to other services
- **Direct Access**: Only to its own database for system messages, users, buildings, rooms

### 2. OCS Tickets API - Port 8000
- **Database**: `ocs_tickets`
- **Responsibility**: Ticket management (technology and maintenance tickets)
- **API Endpoints**:
  - `GET /api/tickets/tech` - List technology tickets
  - `POST /api/tickets/tech` - Create technology ticket
  - `GET /api/tickets/tech/{id}` - Get specific ticket
  - `PUT /api/tickets/tech/{id}` - Update ticket
  - `GET /api/tickets/tech/{id}/updates` - Get ticket updates

### 3. OCS Inventory API - Port 8001
- **Database**: `ocs_inventory`
- **Responsibility**: Asset and inventory management
- **Communication**: Isolated service for equipment tracking

### 4. OCS Requisition API - Port 8002
- **Database**: `ocs_requisition`
- **Responsibility**: Purchase requests and requisition management
- **Communication**: Isolated service for procurement workflows

### 5. OCS Management API - Port 8004
- **Database**: `ocs_manage`
- **Responsibility**: Administrative functions and system management
- **Communication**: Administrative oversight and reporting

## Database Architecture

```yaml
PostgreSQL Server:
  - ocs_portal      # Portal-specific data (users, buildings, system messages)
  - ocs_tickets     # All ticket data and related entities
  - ocs_inventory   # Asset and inventory data
  - ocs_requisition # Purchase and requisition data
  - ocs_manage      # Management and administrative data
```

## Communication Patterns

### ✅ CORRECT: API-Based Communication
```python
# Portal communicating with Tickets API
tickets = await tickets_service.get_tech_tickets("open")
result = await tickets_service.create_tech_ticket(ticket_data)
```

### ❌ INCORRECT: Direct Database Access
```python
# This violates microservices principles
tickets = db.query(Ticket).filter(Ticket.status == "open").all()
```

## Service Layer Implementation

### Portal Services Layer (`ocs-portal-py/services.py`)
```python
class TicketsService:
    async def get_tech_tickets(self, status_filter=None):
        # Makes HTTP call to Tickets API
        
    async def create_tech_ticket(self, ticket_data):
        # Makes HTTP call to Tickets API
        
    async def get_tech_ticket(self, ticket_id):
        # Makes HTTP call to Tickets API
```

## Docker Compose Configuration
Each service runs in its own container with environment variables pointing to its dedicated database:

```yaml
services:
  ocs-portal-py:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ocs_portal
      
  ocs-tickets-api:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ocs_tickets
      
  ocs-manage-api:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ocs_manage
```

## Shared Models Package
The `ocs_shared_models` package provides:
- **Common Entity Definitions**: Shared SQLAlchemy models
- **Timezone Utilities**: Consistent datetime handling
- **Data Validation**: Shared validation logic

**Important**: Shared models are for structure definition only. Each service still maintains its own database instance of these models.

## Architecture Compliance Status

### ✅ COMPLIANT AREAS
1. **Database Separation**: Each service has dedicated database
2. **Portal Implementation**: Uses service layer for API communication
3. **Service Isolation**: No cross-database queries
4. **Container Architecture**: Proper Docker separation

### 📋 MONITORING POINTS
1. **Future Development**: Ensure new features follow API-first approach
2. **Service Health**: Monitor inter-service communication
3. **Database Growth**: Watch for any attempts at cross-database queries

## Development Guidelines

### Adding New Features
1. ✅ **Identify Service Boundary**: Determine which service owns the feature
2. ✅ **API Design**: Design API endpoints before implementation
3. ✅ **Service Layer**: Create service layer methods in consuming services
4. ✅ **No Direct DB**: Never access another service's database directly

### Testing Inter-Service Communication
```python
# Test service layer methods
async def test_tickets_service():
    tickets = await tickets_service.get_tech_tickets()
    assert isinstance(tickets, list)
```

### Error Handling
- Services should gracefully handle API failures
- Implement proper timeout and retry logic
- Provide fallback responses when services are unavailable

## Conclusion
The OCS microservices architecture is **PROPERLY IMPLEMENTED** and follows best practices for:
- Service separation
- Database isolation  
- API-based communication
- Container orchestration

Continue following these patterns for future development to maintain architectural integrity.
