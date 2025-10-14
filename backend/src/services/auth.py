"""Authentication service for user management and GitHub OAuth.

This module provides user authentication, registration, and GitHub OAuth integration
for the PR Summarizer application.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import httpx

from src.models.auth import (
    User, UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse,
    RefreshTokenRequest, RefreshTokenResponse, GitHubOAuthRequest, GitHubUser,
    UserSession, UserStatus, AuthProvider, UserRole
)
from src.models.config import get_config
from src.utils.jwt import get_jwt_manager, AuthenticationError, UserRole as JWTUserRole
from src.utils.logger import get_logger
from src.utils.exceptions import PRSummarizerError


class UserNotFoundError(PRSummarizerError):
    """User not found error."""
    
    def __init__(self, identifier: str):
        super().__init__(
            message=f"User not found: {identifier}",
            details={"identifier": identifier}
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials error."""
    
    def __init__(self):
        super().__init__(
            message="Invalid username or password",
            details={"reason": "invalid_credentials"}
        )


class UserExistsError(PRSummarizerError):
    """User already exists error."""
    
    def __init__(self, field: str, value: str):
        super().__init__(
            message=f"User already exists with {field}: {value}",
            details={"field": field, "value": value}
        )


class GitHubOAuthError(AuthenticationError):
    """GitHub OAuth error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"GitHub OAuth error: {message}",
            details=details or {}
        )


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self):
        self.config = get_config()
        self.jwt_manager = get_jwt_manager()
        self.logger = get_logger("auth_service")
        
        # In-memory user storage (replace with database in production)
        self._users: Dict[str, User] = {}
        self._users_by_username: Dict[str, str] = {}
        self._users_by_email: Dict[str, str] = {}
        self._passwords: Dict[str, str] = {}  # Store hashed passwords by user_id
        
        # Create default admin user if configured
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user if none exists."""
        # For development, create a default admin user
        admin_user = User(
            id="admin-001",
            username="admin",
            email="admin@example.com",
            full_name="Administrator",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL,
            permissions=[
                "read:projects", "write:projects", "delete:projects",
                "read:summaries", "write:summaries", "delete:summaries",
                "read:users", "write:users", "delete:users",
                "admin:system"
            ]
        )
        self._store_user(admin_user)
        # Store admin password
        self._passwords[admin_user.id] = self._hash_password("admin123")
        self.logger.info("Default admin user created", extra={
            "user_id": admin_user.id,
            "username": admin_user.username
        })
    
    def _store_user(self, user: User):
        """Store user in memory storage."""
        self._users[user.id] = user
        self._users_by_username[user.username] = user.id
        self._users_by_email[user.email] = user.id
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt.
        
        In production, use bcrypt or similar strong hashing algorithm.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{pwd_hash}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Stored password hash
            
        Returns:
            True if password matches
        """
        try:
            salt, pwd_hash = hashed.split(":", 1)
            return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
        except ValueError:
            return False
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create new user account.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user information
            
        Raises:
            UserExistsError: If user already exists
        """
        # Check if username or email already exists
        if user_data.username in self._users_by_username:
            raise UserExistsError("username", user_data.username)
        
        if user_data.email in self._users_by_email:
            raise UserExistsError("email", user_data.email)
        
        # Generate user ID
        user_id = f"user-{secrets.token_hex(8)}"
        
        # Create user
        user = User(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            auth_provider=user_data.auth_provider,
            permissions=self._get_default_permissions(user_data.role)
        )
        
        # Store password hash if provided (local auth)
        if user_data.password and user_data.auth_provider == AuthProvider.LOCAL:
            # Store in passwords dictionary
            self._passwords[user_id] = self._hash_password(user_data.password)
        
        self._store_user(user)
        
        self.logger.info("User created", extra={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        })
        
        return UserResponse(**user.dict())
    
    async def authenticate_user(self, login_data: LoginRequest) -> LoginResponse:
        """Authenticate user with username/password.
        
        Args:
            login_data: Login credentials
            
        Returns:
            Login response with tokens and user info
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserNotFoundError: If user doesn't exist
        """
        # Find user by username or email
        user_id = self._users_by_username.get(login_data.username)
        if not user_id:
            user_id = self._users_by_email.get(login_data.username)
        
        if not user_id:
            raise UserNotFoundError(login_data.username)
        
        user = self._users[user_id]
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(f"User account is {user.status.value}")
        
        # Verify password for local auth
        if user.auth_provider == AuthProvider.LOCAL:
            password_hash = self._passwords.get(user_id)
            if not password_hash or not self._verify_password(login_data.password, password_hash):
                raise InvalidCredentialsError()
        
        # Update last login time
        user.last_login_at = datetime.now(timezone.utc)
        
        # Generate tokens
        access_token = self.jwt_manager.create_access_token(
            user_id=user.id,
            username=user.username,
            role=JWTUserRole(user.role.value)
        )
        
        refresh_token = self.jwt_manager.create_refresh_token(
            user_id=user.id,
            username=user.username
        )
        
        self.logger.info("User authenticated", extra={
            "user_id": user.id,
            "username": user.username
        })
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.security.access_token_expire_minutes * 60,
            user=UserResponse(**user.dict())
        )
    
    async def refresh_token(self, refresh_data: RefreshTokenRequest) -> RefreshTokenResponse:
        """Refresh access token using refresh token.
        
        Args:
            refresh_data: Refresh token request
            
        Returns:
            New access token
        """
        access_token = self.jwt_manager.refresh_access_token(refresh_data.refresh_token)
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=self.config.security.access_token_expire_minutes * 60
        )
    
    async def github_oauth(self, oauth_data: GitHubOAuthRequest) -> LoginResponse:
        """Authenticate user with GitHub OAuth.
        
        Args:
            oauth_data: GitHub OAuth data
            
        Returns:
            Login response with tokens and user info
            
        Raises:
            GitHubOAuthError: If OAuth process fails
        """
        try:
            # Exchange code for access token
            github_token = await self._exchange_github_code(oauth_data.code)
            
            # Get user information from GitHub
            github_user = await self._get_github_user(github_token)
            
            # Find or create user
            user = await self._find_or_create_github_user(github_user)
            
            # Update last login time
            user.last_login_at = datetime.now(timezone.utc)
            
            # Generate tokens
            access_token = self.jwt_manager.create_access_token(
                user_id=user.id,
                username=user.username,
                role=JWTUserRole(user.role.value)
            )
            
            refresh_token = self.jwt_manager.create_refresh_token(
                user_id=user.id,
                username=user.username
            )
            
            self.logger.info("User authenticated via GitHub", extra={
                "user_id": user.id,
                "username": user.username,
                "github_id": user.github_id
            })
            
            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.config.security.access_token_expire_minutes * 60,
                user=UserResponse(**user.dict())
            )
            
        except Exception as e:
            self.logger.error("GitHub OAuth failed", extra={"error": str(e)})
            raise GitHubOAuthError(str(e))
    
    async def _exchange_github_code(self, code: str) -> str:
        """Exchange GitHub authorization code for access token.
        
        Args:
            code: GitHub authorization code
            
        Returns:
            GitHub access token
        """
        # This is a simplified implementation
        # In production, use actual GitHub OAuth configuration
        
        # For now, return a mock token for testing
        # In real implementation:
        # POST to https://github.com/login/oauth/access_token
        
        return f"gho_mock_token_{secrets.token_hex(16)}"
    
    async def _get_github_user(self, token: str) -> GitHubUser:
        """Get user information from GitHub API.
        
        Args:
            token: GitHub access token
            
        Returns:
            GitHub user information
        """
        # This is a simplified implementation
        # In production, make actual API call to GitHub
        
        # Mock GitHub user for testing
        return GitHubUser(
            id=12345,
            login="testuser",
            name="Test User",
            email="testuser@example.com",
            avatar_url="https://avatars.githubusercontent.com/u/12345"
        )
    
    async def _find_or_create_github_user(self, github_user: GitHubUser) -> User:
        """Find existing user or create new user from GitHub data.
        
        Args:
            github_user: GitHub user information
            
        Returns:
            User object
        """
        # Look for existing user by GitHub ID
        for user in self._users.values():
            if user.github_id == str(github_user.id):
                # Update user info from GitHub
                user.full_name = github_user.name or user.full_name
                user.avatar_url = github_user.avatar_url or user.avatar_url
                return user
        
        # Look for existing user by email
        if github_user.email and github_user.email in self._users_by_email:
            user_id = self._users_by_email[github_user.email]
            user = self._users[user_id]
            
            # Link GitHub account
            user.github_id = str(github_user.id)
            user.github_username = github_user.login
            user.auth_provider = AuthProvider.GITHUB
            
            return user
        
        # Create new user
        user_id = f"user-{secrets.token_hex(8)}"
        
        user = User(
            id=user_id,
            username=github_user.login,
            email=github_user.email or f"{github_user.login}@github.local",
            full_name=github_user.name,
            avatar_url=github_user.avatar_url,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.GITHUB,
            github_id=str(github_user.id),
            github_username=github_user.login,
            permissions=self._get_default_permissions(UserRole.USER)
        )
        
        self._store_user(user)
        
        self.logger.info("GitHub user created", extra={
            "user_id": user.id,
            "username": user.username,
            "github_id": user.github_id
        })
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User information or None if not found
        """
        user = self._users.get(user_id)
        if user:
            return UserResponse(**user.dict())
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User information or None if not found
        """
        user_id = self._users_by_username.get(username.lower())
        if user_id:
            user = self._users[user_id]
            return UserResponse(**user.dict())
        return None
    
    async def update_user(self, user_id: str, update_data: UserUpdate) -> UserResponse:
        """Update user information.
        
        Args:
            user_id: User identifier
            update_data: Update data
            
        Returns:
            Updated user information
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self._users.get(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        
        self.logger.info("User updated", extra={
            "user_id": user.id,
            "updated_fields": list(update_dict.keys())
        })
        
        return UserResponse(**user.dict())
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """List users with pagination.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of users
        """
        users = list(self._users.values())
        paginated_users = users[skip:skip + limit]
        
        return [UserResponse(**user.dict()) for user in paginated_users]
    
    def _get_default_permissions(self, role: UserRole) -> List[str]:
        """Get default permissions for user role.
        
        Args:
            role: User role
            
        Returns:
            List of default permissions
        """
        if role == UserRole.ADMIN:
            return [
                "read:projects", "write:projects", "delete:projects",
                "read:summaries", "write:summaries", "delete:summaries",
                "read:users", "write:users", "delete:users",
                "admin:system"
            ]
        elif role == UserRole.USER:
            return [
                "read:projects", "write:projects",
                "read:summaries", "write:summaries"
            ]
        else:  # READONLY
            return [
                "read:projects",
                "read:summaries"
            ]


# Singleton auth service instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get singleton auth service instance.
    
    Returns:
        AuthService instance
    """
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service