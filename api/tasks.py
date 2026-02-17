"""Async task manager for PaperBanana generation jobs."""

from __future__ import annotations

import asyncio
import datetime
import uuid
from typing import Optional

import structlog

from paperbanana.core.config import Settings
from paperbanana.core.pipeline import PaperBananaPipeline
from paperbanana.core.types import DiagramType, GenerationInput

from .schemas import GenerateRequest, TaskResult, TaskStatus

logger = structlog.get_logger()

_MAX_CONCURRENT = 3


def _cleanup_genai_client(pipeline: PaperBananaPipeline) -> None:
    """Eagerly close the google-genai sync httpx client to suppress spurious
    ``_async_httpx_client`` errors during garbage collection."""
    try:
        for provider in (getattr(pipeline, "_vlm", None), getattr(pipeline, "_image_gen", None)):
            client = getattr(provider, "_client", None)
            if client is None:
                continue
            api_client = getattr(client, "_api_client", None)
            if api_client is None:
                continue
            httpx_client = getattr(api_client, "_httpx_client", None)
            if httpx_client is not None:
                httpx_client.close()
            # Prevent aclose() from failing on a missing attr
            if not hasattr(api_client, "_async_httpx_client"):
                api_client._async_httpx_client = None
    except Exception:
        pass


class TaskState:
    """Mutable state for a single generation task."""

    def __init__(self, task_id: str, request: GenerateRequest):
        self.task_id = task_id
        self.request = request
        self.status: TaskStatus = TaskStatus.PENDING
        self.created_at: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.completed_at: Optional[datetime.datetime] = None
        self.progress: Optional[str] = None
        self.result: Optional[TaskResult] = None
        self.error: Optional[str] = None


class TaskManager:
    """Manages async generation tasks with concurrency control."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._tasks: dict[str, TaskState] = {}
        self._semaphore = asyncio.Semaphore(_MAX_CONCURRENT)

    def submit(self, request: GenerateRequest) -> str:
        """Create a new task and schedule it for background execution."""
        task_id = uuid.uuid4().hex[:12]
        state = TaskState(task_id=task_id, request=request)
        self._tasks[task_id] = state
        asyncio.create_task(self._execute(state))
        logger.info("Task submitted", task_id=task_id)
        return task_id

    def get(self, task_id: str) -> Optional[TaskState]:
        """Look up a task by ID."""
        return self._tasks.get(task_id)

    async def _execute(self, state: TaskState) -> None:
        """Run the pipeline for a single task under semaphore control."""
        async with self._semaphore:
            state.status = TaskStatus.RUNNING
            state.progress = "Initializing pipeline"
            logger.info("Task started", task_id=state.task_id)

            try:
                # Build settings with optional iteration override
                settings = self._settings
                if state.request.refinement_iterations is not None:
                    settings = settings.model_copy(
                        update={"refinement_iterations": state.request.refinement_iterations}
                    )

                pipeline = PaperBananaPipeline(settings=settings)

                diagram_type = DiagramType(state.request.diagram_type)
                gen_input = GenerationInput(
                    source_context=state.request.source_context,
                    communicative_intent=state.request.communicative_intent,
                    diagram_type=diagram_type,
                    raw_data=state.request.raw_data,
                )

                def on_progress(msg: str):
                    state.progress = msg

                state.progress = "Running generation pipeline"
                output = await pipeline.generate(gen_input, progress_callback=on_progress)

                state.result = TaskResult(
                    image_url=f"/api/v1/tasks/{state.task_id}/image",
                    run_id=pipeline.run_id,
                    description=output.description,
                    total_iterations=len(output.iterations),
                    metadata=output.metadata,
                )
                state.status = TaskStatus.COMPLETED
                state.completed_at = datetime.datetime.now(datetime.timezone.utc)
                state.progress = None
                logger.info(
                    "Task completed",
                    task_id=state.task_id,
                    run_id=pipeline.run_id,
                )

                _cleanup_genai_client(pipeline)

            except Exception as exc:
                state.status = TaskStatus.FAILED
                state.error = str(exc)
                state.completed_at = datetime.datetime.now(datetime.timezone.utc)
                state.progress = None
                logger.error(
                    "Task failed",
                    task_id=state.task_id,
                    error=str(exc),
                    exc_info=True,
                )

                if "pipeline" in locals():
                    _cleanup_genai_client(pipeline)
