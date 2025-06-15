# 🗄️ OCS Tracker Database Setup Guide

This guide resolves the common database initialization issues when setting up the OCS Tracker project from a fresh clone.

## 🚨 The Problem

When running `docker compose up --build` on a fresh clone, services often fail with errors like:
- `FATAL: database "ocs_purchasing" does not exist`
- `FATAL: database "ocs_forms" does not exist`
- Services start before all databases are created

## ✅ The Solution

We've implemented a comprehensive fix with:

1. **Automatic Database Creation**: `init-db.sh` script creates all required databases
2. **Health Checks**: Services wait for database to be fully ready
3. **Proper Dependencies**: Services use `condition: service_healthy`
4. **Setup Script**: `setup-fresh.ps1` automates the entire process

## 🚀 Quick Start (Recommended)

```powershell
# For a completely fresh setup (cleans everything)
.\setup-fresh.ps1 -Clean

# For regular startup
.\setup-fresh.ps1
```

## 🔧 Manual Setup

If you prefer manual control:

```powershell
# 1. Stop and clean everything
docker compose down -v

# 2. Start with proper initialization
docker compose up -d --build --force-recreate

# 3. Verify databases (wait 30 seconds for full initialization)
docker exec tracker-db-1 psql -U ocs_user -d postgres -c "\l"
```

## 🏗️ What Was Fixed

### 1. Database Initialization Script
- **File**: `init-db.sh`
- **Purpose**: Creates all 6 required databases automatically
- **Location**: Mounted to `/docker-entrypoint-initdb.d/` in PostgreSQL container

### 2. Health Checks
- **Database**: Checks if PostgreSQL is ready to accept connections
- **Services**: Each service checks if its specific database exists
- **Dependencies**: Services wait for `db` to be `service_healthy`

### 3. Updated Dockerfiles
- **PostgreSQL Client**: Added to all service containers for health checks
- **Health Check Script**: `healthcheck.sh` verifies database connectivity
- **Proper Permissions**: Scripts are made executable during build

### 4. Enhanced docker-compose.yml
- **Health Check Configuration**: Database has proper health check
- **Service Dependencies**: Uses `condition: service_healthy`
- **Environment Variables**: Added DB connection details for health checks

## 📋 Required Databases

The system creates these databases automatically:

| Database | Service | Purpose |
|----------|---------|---------|
| `ocs_tickets` | Tickets API | Ticket management |
| `ocs_inventory` | Inventory API | Asset tracking |
| `ocs_purchasing` | Purchasing API | Purchase requests |
| `ocs_portal` | Portal | UI and orchestration |
| `ocs_manage` | Management API | Administrative functions |
| `ocs_forms` | Forms API | Time/fuel tracking |

## 🔍 Verification

After setup, verify everything is working:

```powershell
# Check all containers are running
docker ps

# Check database connectivity
docker exec tracker-db-1 psql -U ocs_user -d ocs_tickets -c "\q"
docker exec tracker-db-1 psql -U ocs_user -d ocs_inventory -c "\q"
docker exec tracker-db-1 psql -U ocs_user -d ocs_purchasing -c "\q"
docker exec tracker-db-1 psql -U ocs_user -d ocs_portal -c "\q"
docker exec tracker-db-1 psql -U ocs_user -d ocs_manage -c "\q"
docker exec tracker-db-1 psql -U ocs_user -d ocs_forms -c "\q"

# Check service health
curl http://localhost:8000/docs  # Tickets API
curl http://localhost:8001/docs  # Inventory API
curl http://localhost:8002/docs  # Purchasing API
curl http://localhost:8003       # Portal
curl http://localhost:8004/docs  # Management API
curl http://localhost:8005/docs  # Forms API
```

## 🐛 Troubleshooting

### If databases are still missing:

```powershell
# Create missing databases manually
docker exec tracker-db-1 psql -U ocs_user -d postgres -c "CREATE DATABASE ocs_purchasing;"
docker exec tracker-db-1 psql -U ocs_user -d postgres -c "CREATE DATABASE ocs_forms;"
# ... repeat for any missing databases

# Grant permissions
docker exec tracker-db-1 psql -U ocs_user -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE ocs_purchasing TO ocs_user;"
```

### If services won't start:

```powershell
# Check service logs
docker logs tracker-ocs-tickets-api-1
docker logs tracker-ocs-inventory-api-1
# ... etc

# Restart specific service
docker compose restart ocs-tickets-api
```

### If PostgreSQL won't start:

```powershell
# Check PostgreSQL logs
docker logs tracker-db-1

# Remove volume and restart fresh
docker compose down -v
docker compose up -d --build
```

## 📝 Development Notes

- **First-time setup**: Always use `setup-fresh.ps1 -Clean` for completely clean environment
- **Regular development**: Use `setup-fresh.ps1` or `docker compose up -d`
- **Database changes**: If you modify database schemas, use `-Clean` flag to reset
- **Port conflicts**: Database runs on port 5433 (host) to avoid conflicts with local PostgreSQL

This setup ensures reliable database initialization for all team members and CI/CD environments.
