"""
Authentication routes for Azure AD/Entra ID integration
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uuid
import logging

from database import get_db
from auth_service import AuthenticationService
from auth_config import AuthConfig
from auth_middleware import get_current_user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router for authentication routes
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# Templates
templates = Jinja2Templates(directory="templates")

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = None):
    """Display login page"""
    context = {"request": request}
    if next:
        context["next"] = next
    return templates.TemplateResponse("login.html", context)

@auth_router.get("/microsoft")
async def microsoft_login(request: Request, next: str = None, db: Session = Depends(get_db)):
    """Initiate Microsoft OAuth flow"""
    try:
        # Validate configuration
        AuthConfig.validate_config()
        
        # Create authentication service
        auth_service = AuthenticationService(db)
        
        # Generate state parameter for security
        state = str(uuid.uuid4())
        
        # Store state and next URL in session for callback
        request.session["oauth_state"] = state
        if next:
            request.session["next_url"] = next
            logger.info(f"Storing next URL in session: {next}")
        
        # Get authorization URL
        auth_url = auth_service.get_auth_url(state=state)
        
        logger.info(f"Redirecting to Microsoft login: {auth_url}")
        
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
        
    except Exception as e:
        logger.error(f"Error initiating Microsoft login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate login: {str(e)}"
        )

@auth_router.get("/callback")
async def auth_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Microsoft"""
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"OAuth error: {error} - {error_description}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication failed: {error_description or error}"
            )
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code not received"
            )
        
        # Verify state parameter (if using sessions)
        # stored_state = request.session.get("oauth_state")
        # if state != stored_state:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Invalid state parameter"
        #     )
          # Create authentication service
        auth_service = AuthenticationService(db)
        
        logger.info(f"Processing auth callback with code: {code[:20]}...")
        
        # Exchange authorization code for tokens
        token_result = auth_service.handle_auth_callback(code, state)
        
        if "access_token" not in token_result:
            logger.error(f"Token acquisition failed: {token_result}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token"
            )
          # Get user information from Microsoft Graph
        access_token = token_result["access_token"]
        logger.info("Getting user info from Microsoft Graph...")
        user_info = auth_service.get_user_info(access_token)
        
        user_data = user_info['user']
        groups_data = user_info['groups']
        
        logger.info(f"User authenticated: {user_data.get('userPrincipalName')} with {len(groups_data)} groups")
        
        # Determine user permissions
        permissions = auth_service.determine_user_permissions(user_data, groups_data)
        
        logger.info(f"User permissions determined: {permissions['access_level']} level")
          # Get client IP
        client_ip = request.client.host
        
        # Create user session
        session_token = auth_service.create_user_session(user_data, permissions, client_ip)
        
        logger.info(f"User {user_data.get('userPrincipalName')} logged in successfully")
        
        # Debug: Log session contents
        logger.info(f"Session contents: {dict(request.session)}")
        
        # Get the next URL from session (where user originally wanted to go)
        next_url = request.session.get("next_url", "/")
        logger.info(f"Retrieved next_url from session: {next_url}")
        logger.info(f"Redirecting user to: {next_url}")
        
        # Clear the next URL from session
        if "next_url" in request.session:
            logger.info(f"Clearing next_url from session")
            del request.session["next_url"]
        else:
            logger.info(f"No next_url found in session to clear")
        
        # Set session cookie and redirect to original destination
        response = RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=AuthConfig.SECURE_COOKIES,  # Configurable based on environment
            samesite="lax",
            max_age=AuthConfig.JWT_EXPIRATION_HOURS * 3600
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in auth callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"        )

@auth_router.get("/logout")
@auth_router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """Logout user and invalidate session"""
    try:
        session_token = request.cookies.get("session_token")
        
        if session_token:
            auth_service = AuthenticationService(db)
            client_ip = request.client.host
            auth_service.logout_user(session_token, client_ip)
        
        # Create response and delete cookie
        response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie("session_token")
        
        return response
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        # Still redirect to login even if logout fails
        response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie("session_token")
        return response

@auth_router.get("/user")
async def get_user_info(request: Request):
    """Get current user information"""
    user = get_current_user(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Return user info without sensitive data
    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "access_level": user.get("access_level"),
        "permissions": user.get("permissions", {})
    }

@auth_router.get("/status")
async def auth_status(request: Request):
    """Check authentication status"""
    user = get_current_user(request)
    
    return {
        "authenticated": user is not None,
        "user": {
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "access_level": user.get("access_level")
        } if user else None
    }
