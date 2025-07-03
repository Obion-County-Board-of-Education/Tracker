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

def log_session_details(request: Request, context: str):
    """Helper function to log session details for debugging"""
    session_id = request.session.get("_session_id", "NO_SESSION_ID")
    session_contents = dict(request.session)
    logger.info(f"[{context}] Session ID: {session_id}")
    logger.info(f"[{context}] Session contents: {session_contents}")
    
    # Log cookies for debugging
    cookies = dict(request.cookies)
    logger.info(f"[{context}] Request cookies: {cookies}")

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
        logger.info(f"Microsoft login initiated with next parameter: {next}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request query params: {request.query_params}")
        
        # Log initial session state
        log_session_details(request, "MICROSOFT_AUTH_START")
        
        # Validate configuration
        AuthConfig.validate_config()
        
        # Create authentication service
        auth_service = AuthenticationService(db)
        
        # Generate state parameter for security and store next URL
        state_data = {
            "nonce": str(uuid.uuid4()),
            "next_url": next or "/"
        }
        
        # Encode state data as base64 JSON for security
        import base64
        import json
        encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        
        # Store state in session for verification
        request.session["oauth_state"] = state_data["nonce"]
        if next:
            request.session["next_url"] = next
            logger.info(f"Storing next URL in session: {next}")
        else:
            logger.info(f"No next parameter provided, will default to /")
        
        # Log session state after storing values
        log_session_details(request, "MICROSOFT_AUTH_AFTER_STORING")
        
        # Get authorization URL with encoded state
        auth_url = auth_service.get_auth_url(state=encoded_state)
        
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
        # Log session state at start of callback
        log_session_details(request, "CALLBACK_START")
        
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
        
        # Verify state parameter for security
        if state:
            try:
                import base64
                import json
                decoded_state = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
                state_nonce = decoded_state.get("nonce")
                stored_state = request.session.get("oauth_state")
                
                if state_nonce != stored_state:
                    logger.warning(f"State mismatch: received {state_nonce}, expected {stored_state}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid state parameter"
                    )
                logger.info(f"State parameter verified successfully")
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode state parameter: {state}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid state parameter format"
                )
        else:
            logger.warning("No state parameter received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing state parameter"
            )
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
        
        # Get the next URL from state parameter first, then session as fallback
        next_url = "/"
        
        # Try to decode state parameter to get next_url
        if state:
            try:
                import base64
                import json
                decoded_state = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
                next_url = decoded_state.get("next_url", "/")
                logger.info(f"Retrieved next_url from state parameter: {next_url}")
            except Exception as e:
                logger.warning(f"Failed to decode state parameter: {e}")
                # Fall back to session
                next_url = request.session.get("next_url", "/")
                logger.info(f"Retrieved next_url from session (fallback): {next_url}")
        else:
            # Fall back to session
            next_url = request.session.get("next_url", "/")
            logger.info(f"Retrieved next_url from session (no state): {next_url}")
            
        logger.info(f"Final redirect destination: {next_url}")
        
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
        response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie("session_token")
        
        return response
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        # Still redirect to login even if logout fails
        response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
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
