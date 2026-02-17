"""Nano Banana image generation provider via kie.ai async task API."""

from __future__ import annotations

import asyncio
import json
from io import BytesIO
from typing import Optional

import structlog
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

from paperbanana.providers.base import ImageGenProvider

logger = structlog.get_logger()

# Polling configuration
_INITIAL_DELAY = 2.0  # seconds before first poll
_POLL_INTERVAL = 3.0  # seconds between polls
_POLL_TIMEOUT = 300.0  # 5 minutes max


class NanoBananaImageGen(ImageGenProvider):
    """Image generation via kie.ai Nano Banana async task API.

    Flow: POST createTask -> poll recordInfo -> download result image.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "google/nano-banana",
    ):
        self._api_key = api_key
        self._model = model
        self._client = None

    @property
    def name(self) -> str:
        return "nanobanana"

    @property
    def model_name(self) -> str:
        return self._model

    def _get_client(self):
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url="https://api.kie.ai/api/v1",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    def is_available(self) -> bool:
        return self._api_key is not None

    def _image_size(self, width: int, height: int) -> str:
        ratio = width / height
        if ratio > 2.0:
            return "21:9"
        if ratio > 1.5:
            return "16:9"
        if ratio > 1.3:
            return "3:2"
        if ratio > 1.15:
            return "5:4"
        if ratio > 0.87:
            return "1:1"
        if ratio > 0.77:
            return "4:5"
        if ratio > 0.67:
            return "3:4"
        if ratio > 0.5:
            return "2:3"
        return "9:16"

    async def _create_task(self, prompt: str, width: int, height: int) -> str:
        """Submit an image generation task and return the task ID."""
        client = self._get_client()
        payload = {
            "model": self._model,
            "input": {
                "prompt": prompt,
                "output_format": "png",
                "image_size": self._image_size(width, height),
            },
        }
        response = await client.post("/jobs/createTask", json=payload)
        response.raise_for_status()
        data = response.json()

        task_id = data.get("data", {}).get("taskId")
        if not task_id:
            raise ValueError(f"No taskId in createTask response: {data}")

        logger.debug("NanoBanana task created", task_id=task_id)
        return task_id

    async def _poll_task(self, task_id: str) -> list[str]:
        """Poll until the task completes and return result URLs."""
        client = self._get_client()
        await asyncio.sleep(_INITIAL_DELAY)

        elapsed = _INITIAL_DELAY
        while elapsed < _POLL_TIMEOUT:
            response = await client.get("/jobs/recordInfo", params={"taskId": task_id})
            response.raise_for_status()
            data = response.json()

            record = data.get("data", data)
            state = record.get("state", "").lower()

            if state == "success":
                result_json_str = record.get("resultJson", "")
                try:
                    result_obj = json.loads(result_json_str) if result_json_str else {}
                except (json.JSONDecodeError, TypeError):
                    result_obj = {}
                urls = result_obj.get("resultUrls", [])
                if not urls:
                    raise ValueError(f"Task succeeded but no result URLs: {record}")
                logger.debug("NanoBanana task completed", task_id=task_id, urls=len(urls))
                return urls

            if state == "fail":
                error_msg = record.get("failMsg") or record.get("failCode") or "Unknown error"
                raise RuntimeError(f"NanoBanana task failed: {error_msg}")

            logger.debug(
                "NanoBanana task pending",
                task_id=task_id,
                state=state,
                elapsed=elapsed,
            )
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

        raise TimeoutError(f"NanoBanana task {task_id} timed out after {_POLL_TIMEOUT}s")

    async def _download_image(self, url: str) -> Image.Image:
        """Download an image from a URL and return as PIL Image."""
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as dl_client:
            response = await dl_client.get(url)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
    ) -> Image.Image:
        if negative_prompt:
            prompt = f"{prompt}\n\nAvoid: {negative_prompt}"

        task_id = await self._create_task(prompt, width, height)
        urls = await self._poll_task(task_id)
        image = await self._download_image(urls[0])

        logger.info(
            "NanoBanana image generated",
            model=self._model,
            task_id=task_id,
            size=f"{image.width}x{image.height}",
        )
        return image
