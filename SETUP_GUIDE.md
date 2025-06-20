# OCS Tracker Setup Guide

## Overview

This guide covers the complete setup process for the OCS Tracker microservices architecture, including database initialization, service deployment, and troubleshooting.

## Architecture

The OCS Tracker uses a **modular monorepo structure** with:
- **Single PostgreSQL Container**: All services connect to the same PostgreSQL server
- **Multiple Databases**: Each service has its own database for data isolation
- **Shared Models**: Common SQLAlchemy models via the `ocs_shared_models` package
- **Docker Compose**: Service orchestration and dependency management

### Services and Databases

| Service | Port | Database | Purpose |
|---------|------|----------|---------|
| `ocs-tickets-api` | 8000 | `ocs_tickets` | Ticket management system |
| `ocs-purchasing-api` | 8002 | `ocs_purchasing` | Purchasing and procurement |
| `ocs-portal-py` | 8003 | `ocs_portal` | Admin portal interface |
| `ocs-manage-api` | 8004 | `ocs_manage` | Management tasks and inventory |
| `ocs-forms-api` | 8005 | `ocs_forms` | Forms and tracking |

### Database Server

- **PostgreSQL**: Version 15
- **External Port**: 5433 (to avoid conflicts with local installations)
- **Internal Port**: 5432
- **User**: `ocs_user`
- **Password**: `ocs_pass`

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- PowerShell (Windows) or Bash (Linux/macOS)
- Git (for cloning the repository)

### Fresh Installation

For new installations or when you want to ensure clean setup:

```powershell
# Navigate to project directory
cd path\to\Tracker

# Run the automated setup script
.\setup-fresh.ps1
```

This script will:
1. ✅ Build all service containers
2. ✅ Start PostgreSQL with health checks
3. ✅ Create all required databases automatically
4. ✅ Verify database connectivity
5. ✅ Start all application services
6. ✅ Display service status and URLs

### Advanced Setup Options

```powershell
# Clean setup (removes existing containers and volumes)
.\setup-fresh.ps1 -Clean

# Skip container rebuild (faster for code-only changes)
.\setup-fresh.ps1 -SkipBuild
```

### Manual Setup

If you prefer manual control:

```powershell
# Standard Docker Compose startup
docker compose up --build

# Background execution
docker compose up -d --build
```

## Database Management

### Automatic Database Creation

Databases are created automatically through two mechanisms:

1. **Docker Init Script**: `init-db.sh` runs during PostgreSQL container initialization
2. **PowerShell Verification**: `setup-fresh.ps1` verifies and creates missing databases

### Manual Database Operations

#### Connect to Database Server

```powershell
# Connect to PostgreSQL container
docker exec -it tracker-db-1 psql -U ocs_user -d postgres
```

#### Create Databases Manually

```sql
-- Create all required databases
CREATE DATABASE ocs_tickets;
CREATE DATABASE ocs_inventory;
CREATE DATABASE ocs_purchasing;
CREATE DATABASE ocs_portal;
CREATE DATABASE ocs_manage;
CREATE DATABASE ocs_forms;

-- Grant permissions to ocs_user
GRANT ALL PRIVILEGES ON DATABASE ocs_tickets TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_inventory TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_purchasing TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_portal TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_manage TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_forms TO ocs_user;
```

#### List Existing Databases

```powershell
# List all databases
docker exec tracker-db-1 psql -U ocs_user -d postgres -c "\l"

# Test database connectivity
docker exec tracker-db-1 psql -U ocs_user -d ocs_tickets -c "SELECT 1;"
```

### Database Reset

⚠️ **Warning**: This will delete all data!

```powershell
# Stop all services
docker compose down

# Remove database volume
docker volume rm tracker_pgdata

# Fresh start with clean database
.\setup-fresh.ps1 -Clean
```

## Service Management

### Check Service Status

```powershell
# View running containers
docker ps

# Check service health
docker compose ps

# View container logs
docker logs tracker-ocs-tickets-api-1
```

### Individual Service Management

```powershell
# Restart specific service
docker compose restart ocs-tickets-api

# Rebuild and restart specific service
docker compose up -d --build ocs-tickets-api

# View service logs
docker compose logs -f ocs-tickets-api
```

### Access Service Endpoints

Once running, services are available at:

- **Portal**: http://localhost:8003
- **Tickets API Docs**: http://localhost:8000/docs
- **Inventory API Docs**: http://localhost:8001/docs
- **Purchasing API Docs**: http://localhost:8002/docs
- **Management API Docs**: http://localhost:8004/docs
- **Forms API Docs**: http://localhost:8005/docs

