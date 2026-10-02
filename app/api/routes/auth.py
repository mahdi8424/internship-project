from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.auth.refresh import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.core.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.db.models import RefreshToken, User
from app.db.session import get_db
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import authenticate_user, create_tokens


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


# ---------------------------------------------------------
# Register
# ---------------------------------------------------------


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role="member",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ---------------------------------------------------------
# Login
# ---------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        data.email,
        data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token, refresh_token = create_tokens(
        db,
        user,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ---------------------------------------------------------
# Refresh token
# ---------------------------------------------------------


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    token_hash = hash_refresh_token(
        data.refresh_token
    )

    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )

    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if token_record.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    now = datetime.now(timezone.utc)

    expires_at = token_record.expires_at

    # SQLite may return naive datetimes even when the model
    # uses timezone-aware datetime values.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    user = db.get(
        User,
        token_record.user_id,
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive user",
        )

    # Rotate the refresh token.
    token_record.revoked_at = now

    access_token = create_access_token(
        user.id
    )

    new_refresh_token = generate_refresh_token()

    new_refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(
            new_refresh_token
        ),
        expires_at=now + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        ),
    )

    db.add(new_refresh_record)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


# ---------------------------------------------------------
# Logout
# ---------------------------------------------------------


@router.post("/logout")
def logout(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    token_hash = hash_refresh_token(
        data.refresh_token
    )

    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )

    if token_record is not None:
        if token_record.revoked_at is None:
            token_record.revoked_at = datetime.now(
                timezone.utc
            )
            db.commit()

    return {
        "message": "Logged out successfully",
    }


# ---------------------------------------------------------
# Current user
# ---------------------------------------------------------


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


# ---------------------------------------------------------
# Change password
# ---------------------------------------------------------


@router.put("/me/password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(
        data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(
        data.new_password
    )

    # Changing the password invalidates all existing
    # refresh tokens for this user.
    now = datetime.now(timezone.utc)

    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(
            revoked_at=now
        )
    )

    db.commit()

    return {
        "message": "Password changed successfully",
    }