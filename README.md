<!-- filepath: c:\Users\JordanHowell\OneDrive - Obion County Schools\Documents\Projects\OCS\README.md -->

<p align="center">
  <img src="ocs-portal-py/static/ocs-logo.png" alt="OCS Logo" width="120"/>
</p>

<h1 align="center">Tracker</h1>
<h3 align="center" style="color: #6a1b9a;">codenamed <b>Purple Hat</b></h3>

<p align="center">
  <b>Modular Python FastAPI + PostgreSQL backend for Obion County Schools</b>
</p>

##Test

---

## 🗂️ Project Structure

- <b>ocs-tickets-api/</b> – FastAPI service for ticket system
- <b>ocs-inventory-api/</b> – FastAPI service for inventory
- <b>ocs-forms-api/</b> – FastAPI service for forms (time tracking, fuel tracking)
- <b>ocs-manage/</b> – FastAPI service for management tasks
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

1. <b>Build and start all services:</b>
   ```powershell
   docker compose up --build
   ```
2. Each API will be available at its respective port (see <code>docker-compose.yml</code>).
3. Connect your frontend to these endpoints.

---

## 🛠️ Requirements
- Docker
- Python 3.10+
- (Recommended) VS Code with Python extension

---

## 📋 Current Task Allocation

- <b>ocs-tickets-api/</b> ............................................. jhowell-ocs
- <b>ocs-inventory-api/</b> ......................................... CrypticSYS
- <b>ocs-requisition-api/</b>
- <b>ocs-manage/</b>
- <b>ocs-portal-py/</b>
- <b>ocs-shared-models/</b>

---

For more details, see each service's README or the API docs at <code>/docs</code> when running.

---

<p align="center" style="color: #b71c1c;"><b>Internal Use Only</b> &mdash; This repository contains proprietary code and resources for Obion County Schools. Unauthorized use or distribution is prohibited.</p>
