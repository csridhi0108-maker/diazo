"""
Security utilities: password hashing and JWT creation/verification.
Used by app/api/auth.py (login/register) and app/core/dependencies.py
(to decode the token on every protected request).
"""

from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt is the industry-standard password hashing scheme — slow by
# design (to resist brute-force attacks), and passlib handles the
# salting/versioning for us.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password before storing it in the DB.
    Never store plain_password anywhere."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login attempt's password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Short-lived token (default 30 min) sent on every request to prove
    identity. `data` should include at minimum {"sub": user_id, "role": role}
    so downstream dependencies can check role-based access without a DB hit.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Long-lived token (default 7 days) used only to obtain a new access
    token once it expires, without forcing the user to log in again.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """
    Verify a token's signature and expiry, and return its payload.
    Returns None on any failure (expired, tampered, malformed) — the
    caller (a FastAPI dependency) is responsible for turning that into
    a proper 401 response.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None