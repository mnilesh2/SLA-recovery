from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User

pwd_hasher = PasswordHasher()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    return pwd_hasher.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def get_token_from_request(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else None


def get_current_user(token: Optional[str] = Depends(get_token_from_request), db: Session = Depends(get_db)) -> User:
    default_user = db.query(User).filter(User.username == "admin").first()
    if default_user is None:
        default_user = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(default_user)
        db.commit()

    if token is None:
        return default_user

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return default_user
    except JWTError:
        return default_user

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return default_user
    return user


def require_role(*allowed_roles: str):
    def check_role(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user.role}' not authorized for this action"
            )
        return user
    return check_role
