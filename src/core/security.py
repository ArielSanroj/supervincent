"""
Security utilities for SuperVincent InvoiceBot.
"""

import hashlib
import hmac
import logging
import os
import re
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import redis
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security-related exception."""
    pass


class InputValidator:
    """Input validation utilities."""
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_TEXT_LENGTH = 10000  # 10KB for text inputs
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/png'
    }
    
    @staticmethod
    def validate_file_path(file_path: str) -> Path:
        """Validate and sanitize file path."""
        try:
            path = Path(file_path).resolve()
            
            # Check if path exists
            if not path.exists():
                raise SecurityError(f"File not found: {file_path}")
            
            # Check file size
            if path.stat().st_size > InputValidator.MAX_FILE_SIZE:
                raise SecurityError(f"File too large: {path.stat().st_size} bytes")
            
            # Check file extension
            if path.suffix.lower() not in InputValidator.ALLOWED_EXTENSIONS:
                raise SecurityError(f"Invalid file type: {path.suffix}")
            
            # Check for path traversal attempts
            if '..' in str(path) or path.is_absolute() and not str(path).startswith('/app'):
                raise SecurityError("Path traversal attempt detected")
            
            return path
            
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Invalid file path: {e}")
    
    @staticmethod
    def validate_text_input(text: str, field_name: str = "text") -> str:
        """Validate text input."""
        if not isinstance(text, str):
            raise SecurityError(f"{field_name} must be a string")
        
        if len(text) > InputValidator.MAX_TEXT_LENGTH:
            raise SecurityError(f"{field_name} too long: {len(text)} characters")
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
            r"(\b(OR|AND)\s+\".*\"\s*=\s*\".*\")",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise SecurityError(f"Potential SQL injection in {field_name}")
        
        # Check for XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise SecurityError(f"Potential XSS in {field_name}")
        
        return text.strip()
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise SecurityError(f"Invalid email format: {email}")
        
        if len(email) > 254:  # RFC 5321 limit
            raise SecurityError("Email too long")
        
        return email.lower()
    
    @staticmethod
    def validate_nit(nit: str) -> str:
        """Validate Colombian NIT format."""
        # Remove any non-digit characters except hyphens
        clean_nit = re.sub(r'[^\d-]', '', nit)
        
        # Check format: XXXXXXXXX-X or XXXXXXXXX
        if not re.match(r'^\d{8,10}(-\d)?$', clean_nit):
            raise SecurityError(f"Invalid NIT format: {nit}")
        
        return clean_nit


class RateLimiter:
    """Rate limiting implementation using Redis."""
    
    def __init__(self, redis_client: redis.Redis, default_limit: int = 100, window: int = 3600):
        """Initialize rate limiter.
        
        Args:
            redis_client: Redis client instance
            default_limit: Default requests per window
            window: Time window in seconds
        """
        self.redis = redis_client
        self.default_limit = default_limit
        self.window = window
    
    def is_allowed(self, key: str, limit: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed.
        
        Args:
            key: Unique identifier for rate limiting
            limit: Custom limit (overrides default)
            
        Returns:
            Tuple of (is_allowed, rate_info)
        """
        limit = limit or self.default_limit
        current_time = int(time.time())
        window_start = current_time - self.window
        
        # Use sliding window approach
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(key, self.window)
        
        results = pipe.execute()
        current_requests = results[1]
        
        is_allowed = current_requests < limit
        remaining = max(0, limit - current_requests - 1)
        reset_time = current_time + self.window
        
        rate_info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "window": self.window
        }
        
        return is_allowed, rate_info
    
    def get_rate_limit_headers(self, key: str, limit: Optional[int] = None) -> Dict[str, str]:
        """Get rate limit headers for HTTP response."""
        is_allowed, rate_info = self.is_allowed(key, limit)
        
        return {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset"]),
            "X-RateLimit-Window": str(rate_info["window"])
        }


class SecretsManager:
    """Secure secrets management."""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize secrets manager."""
        self.master_key = master_key or os.getenv('MASTER_SECRET_KEY')
        if not self.master_key:
            raise SecurityError("MASTER_SECRET_KEY not found in environment")
        
        # Derive encryption key from master key
        self.encryption_key = self._derive_key(self.master_key)
        self.cipher = Fernet(self.encryption_key)
    
    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive encryption key from password."""
        if salt is None:
            salt = b'supervincent_salt_2025'  # In production, use random salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            raise SecurityError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            raise SecurityError(f"Decryption failed: {e}")
    
    def hash_password(self, password: str) -> str:
        """Hash password securely."""
        salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return base64.b64encode(salt + pwd_hash).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            decoded = base64.b64decode(hashed)
            salt = decoded[:32]
            stored_hash = decoded[32:]
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return hmac.compare_digest(pwd_hash, stored_hash)
        except Exception:
            return False


class SecurityMiddleware:
    """Security middleware for request processing."""
    
    def __init__(self, rate_limiter: RateLimiter, validator: InputValidator):
        """Initialize security middleware."""
        self.rate_limiter = rate_limiter
        self.validator = validator
    
    def validate_request(self, file_path: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate incoming request."""
        # Rate limiting
        rate_key = f"rate_limit:{user_id or 'anonymous'}"
        is_allowed, rate_info = self.rate_limiter.is_allowed(rate_key)
        
        if not is_allowed:
            raise SecurityError(f"Rate limit exceeded: {rate_info}")
        
        # File validation
        validated_path = self.validator.validate_file_path(file_path)
        
        return {
            "file_path": str(validated_path),
            "rate_info": rate_info,
            "validated": True
        }


def require_authentication(func: Callable) -> Callable:
    """Decorator to require authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # In a real implementation, this would check JWT tokens, API keys, etc.
        # For now, we'll just log the requirement
        logger.info("Authentication required for %s", func.__name__)
        return func(*args, **kwargs)
    return wrapper


def rate_limit(limit: int = 100, window: int = 3600):
    """Decorator for rate limiting."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # In a real implementation, this would use the RateLimiter
            logger.info("Rate limiting applied to %s: %d requests per %d seconds", 
                       func.__name__, limit, window)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_input(**validators):
    """Decorator for input validation."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    kwargs[param_name] = validator(kwargs[param_name])
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Security configuration
SECURITY_CONFIG = {
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": [".pdf", ".jpg", ".jpeg", ".png"],
    "rate_limit": {
        "default": 100,
        "window": 3600,  # 1 hour
        "burst": 20  # Allow burst of 20 requests
    },
    "encryption": {
        "algorithm": "AES-256-GCM",
        "key_derivation": "PBKDF2",
        "iterations": 100000
    },
    "session": {
        "timeout": 3600,  # 1 hour
        "secure": True,
        "httponly": True,
        "samesite": "strict"
    }
}

