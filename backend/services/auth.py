import logging
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify
import jwt
from config import Config
from services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def sign_up(self, email: str, password: str, 
                full_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            email: User email
            password: User password
            full_name: User's full name (optional)
            
        Returns:
            Dictionary containing user data and session
        """
        try:
            data = {
                'email': email,
                'password': password
            }
            
            if full_name:
                data['options'] = {
                    'data': {'full_name': full_name}
                }
            
            response = self.supabase.auth.sign_up(data)
            
            if response.user:
                logger.info(f"User signed up successfully: {email}")
                return {
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'full_name': response.user.user_metadata.get('full_name')
                    },
                    'session': {
                        'access_token': response.session.access_token if response.session else None,
                        'refresh_token': response.session.refresh_token if response.session else None
                    }
                }
            else:
                raise Exception("Sign up failed")
                
        except Exception as e:
            logger.error(f"Sign up error: {str(e)}")
            raise
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in an existing user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dictionary containing user data and session
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            logger.info(f"User signed in: {email}")
            
            return {
                'user': {
                    'id': response.user.id,
                    'email': response.user.email,
                    'full_name': response.user.user_metadata.get('full_name')
                },
                'session': {
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token,
                    'expires_at': response.session.expires_at
                }
            }
            
        except Exception as e:
            logger.error(f"Sign in error: {str(e)}")
            raise
    
    def sign_out(self, access_token: str) -> bool:
        """Sign out user"""
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            return False
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user info from JWT token
        
        Args:
            token: JWT access token
            
        Returns:
            User data or None
        """
        try:
            response = self.supabase.auth.get_user(token)
            
            if response.user:
                return {
                    'id': response.user.id,
                    'email': response.user.email,
                    'full_name': response.user.user_metadata.get('full_name')
                }
            return None
            
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            return None
    
    def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            return {
                'access_token': response.session.access_token,
                'refresh_token': response.session.refresh_token,
                'expires_at': response.session.expires_at
            }
            
        except Exception as e:
            logger.error(f"Refresh session error: {str(e)}")
            raise


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Get user from token
        auth_service = AuthService()
        user = auth_service.get_user_from_token(token)
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user to request context
        request.user = user
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """Decorator for optional authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            auth_service = AuthService()
            user = auth_service.get_user_from_token(token)
            request.user = user
        else:
            request.user = None
        
        return f(*args, **kwargs)
    
    return decorated_function
