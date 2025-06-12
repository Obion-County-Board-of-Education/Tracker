# OCS Purchasing API

FastAPI service for managing requisitions and purchase orders within the OCS microservices architecture.

## Features

### Requisitions
- Create and manage purchase requisitions
- Approval workflow
- Status tracking (pending, approved, rejected, ordered)
- Priority levels (low, normal, high, urgent)
- Department filtering

### Purchase Orders
- Create purchase orders from approved requisitions
- Vendor management
- Status tracking (draft, sent, received, completed, cancelled)
- Delivery tracking

## API Endpoints

### Requisitions
- `GET /api/requisitions` - List all requisitions with filtering
- `POST /api/requisitions` - Create new requisition
- `GET /api/requisitions/{id}` - Get specific requisition
- `PUT /api/requisitions/{id}/approve` - Approve requisition

### Purchase Orders
- `GET /api/purchase-orders` - List all purchase orders with filtering
- `POST /api/purchase-orders` - Create new purchase order
- `GET /api/purchase-orders/{id}` - Get specific purchase order
- `PUT /api/purchase-orders/{id}/status` - Update PO status

### Health
- `GET /health` - Service health check

## Database

Uses dedicated PostgreSQL database `ocs_purchasing` with shared models from `ocs_shared_models` package.

## Development

```powershell
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8002
```

## Docker

Built and run via docker-compose.yml in the root project directory on port 8002.

## Architecture

Follows OCS microservices architecture:
- Database isolation (`ocs_purchasing`)
- API-based communication
- Shared models package
- Health monitoring integration
