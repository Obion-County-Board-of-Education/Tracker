"""
Test the authentication service configuration
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ocs_shared_models'))

from dotenv import load_dotenv
load_dotenv()

from auth_config import AuthConfig
from auth_service import AuthenticationService
from database import get_db

def test_auth_service():
    """Test basic authentication service functionality"""
    
    print("🔧 Testing Authentication Configuration...")
    
    try:
        # Test configuration
        AuthConfig.validate_config()
        print(f"✅ Azure Client ID: {AuthConfig.AZURE_CLIENT_ID[:8]}...")
        print(f"✅ Azure Tenant ID: {AuthConfig.AZURE_TENANT_ID[:8]}...")
        print(f"✅ Redirect URI: {AuthConfig.AZURE_REDIRECT_URI}")
        
        # Test auth service initialization
        db = next(get_db())
        auth_service = AuthenticationService(db)
        print("✅ Authentication service initialized")
        
        # Test auth URL generation
        auth_url = auth_service.get_auth_url("test-state")
        print(f"✅ Auth URL generated: {auth_url[:80]}...")
        
        # Test permission determination with mock data
        mock_user_data = {
            'id': 'test-user-id',
            'mail': 'test@ocs.edu',
            'userPrincipalName': 'test@ocs.edu',
            'displayName': 'Test User',
            'extensionAttribute10': None
        }
        
        mock_groups_data = [
            {'id': 'group-1', 'displayName': 'All_Staff'}
        ]
        
        permissions = auth_service.determine_user_permissions(mock_user_data, mock_groups_data)
        print("✅ Permission determination test passed")
        print(f"   Access Level: {permissions['access_level']}")
        print(f"   Tickets Access: {permissions['tickets_access']}")
        print(f"   Matched Groups: {permissions['matched_groups']}")
        
        db.close()
        
        print("\n🎉 All authentication tests passed!")
        print("\n📋 Next Steps:")
        print("1. Update your Azure AD app registration redirect URL to: http://localhost:8003/auth/callback")
        print("2. Add users to the appropriate Azure AD groups:")
        print("   - Technology Department (for IT staff)")
        print("   - Finance (for finance staff)")
        print("   - All_Staff (for general staff)")
        print("   - All_Students (for students)")
        print("3. Set extensionAttribute10='Director of Schools' for superintendents")
        print("4. Start the application and test login")
        
    except Exception as e:
        print(f"❌ Authentication test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auth_service()
