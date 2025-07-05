from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

class AuthService:
    def __init__(self):
        self.supabase_jwt_secret = os.environ['SUPABASE_JWT_SECRET']
        self.supabase_url = os.environ['SUPABASE_URL']
        self.supabase_key = os.environ['SUPABASE_KEY']
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify Supabase JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            return payload
        except JWTError:
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from JWT token"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None

auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[str]:
    """Get current authenticated user ID"""
    if not token:
        return None
    
    user_id = auth_service.get_user_id_from_token(token)
    return user_id

def require_auth(token: str = Depends(oauth2_scheme)) -> str:
    """Require authentication - raises exception if not authenticated"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = auth_service.get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id