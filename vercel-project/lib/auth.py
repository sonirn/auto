"""Authentication utilities for Vercel serverless functions"""
import os
import jwt
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service using Supabase"""
    
    def __init__(self):
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_KEY')
        self.jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
        
        if not all([self.supabase_url, self.supabase_key, self.jwt_secret]):
            logger.warning("Supabase credentials not configured, using fallback auth")
            self.fallback_mode = True
        else:
            self.fallback_mode = False
    
    def get_current_user(self, authorization_header: Optional[str] = None) -> Optional[str]:
        """Get current user from authorization header"""
        if self.fallback_mode:
            return "default_user"
        
        if not authorization_header:
            return None
        
        try:
            # Extract token from "Bearer <token>"
            token = authorization_header.replace("Bearer ", "")
            
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload.get("sub")  # Subject (user ID)
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
    
    def require_auth(self, authorization_header: Optional[str] = None) -> str:
        """Require authentication, return user ID or raise exception"""
        user_id = self.get_current_user(authorization_header)
        
        if not user_id:
            raise Exception("Authentication required")
        
        return user_id
    
    async def register_user(self, email: str, password: str) -> Dict[str, Any]:
        """Register new user"""
        if self.fallback_mode:
            return {
                "id": "default_user",
                "email": email,
                "message": "Using fallback authentication"
            }
        
        # Implement Supabase registration
        # This would use the Supabase client to create a new user
        raise NotImplementedError("Supabase registration not implemented")
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user"""
        if self.fallback_mode:
            return {
                "access_token": "fallback_token",
                "user": {
                    "id": "default_user",
                    "email": email
                }
            }
        
        # Implement Supabase login
        # This would use the Supabase client to authenticate the user
        raise NotImplementedError("Supabase login not implemented")

# Global auth service instance
auth_service = AuthService()