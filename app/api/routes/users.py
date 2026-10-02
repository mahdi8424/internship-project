from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.models import User
from app.db.session import get_db
from app.schemas import (
    UserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
)


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
    "/{user_id}/role",
    response_model=UserResponse,
)
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
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

    # Prevent an administrator from removing
    # their own admin role.
    if user.id == current_user.id:
        if data.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove your own admin role",
            )

    user.role = data.role

    db.commit()
    db.refresh(user)

    return user


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
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

    # Prevent an administrator from deactivating
    # their own account.
    if user.id == current_user.id:
        if data.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account",
            )

    user.is_active = data.is_active

    db.commit()
    db.refresh(user)

    return user