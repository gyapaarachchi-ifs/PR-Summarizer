"""User models for authentication and authorization.

This module defines user-related data models for the PR Summarizer application,
including authentication, authorization, and user management.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, validator

from src.utils.jwt import UserRole


class AuthProvider(str, Enum):
    """Authentication provider enumeration."""
    
    LOCAL = "local"
    GITHUB = "github"
    GOOGLE = "google"


class UserStatus(str, Enum):
    """User status enumeration."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseModel):
    """User model for authentication and profile management."""
    
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=200, description="Full name")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    
    # Authentication
    role: UserRole = Field(default=UserRole.USER, description="User role")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="User status")
    auth_provider: AuthProvider = Field(default=AuthProvider.LOCAL, description="Authentication provider")
    
    # Provider-specific data
    github_id: Optional[str] = Field(None, description="GitHub user ID")
    github_username: Optional[str] = Field(None, description="GitHub username")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Permissions and preferences
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """Validate permissions format."""
        # Define valid permissions
        valid_permissions = {
            'read:projects', 'write:projects', 'delete:projects',
            'read:summaries', 'write:summaries', 'delete:summaries',
            'read:users', 'write:users', 'delete:users',
            'admin:system'
        }
        
        for perm in v:
            if perm not in valid_permissions:
                raise ValueError(f'Invalid permission: {perm}')
        
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserCreate(BaseModel):
    """Model for creating new users."""
    
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=200, description="Full name")
    password: Optional[str] = Field(None, min_length=8, description="Password (for local auth)")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    auth_provider: AuthProvider = Field(default=AuthProvider.LOCAL, description="Authentication provider")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class UserUpdate(BaseModel):
    """Model for updating user information."""
    
    full_name: Optional[str] = Field(None, max_length=200, description="Full name")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    role: Optional[UserRole] = Field(None, description="User role")
    status: Optional[UserStatus] = Field(None, description="User status")
    permissions: Optional[List[str]] = Field(None, description="User permissions")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """Validate permissions format."""
        if v is None:
            return v
            
        valid_permissions = {
            'read:projects', 'write:projects', 'delete:projects',
            'read:summaries', 'write:summaries', 'delete:summaries',
            'read:users', 'write:users', 'delete:users',
            'admin:system'
        }
        
        for perm in v:
            if perm not in valid_permissions:
                raise ValueError(f'Invalid permission: {perm}')
        
        return v


class UserResponse(BaseModel):
    """User response model (excludes sensitive data)."""
    
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    status: UserStatus
    auth_provider: AuthProvider
    created_at: datetime
    last_login_at: Optional[datetime]
    permissions: List[str]
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LoginRequest(BaseModel):
    """Login request model."""
    
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    
    @validator('username')
    def validate_username(cls, v):
        """Normalize username."""
        return v.lower().strip()


class LoginResponse(BaseModel):
    """Login response model."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    
    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response model."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class GitHubOAuthRequest(BaseModel):
    """GitHub OAuth authentication request."""
    
    code: str = Field(..., description="GitHub authorization code")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


class GitHubUser(BaseModel):
    """GitHub user information from OAuth."""
    
    id: int = Field(..., description="GitHub user ID")
    login: str = Field(..., description="GitHub username")
    name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Primary email")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    
    
class PasswordChangeRequest(BaseModel):
    """Password change request model."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        import re
        
        # Check minimum requirements
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v


class UserSession(BaseModel):
    """User session information."""
    
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    role: UserRole = Field(..., description="User role")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session creation time")
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission.
        
        Args:
            permission: Permission string to check
            
        Returns:
            True if user has permission
        """
        # Admin role has all permissions
        if self.role == UserRole.ADMIN:
            return True
        
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            True if user has at least one permission
        """
        if self.role == UserRole.ADMIN:
            return True
        
        return any(perm in self.permissions for perm in permissions)
    
    def has_role(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher.
        
        Args:
            required_role: Required user role
            
        Returns:
            True if user has required role or higher
        """
        # Define role hierarchy
        role_hierarchy = {
            UserRole.READONLY: 1,
            UserRole.USER: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level