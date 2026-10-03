from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import (
    LOGIN_RATE_LIMIT,
    LOGIN_RATE_WINDOW_SECONDS,
)
from app.db.models import LoginAttempt


def is_login_rate_limited(
    db: Session,
    email: str,
    ip_address: str,
) -> bool:
    now = datetime.now(timezone.utc)

    window_start = now - timedelta(
        seconds=LOGIN_RATE_WINDOW_SECONDS,
    )

    attempt_count = db.scalar(
        select(func.count(LoginAttempt.id))
        .where(
            LoginAttempt.email == email,
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.attempted_at >= window_start,
        )
    )

    return (attempt_count or 0) >= LOGIN_RATE_LIMIT


def record_failed_login(
    db: Session,
    email: str,
    ip_address: str,
) -> None:
    attempt = LoginAttempt(
        email=email,
        ip_address=ip_address,
        attempted_at=datetime.now(timezone.utc),
    )

    db.add(attempt)
    db.commit()


def clear_login_attempts(
    db: Session,
    email: str,
    ip_address: str,
) -> None:
    db.execute(
        delete(LoginAttempt).where(
            LoginAttempt.email == email,
            LoginAttempt.ip_address == ip_address,
        )
    )

    db.commit()


def cleanup_old_login_attempts(
    db: Session,
) -> None:
    now = datetime.now(timezone.utc)

    window_start = now - timedelta(
        seconds=LOGIN_RATE_WINDOW_SECONDS,
    )

    db.execute(
        delete(LoginAttempt).where(
            LoginAttempt.attempted_at < window_start,
        )
    )

    db.commit()