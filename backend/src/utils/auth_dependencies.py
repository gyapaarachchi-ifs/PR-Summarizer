"""Authentication dependencies for FastAPI endpoints.

This module provides FastAPI dependency injection functions for authentication,
authorization, and user session management.
"""

from typing import Optional, List, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.models.auth import UserSession, UserRole
from src.utils.jwt import get_jwt_manager, AuthenticationError, AuthorizationError
from src.utils.logger import get_logger


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)
logger = get_logger("auth_dependencies")


async def get_token_from_header(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Extract JWT token from Authorization header.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        JWT token string or None if not provided
    """
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return None


async def get_current_user(token: Optional[str] = Depends(get_token_from_header)) -> UserSession:
    """Get current authenticated user from JWT token.
    
    Args:
        token: JWT access token
        
    Returns:
        User session information
        
    Raises:
        HTTPException: If token is invalid or user not authenticated
    """
    if not token:
        logger.warning("No authentication token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        jwt_manager = get_jwt_manager()
        payload = jwt_manager.validate_token(token)
        
        # Extract user information from token
        user_session = UserSession(
            user_id=payload["sub"],
            username=payload["username"],
            role=UserRole(payload.get("role", "user")),
            permissions=payload.get("permissions", []),
            session_id=payload.get("jti", ""),
        )
        
        logger.debug("User authenticated successfully", extra={
            "user_id": user_session.user_id,
            "username": user_session.username,
            "role": user_session.role
        })
        
        return user_session
        
    except AuthenticationError as e:
        logger.warning("Authentication failed", extra={
            "error": str(e),
            "token": token[:20] + "..." if len(token) > 20 else token
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except Exception as e:
        logger.error("Authentication error", extra={
            "error": str(e),
            "token": token[:20] + "..." if len(token) > 20 else token
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    token: Optional[str] = Depends(get_token_from_header)
) -> Optional[UserSession]:
    """Get current user if authenticated, otherwise return None.
    
    This dependency allows endpoints to work with both authenticated
    and anonymous users.
    
    Args:
        token: JWT access token
        
    Returns:
        User session information or None if not authenticated
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


def require_role(required_role: UserRole):
    """Create dependency that requires specific user role or higher.
    
    Args:
        required_role: Minimum required role
        
    Returns:
        FastAPI dependency function
    """
    async def role_checker(current_user: UserSession = Depends(get_current_user)) -> UserSession:
        if not current_user.has_role(required_role):
            logger.warning("Authorization failed - insufficient role", extra={
                "user_id": current_user.user_id,
                "user_role": current_user.role,
                "required_role": required_role
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


def require_permission(required_permission: str):
    """Create dependency that requires specific permission.
    
    Args:
        required_permission: Required permission string
        
    Returns:
        FastAPI dependency function
    """
    async def permission_checker(current_user: UserSession = Depends(get_current_user)) -> UserSession:
        if not current_user.has_permission(required_permission):
            logger.warning("Authorization failed - missing permission", extra={
                "user_id": current_user.user_id,
                "required_permission": required_permission,
                "user_permissions": current_user.permissions
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {required_permission}"
            )
        return current_user
    
    return permission_checker


def require_any_permission(required_permissions: List[str]):
    """Create dependency that requires any of the specified permissions.
    
    Args:
        required_permissions: List of acceptable permissions
        
    Returns:
        FastAPI dependency function
    """
    async def permission_checker(current_user: UserSession = Depends(get_current_user)) -> UserSession:
        if not current_user.has_any_permission(required_permissions):
            logger.warning("Authorization failed - no matching permissions", extra={
                "user_id": current_user.user_id,
                "required_permissions": required_permissions,
                "user_permissions": current_user.permissions
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permissions: {', '.join(required_permissions)}"
            )
        return current_user
    
    return permission_checker


def require_admin():
    """Dependency that requires admin role."""
    return require_role(UserRole.ADMIN)


def require_user_or_admin():
    """Dependency that requires user role or higher."""
    return require_role(UserRole.USER)


def require_self_or_admin(user_id_param: str = "user_id"):
    """Create dependency that allows access to own resources or admin access.
    
    Args:
        user_id_param: Name of the path parameter containing user ID
        
    Returns:
        FastAPI dependency function
    """
    async def self_or_admin_checker(
        path_user_id: str,
        current_user: UserSession = Depends(get_current_user)
    ) -> UserSession:
        # Admin can access any user's resources
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Users can only access their own resources
        if current_user.user_id != path_user_id:
            logger.warning("Authorization failed - not self or admin", extra={
                "user_id": current_user.user_id,
                "requested_user_id": path_user_id
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own resources."
            )
        
        return current_user
    
    return self_or_admin_checker


# Type aliases for common dependency patterns
CurrentUser = Annotated[UserSession, Depends(get_current_user)]
OptionalCurrentUser = Annotated[Optional[UserSession], Depends(get_optional_current_user)]
AdminUser = Annotated[UserSession, Depends(require_admin())]
RegularUser = Annotated[UserSession, Depends(require_user_or_admin())]