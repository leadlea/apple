"""
Security configuration and utilities for Mac Status PWA
セキュリティ設定とユーティリティ
"""

import hashlib
import hmac
import secrets
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict, deque

@dataclass
class RateLimitEntry:
    """Rate limiting entry"""
    requests: deque
    last_request: float

class SecurityManager:
    """Security manager for the application"""
    
    def __init__(self):
        self.rate_limits: Dict[str, RateLimitEntry] = defaultdict(
            lambda: RateLimitEntry(deque(), 0.0)
        )
        self.blocked_ips: set = set()
        self.session_tokens: Dict[str, float] = {}
        self.secret_key = secrets.token_hex(32)
    
    def check_rate_limit(self, client_ip: str, requests_per_minute: int = 60) -> bool:
        """Check if client is within rate limits"""
        current_time = time.time()
        entry = self.rate_limits[client_ip]
        
        # Remove old requests (older than 1 minute)
        while entry.requests and entry.requests[0] < current_time - 60:
            entry.requests.popleft()
        
        # Check if under limit
        if len(entry.requests) >= requests_per_minute:
            return False
        
        # Add current request
        entry.requests.append(current_time)
        entry.last_request = current_time
        
        return True
    
    def is_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked"""
        return client_ip in self.blocked_ips
    
    def block_ip(self, client_ip: str):
        """Block an IP address"""
        self.blocked_ips.add(client_ip)
    
    def unblock_ip(self, client_ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(client_ip)
    
    def generate_session_token(self) -> str:
        """Generate a secure session token"""
        token = secrets.token_urlsafe(32)
        self.session_tokens[token] = time.time()
        return token
    
    def validate_session_token(self, token: str, max_age: int = 3600) -> bool:
        """Validate session token"""
        if token not in self.session_tokens:
            return False
        
        token_time = self.session_tokens[token]
        if time.time() - token_time > max_age:
            del self.session_tokens[token]
            return False
        
        return True
    
    def cleanup_expired_tokens(self, max_age: int = 3600):
        """Clean up expired session tokens"""
        current_time = time.time()
        expired_tokens = [
            token for token, token_time in self.session_tokens.items()
            if current_time - token_time > max_age
        ]
        
        for token in expired_tokens:
            del self.session_tokens[token]

# Content Security Policy
CSP_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],  # Needed for inline scripts
    "style-src": ["'self'", "'unsafe-inline'"],   # Needed for inline styles
    "img-src": ["'self'", "data:", "blob:"],
    "font-src": ["'self'"],
    "connect-src": ["'self'", "ws://localhost:*", "wss://localhost:*"],
    "media-src": ["'none'"],
    "object-src": ["'none'"],
    "frame-src": ["'none'"],
    "worker-src": ["'self'"],
    "manifest-src": ["'self'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
    "upgrade-insecure-requests": True
}

def generate_csp_header() -> str:
    """Generate Content Security Policy header"""
    policies = []
    
    for directive, sources in CSP_POLICY.items():
        if directive == "upgrade-insecure-requests":
            if sources:
                policies.append("upgrade-insecure-requests")
        else:
            policy = f"{directive} {' '.join(sources)}"
            policies.append(policy)
    
    return "; ".join(policies)

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": generate_csp_header()
}

def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not isinstance(input_string, str):
        return ""
    
    # Limit length
    sanitized = input_string[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    return sanitized

def validate_websocket_origin(origin: str, allowed_origins: List[str]) -> bool:
    """Validate WebSocket origin"""
    if not origin:
        return False
    
    return origin in allowed_origins

def generate_nonce() -> str:
    """Generate a cryptographic nonce"""
    return secrets.token_hex(16)

def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """Hash password with salt (for future authentication features)"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use PBKDF2 with SHA-256
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return key.hex(), salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify password against hash"""
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hmac.compare_digest(key.hex(), hashed)

# Security middleware configuration
SECURITY_MIDDLEWARE_CONFIG = {
    "rate_limiting": {
        "enabled": True,
        "requests_per_minute": 60,
        "burst_size": 10,
        "block_duration": 300  # 5 minutes
    },
    "input_validation": {
        "enabled": True,
        "max_message_length": 1000,
        "sanitize_html": True
    },
    "session_management": {
        "enabled": True,
        "token_expiry": 3600,  # 1 hour
        "cleanup_interval": 300  # 5 minutes
    },
    "cors": {
        "enabled": True,
        "strict_origin_check": True
    }
}

# Create global security manager instance
security_manager = SecurityManager()