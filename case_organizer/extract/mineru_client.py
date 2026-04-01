"""Async MinerU API client."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass(slots=True)
class MinerUBatchSubmission:
    batch_id: str


@dataclass(slots=True)
class MinerUTaskResult:
    task_id: str


class MinerUClient:
    """Small wrapper around the MinerU API surface used by case-organizer."""

    def __init__(self, settings):
        self.settings = settings
        self.http = httpx.AsyncClient()

    async def get_presigned_urls(self, files: list[dict], model_version: str = "vlm") -> dict:
        headers = {
            "Authorization": f"Bearer {self.settings.mineru_api_token}",
            "Content-Type": "application/json",
        }
        payload = {"files": files, "model_version": model_version}
        response = await self.http.post(
            self.settings.mineru_file_urls_endpoint,
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    async def put_upload(self, put_url: str, path: str) -> None:
        data = Path(path).read_bytes()
        response = await self.http.put(put_url, content=data, timeout=None)
        response.raise_for_status()

    async def submit_batch_task_by_url(self, files: list[dict], model_version: str = "vlm") -> MinerUBatchSubmission:
        headers = {
            "Authorization": f"Bearer {self.settings.mineru_api_token}",
            "Content-Type": "application/json",
        }
        payload = {"files": files, "model_version": model_version}
        response = await self.http.post(
            self.settings.mineru_extract_batch_endpoint,
            json=payload,
            headers=headers,
            timeout=60,
        )
        data = response.json()
        batch_id = data.get("data", {}).get("batch_id")
        if response.status_code == 200 and data.get("code") == 0 and batch_id:
            return MinerUBatchSubmission(batch_id=batch_id)
        raise RuntimeError(f"MinerU batch submission failed: {data}")

    async def submit_single_task(self, url: str, model_version: str = "vlm", **kwargs) -> MinerUTaskResult:
        headers = {
            "Authorization": f"Bearer {self.settings.mineru_api_token}",
            "Content-Type": "application/json",
        }
        payload = {"url": url, "model_version": model_version, **kwargs}
        api_url = self.settings.mineru_extract_batch_endpoint.replace("/batch", "")
        response = await self.http.post(api_url, json=payload, headers=headers, timeout=60)
        data = response.json()
        task_id = data.get("data", {}).get("task_id")
        if response.status_code == 200 and data.get("code") == 0 and task_id:
            return MinerUTaskResult(task_id=task_id)
        raise RuntimeError(f"MinerU single task submission failed: {data}")

    async def get_single_task_result(self, task_id: str) -> dict:
        url = f"{self.settings.mineru_results_base}/extract/task/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.settings.mineru_api_token}",
            "Content-Type": "application/json",
        }
        response = await self.http.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()

    async def get_batch_results(self, batch_id: str) -> dict:
        url = f"{self.settings.mineru_results_base}/extract-results/batch/{batch_id}"
        headers = {
            "Authorization": f"Bearer {self.settings.mineru_api_token}",
            "Content-Type": "application/json",
        }
        response = await self.http.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self.http.aclose()
