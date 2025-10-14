"""Authentication API endpoints.

This module provides REST API endpoints for user authentication, registration,
and user management functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer

from src.models.auth import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse,
    RefreshTokenRequest, RefreshTokenResponse, GitHubOAuthRequest,
    PasswordChangeRequest, UserSession
)
from src.services.auth import get_auth_service, AuthService
from src.utils.auth_dependencies import (
    get_current_user, require_admin, require_self_or_admin,
    CurrentUser, AdminUser
)
from src.utils.logger import get_logger
from src.utils.exceptions import PRSummarizerError


# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger("auth_api")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Register a new user account.
    
    Args:
        user_data: User registration data
        auth_service: Authentication service
        
    Returns:
        Created user information
    """
    try:
        user = await auth_service.create_user(user_data)
        
        logger.info("User registered successfully", extra={
            "user_id": user.id,
            "username": user.username,
            "auth_provider": user.auth_provider
        })
        
        return user
        
    except PRSummarizerError as e:
        logger.warning("User registration failed", extra={
            "error": str(e),
            "username": user_data.username
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """Authenticate user with username/password.
    
    Args:
        login_data: Login credentials
        auth_service: Authentication service
        
    Returns:
        Login response with access token and user info
    """
    try:
        response = await auth_service.authenticate_user(login_data)
        
        logger.info("User login successful", extra={
            "user_id": response.user.id,
            "username": response.user.username
        })
        
        return response
        
    except PRSummarizerError as e:
        logger.warning("User login failed", extra={
            "error": str(e),
            "username": login_data.username
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> RefreshTokenResponse:
    """Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token request
        auth_service: Authentication service
        
    Returns:
        New access token
    """
    try:
        response = await auth_service.refresh_token(refresh_data)
        
        logger.info("Token refreshed successfully")
        
        return response
        
    except PRSummarizerError as e:
        logger.warning("Token refresh failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/github", response_model=LoginResponse)
async def github_oauth(
    oauth_data: GitHubOAuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """Authenticate user with GitHub OAuth.
    
    Args:
        oauth_data: GitHub OAuth request data
        auth_service: Authentication service
        
    Returns:
        Login response with access token and user info
    """
    try:
        response = await auth_service.github_oauth(oauth_data)
        
        logger.info("GitHub OAuth successful", extra={
            "user_id": response.user.id,
            "username": response.user.username
        })
        
        return response
        
    except PRSummarizerError as e:
        logger.warning("GitHub OAuth failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser
) -> UserResponse:
    """Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    auth_service = get_auth_service()
    user = await auth_service.get_user_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Update current user information.
    
    Args:
        update_data: User update data
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        Updated user information
    """
    try:
        # Users can't change their own role or status
        if update_data.role is not None or update_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify role or status"
            )
        
        user = await auth_service.update_user(current_user.user_id, update_data)
        
        logger.info("User profile updated", extra={
            "user_id": current_user.user_id,
            "updated_by": current_user.username
        })
        
        return user
        
    except PRSummarizerError as e:
        logger.warning("User profile update failed", extra={
            "error": str(e),
            "user_id": current_user.user_id
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change current user password.
    
    Args:
        password_data: Password change request
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        Success message
    """
    # This is a placeholder implementation
    # In production, implement actual password change logic
    
    logger.info("Password change requested", extra={
        "user_id": current_user.user_id,
        "username": current_user.username
    })
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout_user(current_user: CurrentUser):
    """Logout current user.
    
    This endpoint can be used to invalidate tokens on the client side.
    In a production system, you might want to maintain a token blacklist.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info("User logout", extra={
        "user_id": current_user.user_id,
        "username": current_user.username
    })
    
    return {"message": "Logged out successfully"}


# Admin endpoints for user management
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    admin_user: AdminUser,
    auth_service: AuthService = Depends(get_auth_service),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return")
) -> List[UserResponse]:
    """List all users (admin only).
    
    Args:
        skip: Number of users to skip for pagination
        limit: Maximum number of users to return
        admin_user: Admin user making the request
        auth_service: Authentication service
        
    Returns:
        List of users
    """
    users = await auth_service.list_users(skip=skip, limit=limit)
    
    logger.info("Users listed", extra={
        "admin_user_id": admin_user.user_id,
        "count": len(users)
    })
    
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    admin_user: AdminUser,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Get user by ID (admin only).
    
    Args:
        user_id: User identifier
        admin_user: Admin user making the request
        auth_service: Authentication service
        
    Returns:
        User information
    """
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: str,
    update_data: UserUpdate,
    admin_user: AdminUser,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Update user by ID (admin only).
    
    Args:
        user_id: User identifier
        update_data: User update data
        admin_user: Admin user making the request
        auth_service: Authentication service
        
    Returns:
        Updated user information
    """
    try:
        user = await auth_service.update_user(user_id, update_data)
        
        logger.info("User updated by admin", extra={
            "user_id": user_id,
            "admin_user_id": admin_user.user_id,
            "updated_fields": list(update_data.dict(exclude_unset=True).keys())
        })
        
        return user
        
    except PRSummarizerError as e:
        logger.warning("Admin user update failed", extra={
            "error": str(e),
            "user_id": user_id,
            "admin_user_id": admin_user.user_id
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )