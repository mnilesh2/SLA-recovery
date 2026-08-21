"""
Authentication Router
User login, registration, and token management
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import (
    authenticate_user, get_user_by_username, create_user,
    create_access_token, get_current_user
)
from ..models import User
from ..schemas import (
    UserCreate, UserResponse, TokenResponse, LoginRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    Args:
        user_data: User registration data (username, email, password)
        db: Database session

    Returns:
        Created user details
    """
    # Check if user already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )

    # Create new user
    try:
        user = create_user(
            db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role if hasattr(user_data, 'role') else "reviewer"
        )
        logger.info(f"New user registered: {user.username}")
        return user
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login user and get access token

    Args:
        credentials: Login credentials (username and password)
        db: Database session

    Returns:
        Access token and user details
    """
    # Authenticate user
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(user.id, user.username, user.role)
    logger.info(f"User logged in: {user.username}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information

    Args:
        current_user: Current authenticated user

    Returns:
        Current user details
    """
    return current_user


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (invalidate token client-side)

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.username}")
    return {
        "status": "success",
        "message": "Logged out successfully"
    }


@router.post("/refresh-token")
def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh access token

    Args:
        current_user: Current authenticated user

    Returns:
        New access token
    """
    new_token = create_access_token(current_user.id, current_user.username, current_user.role)
    logger.info(f"Token refreshed for user: {current_user.username}")

    return {
        "access_token": new_token,
        "token_type": "bearer"
    }
