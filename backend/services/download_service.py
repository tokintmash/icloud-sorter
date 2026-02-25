import asyncio
import json
import logging
import os
import shutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock
from typing import Any

from backend.config import (
    DEFAULT_CONCURRENT_DOWNLOADS,
    DEFAULT_DOWNLOAD_PATH,
    DEFAULT_MAX_RETRIES,
    DEFAULT_METADATA_DELAY_MS,
    SETTINGS_PATH,
)
from backend.services import icloud_service, state_service

logger = logging.getLogger(__name__)

MIN_DISK_SPACE_BYTES = 500 * 1024 * 1024  # 500 MB
DISK_CHECK_INTERVAL_FILES = 100
DISK_CHECK_INTERVAL_BYTES = 1 * 1024 * 1024 * 1024  # 1 GB


class DownloadService:
    def __init__(self) -> None:
        self._executor: ThreadPoolExecutor | None = None
        self._paused = Event()
        self._paused.set()  # Start in running state (set = running)
        self._cancelled = False
        self._lock = Lock()
        self._job_id: str | None = None
        self._album_ids: list[str] = []
        self._download_path: str = ""
        self._running = False
        self._status: str = "idle"

        # Progress tracking
        self._total_assets: int = 0
        self._completed_assets: int = 0
        self._failed_assets: int = 0
        self._skipped_assets: int = 0
        self._bytes_downloaded: int = 0
        self._bytes_total: int = 0
        self._current_file: str = ""
        self._current_album: str = ""
        self._errors: list[dict[str, Any]] = []

        # Speed tracking
        self._speed_start_time: float = 0.0
        self._speed_bytes_start: int = 0

        # Settings
        self._concurrent_downloads: int = DEFAULT_CONCURRENT_DOWNLOADS
        self._max_retries: int = DEFAULT_MAX_RETRIES
        self._metadata_delay_ms: int = DEFAULT_METADATA_DELAY_MS

        # Disk check tracking
        self._files_since_disk_check: int = 0
        self._bytes_since_disk_check: int = 0

    def _load_settings(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "download_path": DEFAULT_DOWNLOAD_PATH,
            "concurrent_downloads": DEFAULT_CONCURRENT_DOWNLOADS,
            "metadata_delay_ms": DEFAULT_METADATA_DELAY_MS,
            "max_retries": DEFAULT_MAX_RETRIES,
        }
        if SETTINGS_PATH.exists():
            try:
                with open(SETTINGS_PATH, "r") as f:
                    stored = json.load(f)
                defaults.update(stored)
            except (json.JSONDecodeError, OSError):
                pass
        return defaults

    def start(self, album_ids: list[str], download_path: str) -> dict[str, Any]:
        if self._running:
            return {
                "error": "download_in_progress",
                "message": "A download is already in progress",
            }

        if not icloud_service._is_authenticated():
            return {
                "error": "not_authenticated",
                "message": "Not authenticated. Please login first.",
            }

        settings = self._load_settings()
        self._concurrent_downloads = int(settings.get("concurrent_downloads", DEFAULT_CONCURRENT_DOWNLOADS))
        self._max_retries = int(settings.get("max_retries", DEFAULT_MAX_RETRIES))
        self._metadata_delay_ms = int(settings.get("metadata_delay_ms", DEFAULT_METADATA_DELAY_MS))

        total_assets = 0
        estimated_bytes = 0

        for album_id in album_ids:
            assets_result = icloud_service.get_album_assets(album_id, 0, 99999)
            if "error" in assets_result:
                return assets_result

            assets = assets_result["assets"]
            count = state_service.create_download_records(album_id, assets, "original")
            total_assets += len(assets)

            for asset in assets:
                estimated_bytes += asset.get("size_bytes", 0)

        if total_assets == 0:
            return {
                "error": "not_found",
                "message": "No assets found in the selected albums",
            }

        # Disk space check
        dl_path = Path(download_path)
        dl_path.mkdir(parents=True, exist_ok=True)
        disk_usage = shutil.disk_usage(str(dl_path))
        if disk_usage.free < estimated_bytes:
            return {
                "error": "insufficient_disk_space",
                "message": "Not enough disk space for the download",
                "required_bytes": estimated_bytes,
                "available_bytes": disk_usage.free,
            }

        # Reset state
        self._job_id = str(uuid.uuid4())
        self._album_ids = album_ids
        self._download_path = download_path
        self._running = True
        self._cancelled = False
        self._paused.set()
        self._status = "downloading"
        self._total_assets = total_assets
        self._completed_assets = 0
        self._failed_assets = 0
        self._skipped_assets = 0
        self._bytes_downloaded = 0
        self._bytes_total = estimated_bytes
        self._current_file = ""
        self._current_album = ""
        self._errors = []
        self._speed_start_time = time.monotonic()
        self._speed_bytes_start = 0
        self._files_since_disk_check = 0
        self._bytes_since_disk_check = 0

        # Start background download task
        loop = asyncio.get_event_loop()
        loop.create_task(self._run_downloads())

        return {
            "job_id": self._job_id,
            "total_assets": total_assets,
            "estimated_bytes": estimated_bytes,
        }

    async def _run_downloads(self) -> None:
        try:
            pending = state_service.get_pending_downloads(self._album_ids)
            self._executor = ThreadPoolExecutor(max_workers=self._concurrent_downloads)

            # Clean up leftover .tmp files
            self._cleanup_tmp_files()

            loop = asyncio.get_event_loop()

            for record in pending:
                if self._cancelled:
                    break

                # Wait while paused
                while not self._paused.is_set():
                    if self._cancelled:
                        break
                    await asyncio.sleep(0.1)

                if self._cancelled:
                    break

                await loop.run_in_executor(self._executor, self._download_one, record)

                # Periodic disk space check
                with self._lock:
                    self._files_since_disk_check += 1

                if self._files_since_disk_check >= DISK_CHECK_INTERVAL_FILES or \
                   self._bytes_since_disk_check >= DISK_CHECK_INTERVAL_BYTES:
                    self._check_disk_space()

            # Determine final status
            with self._lock:
                if self._cancelled:
                    self._status = "cancelled"
                elif self._failed_assets > 0 and self._completed_assets == 0:
                    self._status = "error"
                else:
                    self._status = "complete"

        except Exception:
            logger.exception("Error in download loop")
            with self._lock:
                self._status = "error"
        finally:
            self._running = False
            if self._executor:
                self._executor.shutdown(wait=False)
                self._executor = None

    def _cleanup_tmp_files(self) -> None:
        dl_path = Path(self._download_path)
        if not dl_path.exists():
            return
        for tmp_file in dl_path.rglob(".*.tmp"):
            try:
                tmp_file.unlink()
                logger.info("Cleaned up tmp file: %s", tmp_file)
            except OSError:
                logger.warning("Failed to clean up tmp file: %s", tmp_file)

    def _check_disk_space(self) -> None:
        try:
            disk_usage = shutil.disk_usage(self._download_path)
            if disk_usage.free < MIN_DISK_SPACE_BYTES:
                logger.warning("Low disk space: %d bytes remaining, pausing downloads", disk_usage.free)
                with self._lock:
                    self._status = "paused"
                self._paused.clear()
        except OSError:
            logger.exception("Error checking disk space")
        finally:
            with self._lock:
                self._files_since_disk_check = 0
                self._bytes_since_disk_check = 0

    def _download_one(self, record: dict[str, Any]) -> None:
        asset_id = record["asset_id"]
        album_id = record["album_id"]
        version = record["version"]

        # Get album folder name
        folder_name = state_service.get_album_folder_name(album_id)
        if not folder_name:
            folder_name = "Unknown Album"

        with self._lock:
            self._current_album = folder_name

        target_dir = Path(self._download_path) / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        # Update status to downloading
        state_service.update_download_status(
            asset_id, album_id, version, "downloading"
        )

        # Check cross-album copy optimization
        existing_path = state_service.get_completed_download_path(asset_id, version)
        if existing_path and Path(existing_path).exists():
            try:
                # Get filename from existing path
                src_filename = Path(existing_path).name
                final_name = self._resolve_filename(target_dir, src_filename, "")
                final_path = target_dir / final_name

                shutil.copy2(str(existing_path), str(final_path))
                file_size = final_path.stat().st_size

                state_service.update_download_status(
                    asset_id, album_id, version, "complete",
                    local_path=str(final_path),
                    file_size=file_size,
                    bytes_downloaded=file_size,
                )
                with self._lock:
                    self._completed_assets += 1
                    self._bytes_downloaded += file_size
                    self._bytes_since_disk_check += file_size
                return
            except Exception:
                logger.warning("Cross-album copy failed for %s, will download instead", asset_id)

        # Get asset from iCloud
        album_obj = icloud_service.get_album_by_id(album_id)
        if album_obj is None:
            self._handle_download_failure(
                asset_id, album_id, version, record,
                "Album not found in iCloud"
            )
            return

        asset = icloud_service.get_asset_from_album(album_obj, asset_id)
        if asset is None:
            self._handle_download_failure(
                asset_id, album_id, version, record,
                "Asset not found in album"
            )
            return

        filename = getattr(asset, "filename", None) or f"{asset_id}.dat"
        with self._lock:
            self._current_file = filename

        # Metadata delay
        if self._metadata_delay_ms > 0:
            time.sleep(self._metadata_delay_ms / 1000.0)

        # Download with retry
        attempts = record.get("attempts", 0)
        max_attempts = self._max_retries
        last_error = ""

        for attempt in range(attempts, max_attempts):
            if self._cancelled:
                return

            # Wait while paused
            while not self._paused.is_set():
                if self._cancelled:
                    return
                time.sleep(0.1)

            try:
                result = icloud_service.download_asset_data(asset, version)
                if result is None:
                    last_error = "Download returned no data"
                    continue

                data, data_size = result

                # Resolve filename
                final_name = self._resolve_filename(
                    target_dir, filename,
                    getattr(asset, "created", None)
                )
                final_path = target_dir / final_name
                tmp_path = target_dir / f".{final_name}.tmp"

                # Write to temp file
                with open(tmp_path, "wb") as f:
                    f.write(data)

                # Verify size
                written_size = tmp_path.stat().st_size
                if written_size != data_size:
                    tmp_path.unlink(missing_ok=True)
                    last_error = f"Size mismatch: expected {data_size}, got {written_size}"
                    continue

                # Atomic rename
                os.rename(str(tmp_path), str(final_path))

                # Update state
                state_service.update_download_status(
                    asset_id, album_id, version, "complete",
                    local_path=str(final_path),
                    file_size=data_size,
                    bytes_downloaded=data_size,
                )
                with self._lock:
                    self._completed_assets += 1
                    self._bytes_downloaded += data_size
                    self._bytes_since_disk_check += data_size
                return

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Download attempt %d/%d failed for %s: %s",
                    attempt + 1, max_attempts, asset_id, last_error,
                )
                # Exponential backoff for retries
                if attempt < max_attempts - 1:
                    backoff = min(30 * (2 ** attempt), 300)
                    time.sleep(backoff)

        # All attempts exhausted
        self._handle_download_failure(
            asset_id, album_id, version, record, last_error
        )

    def _handle_download_failure(
        self,
        asset_id: str,
        album_id: str,
        version: str,
        record: dict[str, Any],
        error_message: str,
    ) -> None:
        state_service.update_download_status(
            asset_id, album_id, version, "failed",
            error_message=error_message,
        )
        with self._lock:
            self._failed_assets += 1
            self._errors.append({
                "asset_id": asset_id,
                "filename": self._current_file or asset_id,
                "error": error_message,
                "attempts": record.get("attempts", 0) + 1,
            })

    def _resolve_filename(self, target_dir: Path, filename: str, asset_created_at: Any) -> str:
        if not (target_dir / filename).exists():
            return filename

        stem = Path(filename).stem
        suffix = Path(filename).suffix

        # First collision: append date
        date_str = ""
        if asset_created_at:
            if isinstance(asset_created_at, str) and asset_created_at:
                date_str = asset_created_at[:10]
            elif hasattr(asset_created_at, "strftime"):
                date_str = asset_created_at.strftime("%Y-%m-%d")

        if date_str:
            dated_name = f"{stem}_{date_str}{suffix}"
            if not (target_dir / dated_name).exists():
                return dated_name
            # Further collisions: append sequence number
            counter = 2
            while True:
                seq_name = f"{stem}_{date_str} ({counter}){suffix}"
                if not (target_dir / seq_name).exists():
                    return seq_name
                counter += 1
        else:
            # No date available, use sequence numbers
            counter = 2
            while True:
                seq_name = f"{stem} ({counter}){suffix}"
                if not (target_dir / seq_name).exists():
                    return seq_name
                counter += 1

    def get_progress(self) -> dict[str, Any]:
        with self._lock:
            elapsed = time.monotonic() - self._speed_start_time if self._speed_start_time else 0
            speed = int(self._bytes_downloaded / elapsed) if elapsed > 1 else 0
            remaining = self._bytes_total - self._bytes_downloaded
            eta = int(remaining / speed) if speed > 0 else 0

            return {
                "status": self._status,
                "total_assets": self._total_assets,
                "completed_assets": self._completed_assets,
                "failed_assets": self._failed_assets,
                "skipped_assets": self._skipped_assets,
                "bytes_downloaded": self._bytes_downloaded,
                "bytes_total": self._bytes_total,
                "current_file": self._current_file,
                "current_album": self._current_album,
                "speed_bytes_per_sec": speed,
                "eta_seconds": eta,
                "errors": list(self._errors),
            }

    def pause(self) -> None:
        self._paused.clear()
        with self._lock:
            self._status = "paused"

    def resume(self) -> None:
        self._paused.set()
        with self._lock:
            self._status = "downloading"

    def cancel(self) -> None:
        self._cancelled = True
        self._paused.set()  # Unblock any paused state so workers can exit
        with self._lock:
            self._status = "cancelled"

        # Mark remaining pending as skipped
        state_service.mark_remaining_pending_as_skipped(self._album_ids)

        # Clean up .tmp files
        self._cleanup_tmp_files()

        # Update skipped count
        stats = state_service.get_download_stats(self._album_ids)
        with self._lock:
            self._skipped_assets = stats.get("skipped", 0)

    def is_running(self) -> bool:
        return self._running


download_service = DownloadService()
