"""
Security utilities for Hanco-AI
Authentication, authorization, token validation
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from app.core.firebase import verify_id_token, get_user

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for authentication
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from Firebase ID token.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        User data dictionary including uid, email, role
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify Firebase ID token
        decoded_token = verify_id_token(token)
        uid = decoded_token.get('uid')
        
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: UID not found"
            )
        
        # Get user data from Firestore
        user_data = get_user(uid)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is active
        if not user_data.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Add custom claims from token
        user_data['role'] = decoded_token.get('role', user_data.get('role', 'consumer'))
        
        return user_data
        
    except ValueError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency.
    Returns user if authenticated, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        decoded_token = verify_id_token(token)
        uid = decoded_token.get('uid')
        
        if uid:
            user_data = get_user(uid)
            if user_data:
                user_data['role'] = decoded_token.get('role', user_data.get('role', 'consumer'))
                return user_data
    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
    
    return None


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency that requires user to have admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User data if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    user_role = current_user.get('role', 'consumer')
    
    if user_role not in ['admin', 'support']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def require_role(allowed_roles: list):
    """
    Factory function to create role-based dependency.
    
    Usage:
        @router.get("/", dependencies=[Depends(require_role(['admin', 'support']))])
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get('role', 'consumer')
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return role_checker


def verify_user_access(user_id: str, current_user: Dict[str, Any]) -> bool:
    """
    Check if current user can access resources belonging to user_id.
    User can access their own resources or admin can access any.
    
    Args:
        user_id: The user ID of the resource owner
        current_user: Current authenticated user
        
    Returns:
        True if access is allowed
        
    Raises:
        HTTPException: If access is denied
    """
    current_uid = current_user.get('uid')
    current_role = current_user.get('role', 'consumer')
    
    # User can access their own data
    if current_uid == user_id:
        return True
    
    # Admin can access any data
    if current_role in ['admin', 'support']:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )


class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self._requests = {}
    
    def check_rate_limit(self, key: str, max_requests: int = 60, window: int = 60) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Identifier (user_id, ip, etc.)
            max_requests: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            True if within limit, False otherwise
        """
        # TODO: Implement with Redis for production
        # This is a simple placeholder
        return True


rate_limiter = RateLimiter()
