import datetime
from typing import Optional, List
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import TokenData
from app.core.redis_client import redis_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None, token_version: Optional[int] = None) -> str:
    to_encode = data.copy()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": int(now_utc.timestamp()),
        "token_version": token_version if token_version is not None else 1
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

import hashlib
import re

def validate_password_complexity(password: str) -> None:
    """Enforces minimum 8 characters and character variety."""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )
    if not re.search(r"[a-zA-Z]", password) or not re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one letter and at least one number or special character."
        )

def revoke_token(token: str, ttl_seconds: int = 3600) -> bool:
    """Revokes a JWT by storing its SHA-256 fingerprint in the Redis blacklist."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return redis_client.setex(f"revoked_token:{token_hash}", ttl_seconds, "revoked")

def is_token_revoked(token: str) -> bool:
    """Checks if a JWT is present in the Redis revocation store."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return bool(redis_client.get(f"revoked_token:{token_hash}"))

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify token is not revoked in Redis
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been terminated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    if user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active."
        )

    # Verify token version matches user's current token version (invalidates tokens on password reset)
    token_version = payload.get("token_version")
    if token_version is not None and user.token_version and token_version < user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked due to a password reset. Please log in with your new credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token was issued after any password change
    if user.password_changed_at:
        token_iat = payload.get("iat")
        if token_iat:
            token_issued_at = datetime.datetime.fromtimestamp(token_iat, tz=datetime.timezone.utc)
            pwd_changed_at = user.password_changed_at
            if pwd_changed_at.tzinfo is None:
                pwd_changed_at = pwd_changed_at.replace(tzinfo=datetime.timezone.utc)
            pwd_changed_at = pwd_changed_at.replace(microsecond=0)
            if token_issued_at < pwd_changed_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session has been revoked due to a password reset. Please log in with your new credentials.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return current_user

def verify_google_id_token(id_token: str) -> Optional[dict]:
    import os
    import requests
    import time
    try:
        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=5
        )
        if response.status_code != 200:
            return None
        token_info = response.json()

        # 1. Issuer Validation
        if token_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            return None

        # 2. Expiration Validation
        exp = int(token_info.get("exp", 0))
        if exp < time.time():
            return None

        # 3. Subject (User ID) Validation
        if not token_info.get("sub"):
            return None

        # 4. Audience (Client ID) Validation
        expected_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if expected_client_id:
            token_aud = token_info.get("aud")
            token_azp = token_info.get("azp")
            if token_aud != expected_client_id and token_azp != expected_client_id:
                return None

        return token_info
    except Exception as e:
        print(f"Error validating Google ID Token: {e}")
        return None