## Development Workflow

### Code Changes

For application code changes (no database schema changes):

```powershell
# Quick restart without full rebuild
.\setup-fresh.ps1 -SkipBuild
```

### Database Schema Changes

For changes to shared models or database schema:

```powershell
# Full rebuild to apply schema changes
.\setup-fresh.ps1
```

### Shared Models Development

The `ocs_shared_models` package is automatically installed in each service container. After modifying shared models:

```powershell
# Rebuild all services to pick up model changes
docker compose build
docker compose up -d
```

## Troubleshooting

### Common Issues

#### 1. Port Conflicts

**Error**: "bind: address already in use"

**Solution**:
```powershell
# Check what's using the port
netstat -ano | findstr :8000

# Kill conflicting process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

#### 2. Database Connection Failures

**Error**: "could not connect to server"

**Solution**:
```powershell
# Check database container status
docker ps | findstr tracker-db-1

# Check database logs
docker logs tracker-db-1

# Restart database service
docker compose restart db
```

#### 3. Containers Exit Immediately

**Error**: Container starts then immediately stops

**Solution**:
```powershell
# Check container logs for errors
docker logs tracker-ocs-tickets-api-1

# Common fixes:
# 1. Rebuild containers
docker compose build --no-cache

# 2. Clean restart
.\setup-fresh.ps1 -Clean
```

#### 4. Health Check Failures

**Error**: Services show "unhealthy" status

**Solution**:
```powershell
# Wait for services to fully start (can take 30-60 seconds)
docker compose ps

# If still failing, check logs
docker compose logs
```

### Debug Commands

```powershell
# View all container status
docker ps -a

# Check Docker Compose services
docker compose ps

# View system resources
docker system df

# Clean up unused resources
docker system prune -f

# View detailed container information
docker inspect tracker-db-1
```

### Log Analysis

```powershell
# Follow logs from all services
docker compose logs -f

# Follow logs from specific service
docker compose logs -f ocs-tickets-api

# View last 50 lines of logs
docker compose logs --tail 50 ocs-portal-py

# Search logs for errors
docker compose logs | findstr ERROR
```

## Performance Optimization

### Container Resource Limits

Add resource limits to `docker-compose.yml` if needed:

```yaml
services:
  ocs-tickets-api:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### Database Performance

```sql
-- Monitor database connections
SELECT * FROM pg_stat_activity;

-- View database sizes
SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database;
```

## Security Considerations

### Production Deployment

For production environments:

1. **Change default passwords** in `docker-compose.yml`
2. **Use environment files** for sensitive configuration
3. **Enable SSL/TLS** for database connections
4. **Implement proper firewall rules**
5. **Regular security updates** for base images

### Environment Variables

Create `.env` file for production:

```env
POSTGRES_USER=your_secure_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=ocs_tickets
```

## Backup and Recovery

### Database Backup

```powershell
# Backup all databases
docker exec tracker-db-1 pg_dumpall -U ocs_user > backup_all.sql

# Backup specific database
docker exec tracker-db-1 pg_dump -U ocs_user ocs_tickets > backup_tickets.sql
```

### Database Restore

```powershell
# Restore all databases
docker exec -i tracker-db-1 psql -U ocs_user < backup_all.sql

# Restore specific database
docker exec -i tracker-db-1 psql -U ocs_user -d ocs_tickets < backup_tickets.sql
```

## Support

### Getting Help

1. Check this guide first
2. Review container logs: `docker compose logs`
3. Verify service health: `docker compose ps`
4. Check network connectivity: `docker network ls`

### Reporting Issues

When reporting issues, include:
- Output of `docker compose ps`
- Relevant log snippets from `docker compose logs`
- Steps to reproduce the problem
- Your operating system and Docker version

---

## Quick Reference

### Essential Commands

```powershell
# Fresh setup
.\setup-fresh.ps1

# Clean reset
.\setup-fresh.ps1 -Clean

# View status
docker compose ps

# View logs
docker compose logs -f

# Stop everything
docker compose down

# Remove volumes (deletes data)
docker compose down -v
```

### Service URLs

- Portal: http://localhost:8003
- APIs: http://localhost:800[0-5]/docs
- PostgreSQL: localhost:5433

---

**Last Updated**: June 2025  
**Version**: 1.0  
**Maintainer**: OCS Development Team
