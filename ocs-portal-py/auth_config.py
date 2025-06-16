"""
Azure AD / Entra ID Authentication Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AuthConfig:
    # Azure AD Configuration
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET") 
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
    AZURE_REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI", "http://localhost:8003/auth/callback")
    AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
    
    # Scopes for Microsoft Graph API
    SCOPE = ["User.Read", "GroupMember.Read.All"]
    
    # JWT Configuration
    JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key_change_this_in_production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 8
      # Session Configuration
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))
    MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", 3))
    
    # Security Configuration
    SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"  # Set to true in production with HTTPS
    
    # Feature Flags
    ENABLE_AUDIT_LOGGING = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    ENABLE_MFA_REQUIRED = os.getenv("ENABLE_MFA_REQUIRED", "false").lower() == "true"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_password@localhost:5432/ocs_portal")
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        required_vars = [
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET", 
            "AZURE_TENANT_ID"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
        
        return True
