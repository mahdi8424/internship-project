from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    require_project_member,
    require_project_owner,
    require_task_manager,
    require_task_status_changer,
    require_task_viewer,
)
from app.db.models import Project, ProjectMember, Task, User
from app.db.session import get_db
from app.schemas import (
    TaskCreate,
    TaskResponse,
    TaskStatus,
    TaskStatusUpdate,
    TaskUpdate,
)


project_tasks_router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["tasks"],
)

tasks_router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


def validate_assignee(
    db: Session,
    project_id: int,
    assignee_id: int | None,
) -> None:
    if assignee_id is None:
        return

    user = db.get(User, assignee_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee not found",
        )

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == assignee_id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be a member of the project",
        )


# =========================================================
# Create task
# admin: any project
# manager: own project
# member: forbidden
# =========================================================

@project_tasks_router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: int,
    data: TaskCreate,
    current_user: User = Depends(require_project_owner),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    validate_assignee(
        db,
        project_id,
        data.assignee_id,
    )

    task = Task(
        project_id=project_id,
        title=data.title,
        description=data.description,
        status=data.status,
        assignee_id=data.assignee_id,
        created_by=current_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


# =========================================================
# List tasks
# admin: any project
# manager: own project or member
# member: member only
# =========================================================

@project_tasks_router.get(
    "",
    response_model=list[TaskResponse],
)
def list_tasks(
    project_id: int,
    status_filter: TaskStatus | None = Query(
        default=None,
        alias="status",
    ),
    assignee_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_project_member),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    query = select(Task).where(
        Task.project_id == project_id
    )

    if status_filter is not None:
        query = query.where(
            Task.status == status_filter
        )

    if assignee_id is not None:
        query = query.where(
            Task.assignee_id == assignee_id
        )

    query = (
        query
        .order_by(Task.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return db.scalars(query).all()


# =========================================================
# Get task
# admin: any task
# manager: own project or member
# member: member only
# =========================================================

@tasks_router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    current_user: User = Depends(require_task_viewer),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


# =========================================================
# Modify task
# admin: any task
# manager: own project
# member: forbidden
# =========================================================

@tasks_router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(require_task_manager),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    updates = data.model_dump(exclude_unset=True)

    if "assignee_id" in updates:
        validate_assignee(
            db,
            task.project_id,
            updates["assignee_id"],
        )

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


# =========================================================
# Change task status
# admin: any task
# manager: own project
# member: member of project
# =========================================================

@tasks_router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
)
def update_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    current_user: User = Depends(require_task_status_changer),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task.status = data.status

    db.commit()
    db.refresh(task)

    return task


# =========================================================
# Delete task
# admin: any task
# manager: own project
# member: forbidden
# =========================================================

@tasks_router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    current_user: User = Depends(require_task_manager),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()