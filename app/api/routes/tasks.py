from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    require_project_member,
    require_task_access,
)
from app.db.models import (
    Project,
    ProjectMember,
    Task,
    User,
)
from app.db.session import get_db
from app.schemas import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)


router = APIRouter(
    prefix="/projects/{project_id}/tasks",
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

@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: int,
    data: TaskCreate,
    current_user: User = Depends(require_project_member),
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

@router.get(
    "",
    response_model=list[TaskResponse],
)
def list_tasks(
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

    return db.scalars(
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.id)
    ).all()

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    project_id: int,
    task_id: int,
    current_user: User = Depends(require_task_access),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None or task.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    project_id: int,
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(require_task_access),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None or task.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if data.assignee_id is not None:
        validate_assignee(
            db,
            project_id,
            data.assignee_id,
        )

    updates = data.model_dump(exclude_unset=True)

    if "assignee_id" in updates:
        validate_assignee(
            db,
            project_id,
            updates["assignee_id"],
        )

    for field, value in updates.items():
        setattr(task, field, value)

    if data.title is not None:
        task.title = data.title

    if data.description is not None:
        task.description = data.description

    if data.status is not None:
        task.status = data.status

    if data.assignee_id is not None:
        task.assignee_id = data.assignee_id

    db.commit()
    db.refresh(task)

    return task

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    project_id: int,
    task_id: int,
    current_user: User = Depends(require_task_access),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None or task.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()