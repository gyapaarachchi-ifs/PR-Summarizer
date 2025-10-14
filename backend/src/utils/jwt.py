"""JWT token utilities for authentication.

This module provides JWT token generation, validation, and refresh functionality
for secure user authentication and authorization.
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
from enum import Enum

from src.models.config import get_config
from src.utils.logger import get_logger
from src.utils.exceptions import PRSummarizerError


class TokenType(str, Enum):
    """JWT token type enumeration."""
    
    ACCESS = "access"
    REFRESH = "refresh"


class UserRole(str, Enum):
    """User role enumeration for RBAC."""
    
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class AuthenticationError(PRSummarizerError):
    """Authentication-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details or {})


class AuthorizationError(PRSummarizerError):
    """Authorization-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details or {})


class TokenExpiredError(AuthenticationError):
    """Token expired error."""
    
    def __init__(self, token_type: str = "access"):
        super().__init__(
            message=f"Token expired: {token_type}",
            details={"token_type": token_type}
        )


class InvalidTokenError(AuthenticationError):
    """Invalid token error."""
    
    def __init__(self, reason: str = "invalid"):
        super().__init__(
            message=f"Invalid token: {reason}",
            details={"reason": reason}
        )


class JWTManager:
    """JWT token management utility."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("jwt_manager")
        
        # JWT configuration
        self.secret_key = self.config.security.secret_key
        self.algorithm = self.config.security.algorithm
        self.access_token_expire_minutes = self.config.security.access_token_expire_minutes
        self.refresh_token_expire_days = 7  # Refresh tokens last 7 days
    
    def create_access_token(
        self, 
        user_id: str,
        username: str,
        role: UserRole = UserRole.USER,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token.
        
        Args:
            user_id: User identifier
            username: Username
            role: User role for RBAC
            expires_delta: Custom expiration time
            
        Returns:
            JWT access token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        payload = {
            "sub": user_id,
            "username": username,
            "role": role.value,
            "type": TokenType.ACCESS.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": self._generate_token_id()  # JWT ID for revocation
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        self.logger.info("Access token created", extra={
            "user_id": user_id,
            "username": username,
            "role": role.value,
            "expires_at": expire.isoformat()
        })
        
        return token
    
    def create_refresh_token(self, user_id: str, username: str) -> str:
        """Create JWT refresh token.
        
        Args:
            user_id: User identifier
            username: Username
            
        Returns:
            JWT refresh token string
        """
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "username": username,
            "type": TokenType.REFRESH.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": self._generate_token_id()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        self.logger.info("Refresh token created", extra={
            "user_id": user_id,
            "username": username,
            "expires_at": expire.isoformat()
        })
        
        return token
    
    def validate_token(self, token: str, token_type: Optional[TokenType] = None) -> Dict[str, Any]:
        """Validate JWT token and extract payload.
        
        Args:
            token: JWT token string
            token_type: Expected token type (optional)
            
        Returns:
            Token payload dictionary
            
        Raises:
            InvalidTokenError: If token is invalid
            TokenExpiredError: If token has expired
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            # Validate token type if specified
            if token_type and payload.get("type") != token_type.value:
                raise InvalidTokenError(f"expected {token_type.value} token")
            
            # Ensure required fields are present
            required_fields = ["sub", "username", "type", "exp", "iat"]
            for field in required_fields:
                if field not in payload:
                    raise InvalidTokenError(f"missing field: {field}")
            
            self.logger.debug("Token validated successfully", extra={
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "token_type": payload.get("type")
            })
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired", extra={"token": token[:20] + "..."})
            raise TokenExpiredError(token_type.value if token_type else "unknown")
            
        except jwt.InvalidTokenError as e:
            self.logger.warning("Invalid token", extra={
                "error": str(e),
                "token": token[:20] + "..."
            })
            raise InvalidTokenError(str(e))
        
        except Exception as e:
            self.logger.error("Token validation error", extra={
                "error": str(e),
                "token": token[:20] + "..."
            })
            raise InvalidTokenError("validation failed")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            InvalidTokenError: If refresh token is invalid
            TokenExpiredError: If refresh token has expired
        """
        # Validate refresh token
        payload = self.validate_token(refresh_token, TokenType.REFRESH)
        
        user_id = payload["sub"]
        username = payload["username"]
        
        # Create new access token
        # Note: In production, you might want to check if the refresh token
        # has been revoked in the database
        access_token = self.create_access_token(user_id, username)
        
        self.logger.info("Access token refreshed", extra={
            "user_id": user_id,
            "username": username
        })
        
        return access_token
    
    def extract_user_info(self, token: str) -> Dict[str, Any]:
        """Extract user information from token without full validation.
        
        This is useful for logging or when you need user info from expired tokens.
        
        Args:
            token: JWT token string
            
        Returns:
            User information dictionary
        """
        try:
            # Decode without verification for information extraction
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            
            return {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "role": payload.get("role"),
                "token_type": payload.get("type"),
                "expires_at": payload.get("exp")
            }
            
        except Exception as e:
            self.logger.warning("Failed to extract user info from token", extra={
                "error": str(e),
                "token": token[:20] + "..."
            })
            return {}
    
    def _generate_token_id(self) -> str:
        """Generate unique token ID for JWT ID claim.
        
        Returns:
            Unique token identifier
        """
        import uuid
        return str(uuid.uuid4())
    
    def get_token_ttl(self, token: str) -> Optional[int]:
        """Get time-to-live for a token in seconds.
        
        Args:
            token: JWT token string
            
        Returns:
            TTL in seconds, or None if token is invalid/expired
        """
        try:
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            
            exp = payload.get("exp")
            if exp:
                expire_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                
                if expire_time > now:
                    return int((expire_time - now).total_seconds())
            
            return None
            
        except Exception:
            return None


# Singleton JWT manager instance
_jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """Get singleton JWT manager instance.
    
    Returns:
        JWTManager instance
    """
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager