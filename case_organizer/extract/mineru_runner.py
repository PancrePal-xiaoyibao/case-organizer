"""MinerU orchestration helpers."""

from __future__ import annotations

import asyncio
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Any

import httpx

from case_organizer.extract.mineru_client import MinerUClient

logger = logging.getLogger("case_organizer.mineru")


def build_file_list(input_dir: Path) -> list[dict[str, str]]:
    """Construct the payload MinerU expects for batch uploads."""

    return [{"name": path.name} for path in sorted(input_dir.iterdir(), key=lambda item: item.name) if path.is_file()]


async def download_zip(url: str, output_dir: Path, filename: str = "result.zip") -> Path:
    async with httpx.AsyncClient() as http:
        response = await http.get(url, timeout=None)
        response.raise_for_status()
        output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = output_dir / filename
        zip_path.write_bytes(response.content)
        return zip_path


def unzip_to_keyword_dir(zip_path: Path, output_dir: Path) -> Path:
    target = output_dir / zip_path.stem
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(target)
    return target


async def poll_single_task_until_done(client: MinerUClient, task_id: str, interval_sec: int) -> dict[str, Any]:
    poll_count = 0
    while True:
        data = await client.get_single_task_result(task_id)
        poll_count += 1
        state = data.get("data", {}).get("state")
        if state == "done":
            return data
        if state == "failed":
            raise RuntimeError(f"MinerU task failed: {data.get('data', {}).get('err_msg', 'unknown error')}")
        if poll_count <= 2:
            logger.info("MinerU task poll #%s: %s", poll_count, data)
        await asyncio.sleep(interval_sec)


async def poll_batch_until_done(client: MinerUClient, batch_id: str, interval_sec: int) -> dict[str, Any]:
    poll_count = 0
    while True:
        data = await client.get_batch_results(batch_id)
        poll_count += 1
        extract_results = data.get("data", {}).get("extract_result", [])
        total = len(extract_results)
        done_count = sum(1 for item in extract_results if item.get("state") == "done")
        failed_count = sum(1 for item in extract_results if item.get("state") == "failed")
        if done_count + failed_count == total and total > 0:
            return data
        if poll_count <= 2:
            logger.info("MinerU batch poll #%s: %s", poll_count, data)
        await asyncio.sleep(interval_sec)


class MinerURunner:
    """High-level orchestration for MinerU extraction."""

    def __init__(self, settings):
        self.settings = settings

    async def run_local_file_upload(
        self,
        file_path: Path,
        output_dir: Path,
        model_version: str = "vlm",
    ) -> Path | None:
        """Upload one local file through the precise MinerU v4 batch flow."""

        client = MinerUClient(self.settings)
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            files = [{"name": file_path.name}]
            presign = await client.get_presigned_urls(files, model_version=model_version)
            batch_id = presign.get("data", {}).get("batch_id")
            file_urls = presign.get("data", {}).get("file_urls", [])
            if not batch_id or len(file_urls) != 1:
                raise RuntimeError(f"MinerU presign response invalid: {presign}")

            await client.put_upload(file_urls[0], str(file_path))

            result = await poll_batch_until_done(client, batch_id, self.settings.poll_interval_seconds)
            done_results = [
                item
                for item in result.get("data", {}).get("extract_result", [])
                if item.get("state") == "done" and item.get("full_zip_url")
            ]
            if not done_results:
                return None

            zip_path = await download_zip(done_results[0]["full_zip_url"], output_dir, "result.zip")
            extract_dir = unzip_to_keyword_dir(zip_path, output_dir)

            result_dir = extract_dir / "result"
            if result_dir.exists() and result_dir.is_dir():
                return extract_dir

            nested_dirs = [path for path in extract_dir.iterdir() if path.is_dir()]
            if len(nested_dirs) == 1:
                target = extract_dir / "result"
                if not target.exists():
                    shutil.move(str(nested_dirs[0]), str(target))
                return extract_dir

            return extract_dir
        finally:
            await client.close()

    async def run_single_task(self, file_url: str, output_dir: Path, model_version: str = "vlm") -> Path | None:
        client = MinerUClient(self.settings)
        try:
            task = await client.submit_single_task(file_url, model_version=model_version)
            result = await poll_single_task_until_done(client, task.task_id, self.settings.poll_interval_seconds)
            zip_url = result.get("data", {}).get("full_zip_url")
            if not zip_url:
                return None
            zip_path = await download_zip(zip_url, output_dir, "single_task_result.zip")
            return unzip_to_keyword_dir(zip_path, output_dir)
        finally:
            await client.close()

    async def run_batch_file_upload(self, input_dir: Path, output_dir: Path, model_version: str = "vlm") -> list[Path]:
        files = build_file_list(input_dir)
        if not files:
            return []

        client = MinerUClient(self.settings)
        try:
            presign = await client.get_presigned_urls(files, model_version=model_version)
            batch_id = presign.get("data", {}).get("batch_id")
            file_urls = presign.get("data", {}).get("file_urls", [])
            if not batch_id or not file_urls:
                raise RuntimeError(f"MinerU presign response invalid: {presign}")

            local_files = [path for path in sorted(input_dir.iterdir(), key=lambda item: item.name) if path.is_file()]
            for file_path, upload_url in zip(local_files, file_urls):
                await client.put_upload(upload_url, str(file_path))

            result = await poll_batch_until_done(client, batch_id, self.settings.poll_interval_seconds)
            output_dirs: list[Path] = []
            for idx, item in enumerate(result.get("data", {}).get("extract_result", [])):
                if item.get("state") != "done":
                    continue
                zip_url = item.get("full_zip_url")
                if not zip_url:
                    continue
                original_name = item.get("file_name", f"file_{idx}")
                zip_path = await download_zip(zip_url, output_dir, f"temp_{idx}_{original_name}.zip")
                output_dirs.append(unzip_to_keyword_dir(zip_path, output_dir))
                zip_path.unlink(missing_ok=True)
            return output_dirs
        finally:
            await client.close()
