# 🚀 OCS Microservices - Quick Reference

## Service Communication Patterns

### ✅ CORRECT: API-Based Communication
```python
# Portal to Tickets API
from services import tickets_service
tickets = await tickets_service.get_tech_tickets("open")
result = await tickets_service.create_tech_ticket(data)

# Portal to Management API  
from management_service import management_service
users = await management_service.get_users()
```

### ❌ NEVER DO: Direct Database Access
```python
# Don't access other service databases directly
tickets = db.query(Ticket).all()  # ❌ VIOLATION
```

## Service Endpoints Reference

| Service | Port | Database | Responsibility |
|---------|------|----------|----------------|
| Portal | 8003 | ocs_portal | UI & Orchestration |
| Tickets | 8000 | ocs_tickets | Ticket Management |
| Inventory | 8001 | ocs_inventory | Asset Tracking |
| Requisition | 8002 | ocs_requisition | Purchase Requests |
| Management | 8004 | ocs_manage | Administration |

## Development Checklist

### Adding New Features
- [ ] Identify which service owns the feature
- [ ] Design API endpoints first
- [ ] Create service layer methods for communication
- [ ] Never access another service's database directly
- [ ] Test API communication paths

### Code Review Checklist
- [ ] No direct cross-service database queries
- [ ] Uses service layer for external API calls
- [ ] Proper error handling for service failures
- [ ] Follows established patterns

## Quick Commands

```powershell
# Start all services
docker-compose up -d

# Check architecture compliance
python verify_architecture_compliance.py

# View service logs
docker-compose logs [service-name]
```

## Documentation Links
- **Full Architecture**: `MICROSERVICES_ARCHITECTURE.md`
- **Cleanup Report**: `ARCHITECTURE_CLEANUP_FINAL_STATUS.md`
- **Compliance Checker**: `verify_architecture_compliance.py`

---
*Keep this reference handy for consistent microservices development! 🎯*
