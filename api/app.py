"""FastAPI application for PaperBanana HTTP API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from paperbanana.core.config import Settings

from .schemas import GenerateRequest, TaskCreateResponse, TaskResponse, TaskStatus
from .tasks import TaskManager

logger = structlog.get_logger()


def _patch_genai_aclose():
    """Monkey-patch google-genai BaseApiClient.aclose to suppress
    '_async_httpx_client' AttributeError during garbage collection."""
    try:
        from google.genai import _api_client

        _original_aclose = _api_client.BaseApiClient.aclose

        async def _safe_aclose(self):
            try:
                await _original_aclose(self)
            except AttributeError:
                pass

        _api_client.BaseApiClient.aclose = _safe_aclose
    except Exception:
        pass


_patch_genai_aclose()

_task_manager: TaskManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize settings and task manager on startup."""
    import os

    global _task_manager

    # Debug: check if env vars reach the container
    logger.info(
        "ENV diagnostics",
        APICORE_API_KEY_set=bool(os.environ.get("APICORE_API_KEY")),
        KIE_API_KEY_set=bool(os.environ.get("KIE_API_KEY")),
        VLM_PROVIDER=os.environ.get("VLM_PROVIDER"),
        env_file_exists=Path(".env").exists(),
    )

    settings = Settings()
    _task_manager = TaskManager(settings)

    # Ensure outputs directory exists
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)

    logger.info(
        "API started",
        vlm_provider=settings.vlm_provider,
        image_provider=settings.image_provider,
        settings=repr(settings),
    )
    yield
    logger.info("API shutting down")


app = FastAPI(
    title="PaperBanana API",
    description="Generate publication-quality academic diagrams from text descriptions",
    version="0.1.2",
    lifespan=lifespan,
)

# Mount outputs directory for static file serving
outputs_dir = Path("outputs")
outputs_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")


@app.get("/")
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/v1/generate", response_model=TaskCreateResponse, status_code=202)
async def create_generation_task(request: GenerateRequest):
    """Submit a new diagram generation task.

    Returns immediately with a task ID. Poll the status URL for progress.
    """
    assert _task_manager is not None
    task_id = _task_manager.submit(request)
    return TaskCreateResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        status_url=f"/api/v1/tasks/{task_id}",
    )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """Get the status of a generation task."""
    assert _task_manager is not None
    state = _task_manager.get(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return TaskResponse(
        task_id=state.task_id,
        status=state.status,
        created_at=state.created_at,
        completed_at=state.completed_at,
        progress=state.progress,
        result=state.result,
        error=state.error,
    )


@app.get("/api/v1/tasks/{task_id}/image")
async def get_task_image(task_id: str):
    """Download the generated image for a completed task."""
    assert _task_manager is not None
    state = _task_manager.get(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if state.status != TaskStatus.COMPLETED or state.result is None:
        raise HTTPException(status_code=409, detail="Task has not completed successfully")

    # The image path is in the metadata from the pipeline output
    image_path = state.result.metadata.get("image_path")
    if image_path is None:
        # Fall back to the outputs directory with run_id
        image_path = str(Path("outputs") / state.result.run_id / "final_output.png")

    path = Path(image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(
        path=str(path),
        media_type="image/png",
        filename=f"{state.task_id}.png",
    )
