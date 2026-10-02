from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    require_project_member,
    require_project_owner,
)
from app.db.models import Project, ProjectMember, User
from app.db.session import get_db
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)


router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project

@router.get(
    "",
    response_model=list[ProjectResponse],
)
def list_projects(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "admin":
        query = (
            select(Project)
            .order_by(Project.id)
        )
    else:
        owned_projects = select(Project.id).where(
            Project.owner_id == current_user.id
        )

        member_projects = (
            select(Project.id)
            .join(
                ProjectMember,
                ProjectMember.project_id == Project.id,
            )
            .where(
                ProjectMember.user_id == current_user.id
            )
        )

        project_ids = owned_projects.union(member_projects)

        query = (
            select(Project)
            .where(Project.id.in_(project_ids))
            .order_by(Project.id)
        )

    query = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return db.scalars(query).all()

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    current_user: User = Depends(require_project_member),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project

@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(require_project_owner),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if data.name is not None:
        project.name = data.name

    if data.description is not None:
        project.description = data.description

    db.commit()
    db.refresh(project)

    return project

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: int,
    current_user: User = Depends(require_project_owner),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    db.delete(project)
    db.commit()

@router.post(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(require_project_owner),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a project member",
        )

    membership = ProjectMember(
        project_id=project_id,
        user_id=user_id,
    )

    db.add(membership)
    db.commit()

    return {
        "message": "Member added successfully",
    }

@router.delete(
    "/{project_id}/members/{user_id}",
)
def remove_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(require_project_owner),
    db: Session = Depends(get_db),
):
    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project membership not found",
        )

    db.delete(membership)
    db.commit()

    return {
        "message": "Member removed successfully",
    }