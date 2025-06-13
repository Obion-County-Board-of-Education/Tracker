"""
Authentication routes for OCS Tracker portal.
Handles login, logout, and authentication callback.
"""

from fastapi import APIRouter, Request, Response, Depends, HTTPException, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
import os
import json
from datetime import datetime, timedelta
from typing import Optional

from ocs_shared_models.database import get_db
from ocs_shared_models.auth import generate_token, validate_token, get_permission_level, AuthError
from ocs_shared_models.audit import log_audit_event

router = APIRouter(tags=["Authentication"])

# Azure AD Configuration from environment variables
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID")
AZURE_REDIRECT_URI = os.environ.get("AZURE_REDIRECT_URI", "http://localhost:8000/auth/callback")

# Session configuration
SESSION_COOKIE_NAME = "ocs_session"
SESSION_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "30"))


@router.get("/auth/login")
async def login(
    request: Request, 
    redirect_url: str = "/"
):
    """
    Initiate authentication flow to Microsoft Azure AD
    
    Args:
        request: FastAPI request object
        redirect_url: URL to redirect after successful login
        
    Returns:
        Redirect to Azure AD login page
    """
    if not AZURE_CLIENT_ID or not AZURE_TENANT_ID:
        return JSONResponse(
            status_code=500,
            content={"detail": "Azure AD configuration missing. Check environment variables."}
        )
    
    # Build Azure AD authorization URL
    auth_url = (
        f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={AZURE_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={AZURE_REDIRECT_URI}"
        f"&response_mode=query"
        f"&scope=openid%20profile%20email%20offline_access%20User.Read"
        f"&state={redirect_url}"  # Store redirect URL in state parameter
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str,
    state: str = "/",
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle callback from Azure AD after user login
    
    Args:
        request: FastAPI request object
        code: Authorization code from Azure AD
        state: Original redirect URL from login request
        error: Error message if authentication failed
        db: Database session
        
    Returns:
        Redirect to original URL with session cookie set
    """
    if error:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Authentication error: {error}"}
        )
    
    if not code:
        return JSONResponse(
            status_code=400,
            content={"detail": "No authorization code provided"}
        )
    
    try:
        # Exchange authorization code for access token
        token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            "client_id": AZURE_CLIENT_ID,
            "client_secret": AZURE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": AZURE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_data = token_response.json()
            
            # Get user info from Microsoft Graph API
            user_response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={
                    "Authorization": f"Bearer {token_data['access_token']}",
                    "Content-Type": "application/json",
                }
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get user's group memberships
            groups_response = await client.get(
                "https://graph.microsoft.com/v1.0/me/memberOf",
                headers={
                    "Authorization": f"Bearer {token_data['access_token']}",
                    "Content-Type": "application/json",
                }
            )
            groups_response.raise_for_status()
            groups_data = groups_response.json()
            
            # Extract user attributes
            user_id = user_data.get("id")
            display_name = user_data.get("displayName")
            email = user_data.get("mail") or user_data.get("userPrincipalName")
            
            # Extract group info
            user_groups = []
            for group in groups_data.get("value", []):
                if group.get("@odata.type") == "#microsoft.graph.group":
                    user_groups.append(group.get("displayName"))
            
            # Get on-premises extension attributes if available
            extension_attribute_10 = None
            ext_attrs_response = await client.get(
                "https://graph.microsoft.com/v1.0/me?$select=onPremisesExtensionAttributes",
                headers={
                    "Authorization": f"Bearer {token_data['access_token']}",
                    "Content-Type": "application/json",
                }
            )
            
            if ext_attrs_response.status_code == 200:
                ext_data = ext_attrs_response.json()
                ext_attrs = ext_data.get("onPremisesExtensionAttributes", {})
                extension_attribute_10 = ext_attrs.get("extensionAttribute10")
            
            # Calculate user permissions
            permissions = get_permission_level(user_groups, extension_attribute_10)
            
            # Generate session token
            session_token = generate_token(
                user_id,
                email,
                display_name,
                user_groups,
                SESSION_TIMEOUT_MINUTES
            )
            
            # Store session in database
            expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            
            # Use parameterized query to prevent SQL injection
            db.execute(
                text("""
                INSERT INTO user_sessions 
                (token, user_id, email, display_name, access_level, azure_groups, effective_permissions, expires_at)
                VALUES (:token, :user_id, :email, :display_name, :access_level, :azure_groups, :permissions, :expires_at)
                ON CONFLICT (token) DO UPDATE SET 
                    expires_at = :expires_at,
                    last_activity = NOW()
                """),
                {
                    "token": session_token,
                    "user_id": user_id,
                    "email": email,
                    "display_name": display_name,
                    "access_level": "super_admin" if "Technology Department" in user_groups else "user",
                    "azure_groups": json.dumps(user_groups),
                    "permissions": json.dumps(permissions),
                    "expires_at": expires_at
                }
            )
            db.commit()
            
            # Log audit event for successful login
            log_audit_event(
                db,
                user_id,
                action="login",
                status="success",
                details=f"User logged in successfully. Groups: {json.dumps(user_groups)}"
            )
            
            # Create response with session cookie
            response = RedirectResponse(url=state, status_code=302)
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_token,
                httponly=True,
                max_age=SESSION_TIMEOUT_MINUTES * 60,
                secure=request.url.scheme == "https",
                samesite="lax"
            )
            
            # Log successful login
            log_audit_event(
                db=db,
                user_id=user_id,
                action_type="login",
                resource_type="session",
                resource_id=session_token,
                details={
                    "email": email,
                    "groups": user_groups,
                    "permissions": permissions
                },
                ip_address=request.client.host
            )
            
            return response
            
    except httpx.HTTPError as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error communicating with Microsoft: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Authentication error: {str(e)}"}
        )


@router.get("/auth/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    redirect_url: str = "/",
    ocs_session: Optional[str] = Cookie(None)
):
    """
    Log out the current user
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        db: Database session
        redirect_url: URL to redirect after logout
        ocs_session: Session cookie
        
    Returns:
        Redirect to login page
    """
    try:
        if ocs_session:
            # Get user ID before deleting session
            user_result = db.execute(
                text("SELECT user_id FROM user_sessions WHERE token = :token"),
                {"token": ocs_session}
            )
            user_row = user_result.fetchone()
            user_id = user_row.user_id if user_row else "unknown"
            
            # Delete session from database
            db.execute(
                text("DELETE FROM user_sessions WHERE token = :token"),
                {"token": ocs_session}
            )
            db.commit()
            
            # Log logout
            log_audit_event(
                db=db,
                user_id=user_id,
                action_type="logout",
                resource_type="session",
                resource_id=ocs_session,
                ip_address=request.client.host
            )
        
        # Clear session cookie
        response = RedirectResponse(url=redirect_url)
        response.delete_cookie(SESSION_COOKIE_NAME)
        
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Logout error: {str(e)}"}
        )


@router.get("/auth/user")
async def get_current_user_info(request: Request):
    """
    Get information about the currently logged in user
    
    Args:
        request: FastAPI request object
        
    Returns:
        User information JSON
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "roles": user.get("roles", []),
        "permissions": user.get("permissions", {})
    }


@router.get("/auth/status")
async def get_auth_status(
    request: Request,
    ocs_session: Optional[str] = Cookie(None)
):
    """
    Check the current authentication status
    
    Args:
        request: FastAPI request object
        ocs_session: Session cookie
        
    Returns:
        Authentication status JSON
    """
    if not ocs_session:
        return {"authenticated": False}
    
    try:
        payload = validate_token(ocs_session)
        return {
            "authenticated": True,
            "user": {
                "email": payload.get("email"),
                "name": payload.get("name")
            }
        }
    except AuthError:
        return {"authenticated": False}
