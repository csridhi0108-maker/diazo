"""
Authentication endpoints: register, login, refresh.
Everything downstream (protected routes) relies on the tokens issued
here, verified later by core/dependencies.py.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.schemas.user import UserRegister, UserOut, TokenPair, RefreshRequest


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == payload.email).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        preferred_language=payload.preferred_language,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenPair)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # OAuth2 uses the "username" field.
    # In DIAZO, we use the user's email as the username.
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    # Account does not exist
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email. Try signing up.",
        )

    # Account exists, but password is incorrect
    if not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again.",
        )

    # Successful login
    token_data = {
        "sub": str(user.id),
        "role": user.role.value,
    }

    return TokenPair(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db)
):
    decoded = decode_token(payload.refresh_token)

    if decoded is None or decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = (
        db.query(User)
        .filter(User.id == decoded["sub"])
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    # Issue a fresh access + refresh token pair
    token_data = {
        "sub": str(user.id),
        "role": user.role.value,
    }

    return TokenPair(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )