from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TaskStatus = Literal["todo", "in_progress", "done"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus = "todo"
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    status: TaskStatus | None = None

    assignee_id: int | None = None


class TaskResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    assignee_id: int | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)