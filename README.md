<!-- filepath: c:\Users\JordanHowell\OneDrive - Obion County Schools\Documents\Projects\OCS\README.md -->

<p align="center">
  <img src="ocs-portal-py/static/ocs-logo.png" alt="OCS Logo" width="120"/>
</p>

<h1 align="center">Tracker</h1>
<h3 align="center" style="color: #6a1b9a;">codenamed <b>Purple Hat</b></h3>

<p align="center">
  <b>Modular Python FastAPI + PostgreSQL backend for Obion County Schools</b>
</p>

---

## 🗂️ Project Structure

- <b>ocs-tickets-api/</b> – FastAPI service for ticket system
- <b>ocs-forms-api/</b> – FastAPI service for forms (time tracking, fuel tracking)
- <b>ocs-manage/</b> – FastAPI service for management tasks and inventory
- <b>ocs-portal-py/</b> – FastAPI service for admin portal (Jinja2, static, templates)
- <b>ocs_shared_models/</b> – Shared SQLAlchemy models for all services
- <b>tests/</b> – Comprehensive test suite organized by component and type
- <b>docker-compose.yml</b> – Orchestration for all services and a single PostgreSQL container

---

## 🧪 Testing

All testing scripts are properly organized in the `tests/` folder:

- **Unit Tests**: `tests/unit/` - Component-level testing
- **Portal Tests**: `tests/portal/` - Portal-specific functionality tests  
- **API Tests**: `tests/api/` - API endpoint testing
- **Integration Tests**: `tests/integration/` - End-to-end testing
- **CSV Tests**: `tests/csv/` - CSV import/export functionality
- **Utilities**: `tests/utilities/` - Test utilities and verification scripts

### Running Tests

**PowerShell (Windows):**
```powershell
# Run all tests
.\Run-AllTests.ps1

# Run specific category
.\Run-AllTests.ps1 -Category Portal

# Show test organization
.\Run-AllTests.ps1 -ShowOrganization
```

**Python:**
```bash
# Run all tests  
python run_all_tests.py

# Run specific category
python run_all_tests.py portal

# Show test organization
python run_all_tests.py organization
```

---

## 🚀 Getting Started

### Quick Start (Recommended)

For a fresh installation or when you need to ensure all databases are properly initialized:

```powershell
# Fresh setup with automatic database initialization
.\setup-fresh.ps1

# Fresh setup with cleanup (removes existing containers and volumes)
.\setup-fresh.ps1 -Clean

# Fresh setup without rebuilding containers
.\setup-fresh.ps1 -SkipBuild
```

### Manual Setup

1. <b>Build and start all services:</b>
   ```powershell
   docker compose up --build
   ```
2. Each API will be available at its respective port (see <code>docker-compose.yml</code>).
3. Connect your frontend to these endpoints.

### Database Setup

The project uses a single PostgreSQL container with multiple databases for each service:

- **ocs_tickets** - Ticket management system
- **ocs_inventory** - Inventory tracking  
- **ocs_purchasing** - Purchasing and procurement
- **ocs_portal** - Admin portal data
- **ocs_manage** - Management tasks
- **ocs_forms** - Forms and tracking data

#### Automatic Database Initialization

Databases are automatically created using two methods:

1. **Docker Init Script**: `init-db.sh` runs during container initialization
2. **PowerShell Setup Script**: `setup-fresh.ps1` verifies and creates missing databases

#### Manual Database Creation

If you need to manually create databases:

```powershell
# Connect to the database container
docker exec -it tracker-db-1 psql -U ocs_user -d postgres

# Create databases manually
CREATE DATABASE ocs_tickets;
CREATE DATABASE ocs_inventory;
CREATE DATABASE ocs_purchasing;
CREATE DATABASE ocs_portal;
CREATE DATABASE ocs_manage;
CREATE DATABASE ocs_forms;

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE ocs_tickets TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_inventory TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_purchasing TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_portal TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_manage TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_forms TO ocs_user;
```

### Service Endpoints

Once running, services are available at:

- **Portal**: http://localhost:8003
- **Tickets API**: http://localhost:8000/docs
- **Inventory API**: http://localhost:8001/docs  
- **Purchasing API**: http://localhost:8002/docs
- **Management API**: http://localhost:8004/docs
- **Forms API**: http://localhost:8005/docs
- **PostgreSQL**: localhost:5433 (external port)

---

## 🛠️ Requirements
- Docker
- Python 3.10+
- (Recommended) VS Code with Python extension

---

## 🔧 Troubleshooting

### Database Connection Issues

If services can't connect to their databases:

1. **Check database container health:**
   ```powershell
   docker ps
   # Look for "healthy" status on tracker-db-1
   ```

2. **Verify databases exist:**
   ```powershell
   # List all databases
   docker exec tracker-db-1 psql -U ocs_user -d postgres -c "\l"
   ```

3. **Check database logs:**
   ```powershell
   docker logs tracker-db-1 --tail 20
   ```

4. **Re-run setup script:**
   ```powershell
   .\setup-fresh.ps1 -Clean
   ```

### Port Conflicts

If you get port binding errors:

- PostgreSQL runs on port 5433 (external) to avoid conflicts with local PostgreSQL installations
- API services run on ports 8000-8005
- Check for conflicting services: `netstat -an | findstr :8000`

### Container Build Issues

If containers fail to build:

1. **Clean Docker cache:**
   ```powershell
   docker system prune -f
   docker builder prune -f
   ```

2. **Force rebuild:**
   ```powershell
   docker compose build --no-cache
   ```

### Database Volume Issues

If you need to completely reset the database:

```powershell
# Stop all services
docker compose down

# Remove volumes (⚠️ This deletes all data!)
docker volume rm tracker_pgdata

# Fresh start
.\setup-fresh.ps1 -Clean
```

---

## 📋 Current Task Allocation

- <b>ocs-tickets-api/</b> ............................................. jhowell-ocs
- <b>ocs-manage/</b> (includes inventory) ........................... CrypticSYS
- <b>ocs-requisition-api/</b>
- <b>ocs-portal-py/</b>
- <b>ocs-shared-models/</b>

---

For more details, see each service's README or the API docs at <code>/docs</code> when running.

---

<p align="center" style="color: #b71c1c;"><b>Internal Use Only</b> &mdash; This repository contains proprietary code and resources for Obion County Schools. Unauthorized use or distribution is prohibited.</p>
