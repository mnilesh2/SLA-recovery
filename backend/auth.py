"""
Authentication and Authorization
JWT-based auth with role-based access control (RBAC)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .models import User
from .database import get_db

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# JWT configuration
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, username: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(user_id),  # Convert to string - JWT standard requires string subject
        "username": username,
        "role": role,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        logger.info(f"Attempting to verify token: {token[:50]}...")
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        logger.info(f"Token decoded successfully. Payload: {payload}")

        user_id_str: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")

        # Convert user_id from string to int
        try:
            user_id: int = int(user_id_str) if user_id_str else None
        except (ValueError, TypeError):
            user_id = None

        logger.info(f"Extracted from token - user_id: {user_id}, username: {username}, role: {role}")

        if user_id is None or username is None:
            logger.error("Invalid token - missing user_id or username")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        return {
            "user_id": user_id,
            "username": username,
            "role": role
        }
    except JWTError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user"""
    logger.info(f"get_current_user called with credentials: {credentials}")

    if not credentials:
        logger.error("No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No credentials provided"
        )

    # Extract token - try different attribute names
    token = None
    if hasattr(credentials, 'credentials'):
        token = credentials.credentials
        logger.info(f"Token extracted from credentials.credentials: {token[:20] if token else None}...")
    elif hasattr(credentials, 'token'):
        token = credentials.token
        logger.info(f"Token extracted from credentials.token: {token[:20] if token else None}...")
    else:
        token = str(credentials)
        logger.info(f"Token extracted as string: {token[:20] if token else None}...")

    if not token:
        logger.error("No token found in credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token found"
        )

    try:
        token_data = verify_token(token)
    except HTTPException as e:
        logger.error(f"Token verification failed: {e.detail}")
        raise

    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user or not user.is_active:
        logger.error(f"User not found or inactive for user_id: {token_data.get('user_id')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    logger.info(f"User authenticated: {user.username}")
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_approver_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is approver or admin"""
    if current_user.role not in ["approver", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approver access required"
        )
    return current_user


def check_role(required_role: str):
    """Factory for role-checking dependency"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user

    return role_checker


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: str = "reviewer"
) -> User:
    """Create a new user"""
    hashed_password = hash_password(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"User created: {username} (role: {role})")
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
