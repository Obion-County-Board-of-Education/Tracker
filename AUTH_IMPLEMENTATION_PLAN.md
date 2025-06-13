# OCS Tracker Authentication Implementation Plan

## Phase 1: Core Authentication

### 1.1 Requirements Verification
- [x] Check requirements.txt for necessary authentication packages
- [x] Verify dependencies are properly installed
- [x] Confirm Azure AD application setup

### 1.2 Database Setup
- [ ] Create authentication tables with setup_auth_database.py
- [ ] Verify group_roles, user_sessions, and audit_log tables are created
- [ ] Insert initial role definitions for Azure AD groups

### 1.3 Azure AD Integration
- [ ] Implement Microsoft Graph API client in auth_service.py
- [ ] Create login endpoint to redirect to Azure AD
- [ ] Implement callback handler for Azure AD OAuth flow
- [ ] Implement token validation and user session creation

### 1.4 Session Management
- [ ] Set up JWT token generation with proper claims
- [ ] Create session storage in database
- [ ] Implement session validation middleware
- [ ] Add automatic token refresh handling
- [ ] Add session timeout and sliding expiration

## Phase 2: Authorization Framework

### 2.1 Group-Based Permissions
- [ ] Implement permission resolution from Azure AD groups
- [ ] Create cache for user permissions
- [ ] Create mapping between AD groups and application roles

### 2.2 Access Control
- [ ] Implement route-level permission checks
- [ ] Create permission decorators for FastAPI endpoints
- [ ] Add authorization middleware to all APIs
- [ ] Create data-level access control (department isolation)

### 2.3 Admin Interface
- [ ] Create admin interface for group role management
- [ ] Add group permission editor
- [ ] Implement user session management
- [ ] Add user permission override capability

## Phase 3: Security Hardening

### 3.1 Audit Logging
- [ ] Implement audit logging middleware
- [ ] Add logging for all security-related actions
- [ ] Create audit log viewer for admins
- [ ] Set up log retention policy

### 3.2 Security Features
- [ ] Implement rate limiting for login attempts
- [ ] Add CSRF protection
- [ ] Implement secure cookie handling
- [ ] Set up session invalidation across services
- [ ] Add concurrent session management

## Implementation Details

### Authentication Flow
1. User accesses OCS Tracker
2. System redirects to Microsoft login
3. User authenticates with Azure AD credentials
4. Azure AD redirects back with authorization code
5. System exchanges code for access token
6. System uses token to fetch user profile and group memberships
7. System creates local session and issues JWT
8. JWT is stored in HTTP-only cookie
9. User is redirected to original destination

### Authorization Process
1. Each request includes JWT token (in cookie or Authorization header)
2. Middleware validates token signature and expiration
3. User's Azure AD groups are mapped to application roles
4. System checks if user has permission for the requested resource
5. If authorized, request proceeds; otherwise, 403 Forbidden response
6. Action is logged in audit_log table

## Testing Strategy

### Authentication Testing
- Test valid login flow
- Test invalid credentials
- Test token expiration
- Test session timeout
- Test concurrent sessions

### Authorization Testing
- Test different permission levels
- Test access control across services
- Test department isolation
- Verify audit logging
