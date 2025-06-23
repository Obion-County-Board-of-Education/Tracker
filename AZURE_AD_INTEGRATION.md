# Azure AD Integration Summary

## Overview
The OCS Tracker system leverages a single Azure AD (Entra ID) app registration for both user authentication and user import functionality. This unified approach simplifies configuration and ensures consistent permissions across the system.

## Azure AD Configuration

### App Registration Settings
- **Client ID**: Configured via `AZURE_CLIENT_ID` environment variable
- **Client Secret**: Configured via `AZURE_CLIENT_SECRET` environment variable  
- **Tenant ID**: Configured via `AZURE_TENANT_ID` environment variable
- **Redirect URI**: `http://localhost:8003/auth/callback` (configurable via `AZURE_REDIRECT_URI`)

### Required Permissions
The Azure AD app registration requires the following Microsoft Graph API permissions:

1. **User.Read** - Allows the app to read the signed-in user's profile
2. **User.Read.All** - Allows the app to read all users' profiles (for user import)
3. **Group.Read.All** - Allows the app to read all groups (for role determination and user import)
4. **GroupMember.Read.All** - Allows the app to read group memberships (for role determination and user import)

These permissions support both authentication flows and the user import functionality from Azure AD groups.

## Authentication Flow

### 1. User Login Process
```
User → Portal Login Page → Azure AD → User Consents → Azure AD Callback → Portal Dashboard
```

1. User clicks login on the portal
2. Portal redirects to Azure AD with authorization request
3. User authenticates with Azure AD (can be SSO if already logged in)
4. Azure AD redirects back to portal with authorization code
5. Portal exchanges code for access token
6. Portal uses access token to get user info and group memberships
7. Portal determines user permissions based on group memberships
8. Portal creates JWT session token and logs user in

### 2. Session Management
- JWT tokens expire after 8 hours (configurable)
- Sessions are tracked in the database with automatic cleanup
- Maximum of 3 concurrent sessions per user (configurable)
- All login/logout events are audited

### 3. Role Determination
User roles are determined by Azure AD group membership:
- **All_Students** group → `student` access level
- **All_Staff** group → `staff` access level  
- **OCS_Admin** group → `admin` access level
- **Super_Admins** group → `super_admin` access level

## User Import Flow

### 1. Import Process Overview
```
Admin → Import UI → Portal API → Azure AD Graph API → Database Update → Status Report
```

1. Admin accesses the user management interface (`/admin/users`)
2. Admin initiates import from Azure AD groups
3. Portal uses client credentials to get application token
4. Portal queries Azure AD Graph API for group members
5. Portal processes user data and creates/updates database records
6. Portal provides status report of import results

### 2. Import Implementation
The `UserImportService` class handles the import process:

```python
# Key methods:
- get_application_token()     # Gets app-only access token
- get_group_id_by_name()      # Finds Azure AD group by name
- get_group_members()         # Retrieves all members of a group
- process_user_data()         # Maps Azure AD data to database schema
- import_users_from_groups()  # Main import orchestration
```

### 3. Data Mapping
Azure AD user attributes are mapped to the OCS database schema:

| Azure AD Field | Database Field | Notes |
|----------------|----------------|-------|
| id | azure_id | Primary identifier |
| userPrincipalName | email | Login email |
| displayName | display_name | Full name |
| givenName | first_name | First name |
| surname | last_name | Last name |
| department | department_name | Department (via UserDepartment) |
| jobTitle | title | Job title |

### 4. Group Processing
The system imports users from two specific Azure AD groups:
- **All_Staff**: Maps to `staff` access level
- **All_Students**: Maps to `student` access level

## Technical Implementation

### 1. Authentication Service
Located in `ocs-portal-py/auth_service.py`:
- Handles user authentication flows
- Manages session creation and validation
- Provides application token for Graph API access
- Determines user permissions from group memberships

### 2. User Import Service  
Located in `ocs-portal-py/user_import_service.py`:
- Handles bulk user import from Azure AD
- Uses application credentials for Graph API access
- Processes user data and department assignments
- Provides detailed import status reporting

### 3. Configuration
Located in `ocs-portal-py/auth_config.py`:
- Centralizes all Azure AD configuration
- Defines required scopes and permissions
- Configures JWT and session settings

## Security Considerations

### 1. Token Management
- Application tokens are requested on-demand and not stored
- User session tokens are validated on each request
- Expired sessions are automatically cleaned up
- All authentication events are audited

### 2. Permission Scope
The application uses minimal required permissions:
- Read-only access to user profiles and groups
- No write permissions to Azure AD
- Application-level permissions only for user import

### 3. Access Control
- User import functionality is restricted to admin users only
- All import operations are logged and auditable
- Rate limiting is applied to prevent abuse

## Environment Variables

The following environment variables must be configured:

```bash
# Azure AD Configuration
AZURE_CLIENT_ID=your_app_client_id
AZURE_CLIENT_SECRET=your_app_client_secret  
AZURE_TENANT_ID=your_tenant_id
AZURE_REDIRECT_URI=http://localhost:8003/auth/callback

# Optional Configuration
JWT_SECRET=your_jwt_secret_key
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_SESSIONS=3
DATABASE_URL=postgresql://ocs_user:ocs_password@localhost:5432/ocs_portal
```

## Testing and Validation

### 1. Authentication Testing
- Login/logout flows are tested with real Azure AD accounts
- Session management is validated with concurrent login tests
- Role assignment is verified with different group memberships

### 2. Import Testing
- Mock data testing validates data mapping and processing logic
- Group membership resolution is tested with sample Azure AD data
- Error handling is validated with various failure scenarios

### 3. End-to-End Testing
The test suite (`test_user_import.py`) provides comprehensive validation:
- Data mapping accuracy
- Department creation and assignment
- Error handling and edge cases
- Status reporting functionality

## Deployment Considerations

### 1. Azure AD App Registration
Ensure the Azure AD app registration has:
- Correct redirect URIs configured
- Required API permissions granted and admin consented
- Client secret properly secured and rotated regularly

### 2. Production Environment
- Use HTTPS for all authentication redirects in production
- Configure secure cookie settings (`SECURE_COOKIES=true`)
- Set appropriate session timeouts for security
- Monitor authentication and import logs regularly

### 3. Scaling Considerations
- Import operations run asynchronously to prevent timeout issues
- Batch processing handles large group memberships efficiently
- Database connections are managed efficiently during bulk operations

## Support and Troubleshooting

### 1. Common Issues
- **Permission Denied**: Verify Azure AD app permissions are granted and consented
- **Token Expired**: Check client secret expiration and renewal
- **Group Not Found**: Verify group names match exactly in Azure AD
- **Import Timeout**: Check network connectivity and Azure AD service status

### 2. Monitoring
- All authentication events are logged to the audit system
- Import operations provide detailed status reports
- Health checks monitor service availability
- Error logs capture detailed failure information

### 3. Configuration Validation
Use the `AuthConfig.validate_config()` method to verify all required settings are present before startup.

## Conclusion

The unified Azure AD integration provides a robust foundation for both authentication and user management in the OCS Tracker system. By leveraging a single app registration with appropriate permissions, the system maintains security while providing seamless user experience and efficient administrative capabilities.
