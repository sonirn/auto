"""Authentication service for Vercel serverless functions"""
import os
import jwt
import httpx
import json
import logging
from typing import Optional, Dict, Any
from .database import UserOperations

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service using Supabase"""
    
    def __init__(self):
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_KEY')
        self.jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    
    def get_current_user(self, auth_header: Optional[str] = None) -> Optional[str]:
        """Get current user ID from JWT token"""
        if not auth_header:
            # Fallback for development
            return "default_user"
        
        try:
            # Extract token from Authorization header
            if not auth_header.startswith('Bearer '):
                return None
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Verify JWT token
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=['HS256'],
                options={"verify_signature": True}
            )
            
            return payload.get('sub')  # Subject is user ID
            
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    async def register_user(self, email: str, password: str) -> Dict[str, Any]:
        """Register a new user with Supabase"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/signup",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Registration failed: {response.text}")
                
                data = response.json()
                user_data = data.get('user', {})
                
                # Create user record in our database
                UserOperations.create_user(email, user_data.get('id'))
                
                return {
                    "message": "User registered successfully",
                    "user": {
                        "id": user_data.get('id'),
                        "email": email
                    },
                    "access_token": data.get('access_token')
                }
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise e
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with Supabase"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/token?grant_type=password",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Login failed: {response.text}")
                
                data = response.json()
                user_data = data.get('user', {})
                
                # Update last login in our database
                UserOperations.update_last_login(user_data.get('id'))
                
                return {
                    "message": "Login successful",
                    "user": {
                        "id": user_data.get('id'),
                        "email": user_data.get('email')
                    },
                    "access_token": data.get('access_token')
                }
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise e

# Create global auth service instance
auth_service = AuthService()