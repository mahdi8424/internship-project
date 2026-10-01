from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )