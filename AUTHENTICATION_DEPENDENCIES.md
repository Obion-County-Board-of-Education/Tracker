# Authentication System Dependencies

This document outlines the dependencies required for the OCS Tracker authentication system and provides solutions for common import issues.

## Required Packages

The authentication system relies on the following Python packages:

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pyjwt` | >=2.8.0 | JWT token generation and validation |
| `cryptography` | >=41.0.3 | Cryptographic functions for JWT |
| `fastapi` | >=0.103.1 | Web framework and middleware support |
| `httpx` | >=0.25.0 | HTTP client for Azure AD integration |
| `sqlalchemy` | >=2.0.20 | Database ORM for session storage |
| `psycopg2-binary` | >=2.9.7 | PostgreSQL driver |
| `python-dotenv` | >=1.0.0 | Environment variable management |
| `pytz` | >=2.23.3 | Timezone handling for token expiration |

### Azure AD Integration

| Package | Version | Purpose |
|---------|---------|---------|
| `msal` | >=1.24.1 | Microsoft Authentication Library (optional) |

## Installation

To install all required dependencies, run the following PowerShell script:

```powershell
.\install_dependencies.ps1
```

This script will install the shared models package in development mode and all service-specific dependencies.

## Common Import Issues and Solutions

### ModuleNotFoundError: No module named 'jwt'

**Problem:** The authentication system imports `jwt`, but you may see an error saying the module cannot be found.

**Solution:** Install the PyJWT package:

```
pip install pyjwt
```

### ImportError: cannot import name 'get_permission_level' from 'ocs_shared_models.auth'

**Problem:** This occurs when the shared models package is not properly installed or accessible.

**Solution:** Install the shared models package in development mode:

```
pip install -e ./ocs_shared_models/
```

### ImportError: cannot import name 'HTTPBearer' from 'fastapi.security'

**Problem:** This error occurs if you have an older version of FastAPI installed.

**Solution:** Upgrade FastAPI to the latest version:

```
pip install --upgrade fastapi
```

### ModuleNotFoundError: No module named 'cryptography'

**Problem:** The PyJWT package uses cryptography for certain algorithms.

**Solution:** Install the cryptography package:

```
pip install cryptography
```

## Package Path Resolution

The authentication system uses relative imports from the `ocs_shared_models` package. To ensure proper resolution, the package must be either:

1. Installed as a package:
   ```
   pip install -e ./ocs_shared_models/
   ```

2. Added to the Python path in your code:
   ```python
   import sys
   import os
   sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
   ```

## Docker Environment

When running in Docker, ensure the Dockerfiles correctly install the shared models package before the service-specific requirements:

```dockerfile
# Copy shared models first
COPY ocs_shared_models/ ./ocs_shared_models/

# Install shared models as package
RUN pip install -e ./ocs_shared_models/

# Copy service requirements and install dependencies
COPY service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
```

## Environment Variables

The authentication system requires the following environment variables:

- `JWT_SECRET`: Secret key for JWT token signing (defaults to "development-secret-change-in-production")
- `SESSION_TIMEOUT_MINUTES`: Token validity duration in minutes (defaults to 30)
- `AZURE_CLIENT_ID`: Azure AD application client ID
- `AZURE_CLIENT_SECRET`: Azure AD application client secret
- `AZURE_TENANT_ID`: Azure AD tenant ID
- `AZURE_REDIRECT_URI`: Callback URL for Azure AD authentication
