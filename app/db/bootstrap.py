from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.password import hash_password
from app.db.models import User


def create_initial_admin(
    db: Session,
    email: str,
    password: str,
    full_name: str,
) -> None:
    existing_admin = db.scalar(
        select(User).where(User.role == "admin")
    )

    if existing_admin is not None:
        return

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is not None:
        existing_user.role = "admin"
        existing_user.is_active = True
    else:
        admin = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="admin",
            is_active=True,
        )
        db.add(admin)

    db.commit()