"""API dependencies."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prisma.models import User

from app.db.prisma import get_prisma
from app.utils.auth import decode_token
from app.utils.errors import InvalidTokenError, UserNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        logger.warning("Invalid or expired token", token_type=None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        logger.warning("Wrong token type", token_type=payload.get("type"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("Token missing subject claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = await get_prisma()
    user = await db.user.find_unique(where={"id": user_id})
    
    if user is None:
        logger.warning("User not found for token", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug("Authenticated user", user_id=user_id, email=user.email)
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """Get optional authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials (optional)

    Returns:
        Current authenticated user or None if not authenticated
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
