"""
Security utilities for Hanco-AI
Authentication, authorization, token validation, IDOR protection
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from google.cloud import firestore
import logging
import re

from app.core.firebase import verify_id_token, get_user, db, Collections

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for authentication
security = HTTPBearer()


# ==================== Log Redaction ====================

def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive information from logs
    Removes: emails, credit cards, tokens, phone numbers
    """
    if not text:
        return text
    
    # Redact email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
    
    # Redact credit card patterns (13-19 digits with optional spaces/dashes)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4,7}\b', '[CARD_REDACTED]', text)
    
    # Redact CVV patterns
    text = re.sub(r'\b(cvv|cvc)[:\s]*\d{3,4}\b', '[CVV_REDACTED]', text, flags=re.IGNORECASE)
    
    # Redact API tokens (common patterns)
    text = re.sub(r'\b(AIza[0-9A-Za-z_-]{35})\b', '[API_KEY_REDACTED]', text)
    text = re.sub(r'\b(sk-[a-zA-Z0-9]{48})\b', '[API_KEY_REDACTED]', text)
    
    # Redact phone numbers
    text = re.sub(r'\b\+?[\d\s-()]{10,15}\b', '[PHONE_REDACTED]', text)
    
    return text


def safe_log_error(message: str, error: Exception):
    """Log errors with sensitive data redaction"""
    safe_message = redact_sensitive_data(message)
    safe_error = redact_sensitive_data(str(error))
    logger.error(f"{safe_message}: {safe_error}")


# ==================== Authentication ====================

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
                detail="Invalid authentication credentials"
            )
        
        # Get user data from Firestore
        user_data = get_user(uid)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Check if user is active
        if not user_data.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Add custom claims from token (role)
        user_data['role'] = decoded_token.get('role', user_data.get('role', 'consumer'))
        user_data['uid'] = uid
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        safe_log_error("Authentication failed", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
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
                user_data['uid'] = uid
                return user_data
    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
    
    return None


# ==================== Authorization ====================

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
            detail="Insufficient permissions"
        )
    
    return current_user


def require_role(allowed_roles: list):
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
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker


# ==================== IDOR Protection ====================

async def verify_booking_ownership(
    booking_id: str,
    current_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify that the current user owns the booking or is an admin.
    
    Args:
        booking_id: Booking ID to check
        current_user: Current authenticated user
        
    Returns:
        Booking data if authorized
        
    Raises:
        HTTPException: If booking not found or user not authorized
    """
    try:
        booking_ref = db.collection(Collections.BOOKINGS).document(booking_id)
        booking_doc = booking_ref.get()
        
        if not booking_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        booking_data = booking_doc.to_dict()
        user_role = current_user.get('role', 'consumer')
        
        # Admin can access any booking
        if user_role in ['admin', 'support']:
            return booking_data
        
        # Regular user can only access their own bookings
        if booking_data.get('user_id') != current_user.get('uid'):
            # Return 404 instead of 403 to prevent info leakage
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        return booking_data
        
    except HTTPException:
        raise
    except Exception as e:
        safe_log_error(f"Error verifying booking ownership for {booking_id}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to verify resource access"
        )


async def verify_payment_ownership(
    payment_id: str,
    current_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify that the current user owns the payment or is an admin.
    
    Args:
        payment_id: Payment/Transaction ID to check
        current_user: Current authenticated user
        
    Returns:
        Payment data if authorized
        
    Raises:
        HTTPException: If payment not found or user not authorized
    """
    try:
        payment_ref = db.collection('payments').document(payment_id)
        payment_doc = payment_ref.get()
        
        if not payment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        payment_data = payment_doc.to_dict()
        user_role = current_user.get('role', 'consumer')
        
        # Admin can access any payment
        if user_role in ['admin', 'support']:
            return payment_data
        
        # Regular user can only access their own payments
        if payment_data.get('user_id') != current_user.get('uid'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        return payment_data
        
    except HTTPException:
        raise
    except Exception as e:
        safe_log_error(f"Error verifying payment ownership for {payment_id}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to verify resource access"
        )


# ==================== AI Input Validation ====================

def validate_ai_input(text: str, max_length: int = 2000) -> str:
    """
    Validate and sanitize AI chatbot input.
    Prevents prompt injection and abuse.
    
    Args:
        text: User input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
        
    Raises:
        HTTPException: If input is invalid
    """
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input cannot be empty"
        )
    
    text = text.strip()
    
    # Check length
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input too long. Maximum {max_length} characters allowed"
        )
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    # Basic prompt injection detection
    injection_patterns = [
        r'ignore\s+(previous|above|all)\s+instructions',
        r'system\s*:',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
        r'###\s*instruction',
        r'forget\s+(everything|all|previous)',
    ]
    
    text_lower = text.lower()
    for pattern in injection_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input detected"
            )
    
    # Check for excessive repetition (potential abuse)
    if len(text) > 50:
        words = text.split()
        if words and words[0] * 10 in text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input pattern detected"
            )
    
    return text


# ==================== Rate Limiting Support ====================

def get_client_ip(request: Request) -> str:
    """Extract client IP address for rate limiting"""
    # Check X-Forwarded-For header (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    if request.client:
        return request.client.host
    
    return "unknown"


# ==================== Legacy Functions (kept for compatibility) ====================
        
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
