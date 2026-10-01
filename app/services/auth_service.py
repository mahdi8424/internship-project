from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.auth.refresh import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.core.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.db.models import RefreshToken, User


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def create_tokens(
    db: Session,
    user: User,
) -> tuple[str, str]:
    access_token = create_access_token(user.id)

    refresh_token = generate_refresh_token()

    refresh_token_hash = hash_refresh_token(
        refresh_token
    )

    now = datetime.now(timezone.utc)

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=now + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        ),
    )

    db.add(token_record)
    db.commit()

    return access_token, refresh_token