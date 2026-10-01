from collections.abc import Callable

from fastapi import HTTPException, status
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.db.models import User, Project, ProjectMember, Task
from app.db.session import get_db


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive user",
        )

    return user


def require_roles(*allowed_roles: str):
    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency


def require_project_member(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if current_user.role == "admin":
        return current_user

    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if project.owner_id == current_user.id:
        return current_user

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    return current_user

def require_project_owner(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if current_user.role == "admin":
        return current_user

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this project",
        )

    return current_user

def require_task_access(
    project_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if current_user.role == "admin":
        return current_user

    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if project.owner_id == current_user.id:
        return current_user

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    task = db.get(Task, task_id)

    if task is None or task.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return current_user