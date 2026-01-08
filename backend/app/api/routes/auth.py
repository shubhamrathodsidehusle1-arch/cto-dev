"""Authentication API routes."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.auth import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    TokenResponse,
    UserResponse
)
from app.api.dependencies import get_current_user
from app.db.prisma import get_prisma
from app.db.models import create_job, update_job_status
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.utils.errors import (
    DuplicateEmailError,
    AuthenticationError,
    InvalidTokenError,
    DatabaseError
)
from app.config import settings
from app.utils.logger import get_logger
from prisma.models import User

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserRegister) -> UserResponse:
    """Register a new user.

    Args:
        user_data: User registration data

    Returns:
        Created user

    Raises:
        DuplicateEmailError: If email already exists
    """
    db = await get_prisma()
    
    # Check if user already exists
    existing_user = await db.user.find_unique(
        where={"email": user_data.email}
    )
    if existing_user:
        logger.warning("Registration attempt with existing email", email=user_data.email)
        raise DuplicateEmailError(user_data.email)
    
    # Hash password
    password_hash = get_password_hash(user_data.password)
    
    # Create user
    try:
        user = await db.user.create(
            data={
                "email": user_data.email,
                "passwordHash": password_hash
            }
        )
        logger.info("User registered", user_id=user.id, email=user.email)
        return UserResponse.model_validate(user)
    except Exception as e:
        logger.error("Failed to create user", error=str(e))
        raise DatabaseError(f"Failed to create user: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin) -> TokenResponse:
    """Authenticate user and return tokens.

    Args:
        user_data: User login data

    Returns:
        Access and refresh tokens

    Raises:
        AuthenticationError: If credentials are invalid
    """
    db = await get_prisma()
    
    # Find user by email
    user = await db.user.find_unique(where={"email": user_data.email})
    
    if not user or not verify_password(user_data.password, user.passwordHash):
        logger.warning("Failed login attempt", email=user_data.email)
        raise AuthenticationError("Invalid email or password")
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    logger.info("User logged in", user_id=user.id, email=user.email)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        token_data: Refresh token data

    Returns:
        New access and refresh tokens

    Raises:
        InvalidTokenError: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_token(token_data.refresh_token)
    
    if payload is None:
        logger.warning("Invalid refresh token")
        raise InvalidTokenError("Invalid or expired refresh token")
    
    if payload.get("type") != "refresh":
        logger.warning("Wrong token type for refresh endpoint")
        raise InvalidTokenError("Invalid token type")
    
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("Refresh token missing subject claim")
        raise InvalidTokenError("Invalid token payload")
    
    # Verify user still exists
    db = await get_prisma()
    user = await db.user.find_unique(where={"id": user_id})
    
    if user is None:
        logger.warning("User not found for refresh token", user_id=user_id)
        raise InvalidTokenError("User not found")
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    logger.info("Token refreshed", user_id=user.id, email=user.email)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user profile.

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        Current user profile
    """
    logger.debug("User profile requested", user_id=current_user.id)
    return UserResponse.model_validate(current_user)
