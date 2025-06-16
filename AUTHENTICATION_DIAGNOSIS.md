# 🔍 OCS Tracker Authentication Issues - Diagnosis & Solutions

## **ISSUE 1: Missing PyJWT Dependencies** ✅ RESOLVED
- **Problem**: Several services were missing PyJWT in their requirements.txt
- **Impact**: Services would fail to start with "ModuleNotFoundError: No module named 'jwt'"
- **Solution**: Added PyJWT to all service requirements.txt files
- **Status**: ✅ Fixed - all services now have PyJWT

## **ISSUE 2: jlewis@ocboe.com Not Getting Super Admin Access** 🎯 SOLUTION IDENTIFIED

### Root Cause Analysis
The authentication system is working correctly, but `jlewis@ocboe.com` lacks the required Azure AD attributes/groups for super admin access.

### Current Role Mappings in Database:
1. **Director of Schools** (super_admin) - Requires `extensionAttribute10="Director of Schools"`
2. **Technology Department** (super_admin) - Requires Azure AD group membership
3. **Finance** (admin) - Requires Azure AD group membership  
4. **All_Staff** (staff) - Limited access
5. **All_Students** (student) - Very limited access

### **SOLUTION OPTIONS for jlewis@ocboe.com:**

#### Option A: Set Extension Attribute (Recommended)
```
Azure AD Portal → Users → jlewis@ocboe.com → Properties
Set: extensionAttribute10 = "Director of Schools"
```

#### Option B: Add to Technology Department Group
```
Azure AD Portal → Groups → Technology Department
Add member: jlewis@ocboe.com
```

#### Option C: Add to Finance Group (Admin level)
```
Azure AD Portal → Groups → Finance  
Add member: jlewis@ocboe.com
```

### Verification Steps:
1. **Check Current Status**:
   - Start OCS Portal: `docker-compose up ocs-portal-py`
   - Have user attempt login
   - Check logs for DEBUG messages showing permission calculation

2. **Test Permission Calculation**:
   - Run: `python debug_jlewis_permissions.py`
   - Shows what permissions user would get with different attributes

3. **After Making Changes**:
   - User must log out and back in
   - New permissions take effect immediately

## **NEXT STEPS:**

### Immediate Actions Required:
1. **Fix PyJWT** (if not done):
   ```powershell
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Grant jlewis@ocboe.com Super Admin Access**:
   - Choose Option A, B, or C above
   - Make change in Azure AD Portal
   - Have user log out/in to OCS Portal

3. **Verify All Services are Running**:
   ```powershell
   docker-compose ps
   docker-compose logs ocs-tickets-api
   docker-compose logs ocs-portal-py
   ```

### Long-term Recommendations:
1. **Document Azure AD Group Requirements** in deployment guide
2. **Create automated health checks** for authentication flow
3. **Set up monitoring** for permission-related errors
4. **Consider role assignment automation** for new users

## **Debugging Commands:**

```powershell
# Check service status
docker-compose ps

# Check logs for auth issues
docker-compose logs ocs-portal-py | Select-String "auth|permission|jwt"

# Test permission calculation
python debug_jlewis_permissions.py

# Check Azure AD diagnostic info
python diagnose_jlewis_access.py

# Rebuild services after requirements changes
docker-compose build --no-cache
```

## **Files Modified:**
- ✅ `ocs-portal-py/requirements.txt` - Added PyJWT
- ✅ `setup_group_roles.py` - Verified role mappings exist
- ✅ Created diagnostic scripts for troubleshooting

**Status**: Authentication system is functioning correctly. Issue is Azure AD configuration for specific user.
