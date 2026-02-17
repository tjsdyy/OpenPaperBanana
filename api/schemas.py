"""Request and response schemas for the PaperBanana HTTP API."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request body for POST /api/v1/generate."""

    source_context: str = Field(description="Methodology text or paper excerpt")
    communicative_intent: str = Field(description="Figure caption / what to communicate")
    diagram_type: str = Field(default="methodology", description="methodology | statistical_plot")
    raw_data: Optional[dict[str, Any]] = Field(
        default=None, description="Raw data for statistical plots"
    )
    refinement_iterations: Optional[int] = Field(
        default=None, description="Override default refinement iterations"
    )


class TaskStatus(str, Enum):
    """Status of an async generation task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskResult(BaseModel):
    """Result payload when a task completes successfully."""

    image_url: str = Field(description="URL path to download the generated image")
    run_id: str
    description: str = Field(description="Final optimized description")
    total_iterations: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Response for GET /api/v1/tasks/{task_id}."""

    task_id: str
    status: TaskStatus
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    progress: Optional[str] = None
    result: Optional[TaskResult] = None
    error: Optional[str] = None


class TaskCreateResponse(BaseModel):
    """Response for POST /api/v1/generate (202 Accepted)."""

    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    status_url: str
