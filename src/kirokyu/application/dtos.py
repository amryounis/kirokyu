"""Data Transfer Objects for use-case boundaries (Decision 15).

DTOs carry data into and out of use cases. They are Pydantic models
because validation at the boundary is exactly what Pydantic is for.

The domain layer knows nothing about these types — they live here in
application and translate between the domain's rich types and the flat
data that callers (CLI, API, tests) naturally produce.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator

from kirokyu.domain.value_objects import Priority, TaskStatus


class CreateTaskInput(BaseModel):
    """Input for the CreateTask use case."""

    title: str = Field(..., min_length=1)
    description: str = Field(default="")
    priority: Priority = Field(default=Priority.MEDIUM)
    due_date: date | None = Field(default=None)
    starred: bool = Field(default=False)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip()


class UpdateTaskInput(BaseModel):
    """Input for the UpdateTask use case.

    All fields are optional — only provided fields are applied.
    """

    title: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None)
    priority: Priority | None = Field(default=None)
    due_date: date | None = Field(default=None)
    clear_due_date: bool = Field(default=False)
    starred: bool | None = Field(default=None)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip() if v else v


class TaskOutput(BaseModel):
    """Read-side projection of a Task, safe to expose to any caller."""

    id: str
    title: str
    description: str
    priority: Priority
    status: TaskStatus
    due_date: date | None
    starred: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
