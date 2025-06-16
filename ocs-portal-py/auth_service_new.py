class AuthenticationService:
    def __init__(self, db):
        self.db = db
    
    def get_auth_url(self, state=None):
        return "https://login.microsoftonline.com/test"
    
    def handle_auth_callback(self, code, state=None):
        return {"access_token": "test_token", "user_info": {"id": "test_user"}}
    
    def create_session(self, user_id, permissions, ip_address=None):
        return "test_session_token"
    
    def validate_token(self, token):
        return {"user_id": "test_user", "permissions": {"access_level": "admin"}}
    
    def logout(self, token, ip_address=None):
        return True
