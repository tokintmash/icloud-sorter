import asyncio
import logging
import os
import shutil
from pathlib import Path

from backend.services import state_service, icloud_service
from backend.config import load_settings

logger = logging.getLogger(__name__)


class SorterService:
    def __init__(self) -> None:
        self._running: bool = False
        self._status: str = "idle"
        self._total_files: int = 0
        self._completed_files: int = 0
        self._failed_files: int = 0
        self._current_file: str = ""
        self._current_album: str = ""
        self._errors: list[dict[str, str]] = []
        self._background_task: asyncio.Task[None] | None = None

    def start(self, album_ids: list[str]) -> dict:
        if self._running:
            return {"error": "sort_in_progress", "message": "A sort operation is already in progress"}

        if not icloud_service._is_authenticated():
            return {"error": "not_authenticated", "message": "Not authenticated. Please login first."}

        settings = load_settings()
        icloud_folder = settings.get("icloud_folder", "")

        if not icloud_folder or not Path(icloud_folder).is_dir():
            return {"error": "file_not_found", "message": "iCloud folder not found. Please configure it in settings."}

        # Fetch album metadata from iCloud (only selected albums)
        albums_result = icloud_service.get_albums()
        if isinstance(albums_result, dict) and "error" in albums_result:
            return albums_result

        folder_map = {a["id"]: a["folder_name"] for a in albums_result}
        sync_result = icloud_service.sync_album_metadata(folder_map, album_ids)
        if isinstance(sync_result, dict) and "error" in sync_result:
            return sync_result

        state_service.reset_album_files(album_ids)
        rows = state_service.get_pending_album_files(album_ids)

        if not rows:
            return {"error": "file_not_found", "message": "No files to sort for the selected albums. Fetch albums first."}

        self._reset_progress(len(rows))
        duplicate_handling = settings.get("duplicate_handling", "move_only")
        self._background_task = self._schedule_sort(rows, icloud_folder, duplicate_handling)
        return {"total_files": len(rows)}

    def _reset_progress(self, total_files: int) -> None:
        self._running = True
        self._status = "sorting"
        self._total_files = total_files
        self._completed_files = 0
        self._failed_files = 0
        self._current_file = ""
        self._current_album = ""
        self._errors = []

    def _schedule_sort(
        self,
        rows: list[dict[str, str]],
        icloud_folder: str,
        duplicate_handling: str,
    ) -> asyncio.Task[None]:
        task = asyncio.create_task(
            asyncio.to_thread(self._run_sort, rows, icloud_folder, duplicate_handling)
        )
        task.add_done_callback(self._clear_background_task)
        return task

    def _clear_background_task(self, task: asyncio.Task[None]) -> None:
        if self._background_task is task:
            self._background_task = None

    def _build_folder_map(self, rows: list[dict[str, str]]) -> dict[str, str]:
        folder_map: dict[str, str] = {}
        for row in rows:
            folder_name = row.get("folder_name")
            if folder_name:
                folder_map.setdefault(row["album_id"], folder_name)
        return folder_map

    def _build_file_index(self, root: Path) -> dict[str, list[Path]]:
        file_index: dict[str, list[Path]] = {}
        for entry in root.rglob("*"):
            if entry.is_file():
                file_index.setdefault(entry.name.casefold(), []).append(entry)
        return file_index

    def _set_current_item(self, filename: str, album_name: str) -> None:
        self._current_file = filename
        self._current_album = album_name

    def _target_dir(
        self,
        root: Path,
        album_id: str,
        album_name: str,
        folder_map: dict[str, str],
    ) -> Path:
        folder_name = folder_map.get(album_id, icloud_service._sanitize_folder_name(album_name))
        return root / folder_name

    def _record_sorted(self, album_id: str, filename: str) -> None:
        state_service.mark_album_file_sorted(album_id, filename)
        self._completed_files += 1

    def _record_failure(
        self,
        album_id: str,
        album_name: str,
        filename: str,
        message: str,
    ) -> None:
        state_service.mark_album_file_failed(album_id, filename, message)
        self._failed_files += 1
        self._errors.append({"filename": filename, "error": message, "album": album_name})

    def _existing_target_candidates(
        self,
        candidates: list[Path],
        target_dir: Path,
        claimed: set[Path],
        duplicate_handling: str,
    ) -> list[Path]:
        if duplicate_handling == "copy_to_each":
            return [candidate for candidate in candidates if candidate.parent == target_dir]
        return [
            candidate
            for candidate in candidates
            if candidate.parent == target_dir and candidate not in claimed
        ]

    def _claim_existing_target(
        self,
        album_id: str,
        filename: str,
        candidates: list[Path],
        target_dir: Path,
        claimed: set[Path],
        duplicate_handling: str,
    ) -> bool:
        in_target = self._existing_target_candidates(
            candidates,
            target_dir,
            claimed,
            duplicate_handling,
        )
        if not in_target:
            return False

        claimed.add(in_target[0])
        self._record_sorted(album_id, filename)
        return True

    def _allocate_target_path(self, target_dir: Path, source_name: str) -> Path:
        target_path = target_dir / source_name
        if not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        counter = 2
        while target_path.exists():
            target_path = target_dir / f"{stem} ({counter}){suffix}"
            counter += 1
        return target_path

    def _update_file_index(
        self,
        file_index: dict[str, list[Path]],
        source: Path,
        target_path: Path,
    ) -> None:
        key = source.name.casefold()
        if key in file_index:
            file_index[key] = [target_path if path == source else path for path in file_index[key]]

    def _move_file(
        self,
        source: Path,
        target_path: Path,
        file_index: dict[str, list[Path]],
    ) -> None:
        os.rename(str(source), str(target_path))
        self._update_file_index(file_index, source, target_path)

    def _copy_to_each(
        self,
        candidates: list[Path],
        target_dir: Path,
        claimed: set[Path],
        file_index: dict[str, list[Path]],
    ) -> None:
        source = candidates[0]
        target_path = self._allocate_target_path(target_dir, source.name)

        if source not in claimed:
            self._move_file(source, target_path, file_index)
            claimed.add(source)
            claimed.add(target_path)
            return

        shutil.copy2(str(source), str(target_path))

    def _move_only(
        self,
        album_id: str,
        album_name: str,
        filename: str,
        candidates: list[Path],
        target_dir: Path,
        claimed: set[Path],
        file_index: dict[str, list[Path]],
    ) -> bool:
        unclaimed = [candidate for candidate in candidates if candidate not in claimed]
        if not unclaimed:
            self._record_failure(
                album_id,
                album_name,
                filename,
                "Already moved to another album",
            )
            return False

        source = unclaimed[0]
        claimed.add(source)
        target_path = self._allocate_target_path(target_dir, source.name)
        self._move_file(source, target_path, file_index)
        claimed.add(target_path)
        return True

    def _handle_candidate(
        self,
        row: dict[str, str],
        candidates: list[Path],
        target_dir: Path,
        claimed: set[Path],
        duplicate_handling: str,
        file_index: dict[str, list[Path]],
    ) -> bool:
        if duplicate_handling == "copy_to_each":
            self._copy_to_each(candidates, target_dir, claimed, file_index)
            return True

        return self._move_only(
            row["album_id"],
            row["album_name"],
            row["filename"],
            candidates,
            target_dir,
            claimed,
            file_index,
        )

    def _process_row(
        self,
        row: dict[str, str],
        root: Path,
        folder_map: dict[str, str],
        file_index: dict[str, list[Path]],
        claimed: set[Path],
        duplicate_handling: str,
    ) -> None:
        album_id = row["album_id"]
        album_name = row["album_name"]
        filename = row["filename"]
        self._set_current_item(filename, album_name)

        target_dir = self._target_dir(root, album_id, album_name, folder_map)

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            candidates = file_index.get(filename.casefold(), [])

            if not candidates:
                self._record_failure(album_id, album_name, filename, "File not found")
                return

            if self._claim_existing_target(
                album_id,
                filename,
                candidates,
                target_dir,
                claimed,
                duplicate_handling,
            ):
                return

            if not self._handle_candidate(
                row,
                candidates,
                target_dir,
                claimed,
                duplicate_handling,
                file_index,
            ):
                return

            self._record_sorted(album_id, filename)

        except PermissionError as error:
            self._record_failure(
                album_id,
                album_name,
                filename,
                f"Permission denied: {error}",
            )
        except OSError as error:
            self._record_failure(album_id, album_name, filename, f"OS error: {error}")

    def _run_sort(self, rows: list[dict[str, str]], icloud_folder: str, duplicate_handling: str = "move_only") -> None:
        try:
            root = Path(icloud_folder)
            folder_map = self._build_folder_map(rows)
            file_index = self._build_file_index(root)
            claimed: set[Path] = set()

            for row in rows:
                self._process_row(
                    row,
                    root,
                    folder_map,
                    file_index,
                    claimed,
                    duplicate_handling,
                )

            self._status = "complete"
        except Exception as error:
            logger.exception("Fatal error during sort")
            self._status = "error"
            self._errors.append({"filename": "", "error": f"Fatal error: {error}", "album": ""})
        finally:
            self._running = False

    def get_progress(self) -> dict:
        return {
            "status": self._status,
            "total_files": self._total_files,
            "completed_files": self._completed_files,
            "failed_files": self._failed_files,
            "current_file": self._current_file,
            "current_album": self._current_album,
            "errors": self._errors,
        }

    def is_running(self) -> bool:
        return self._running


sorter_service = SorterService()
