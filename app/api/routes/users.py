from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.models import User
from app.db.session import get_db
from app.schemas import UserResponse, UserUpdate


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "",
    response_model=list[UserResponse],
)
def list_users(
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(User).order_by(User.id)
    ).all()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updates = data.model_dump(exclude_unset=True)

    # Prevent an administrator from accidentally
    # locking themselves out.
    if user.id == current_user.id:
        if updates.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account",
            )

        if updates.get("role") not in (None, "admin"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove your own admin role",
            )

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user