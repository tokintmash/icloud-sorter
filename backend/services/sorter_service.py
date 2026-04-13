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

        self._running = True
        self._status = "sorting"
        self._total_files = len(rows)
        self._completed_files = 0
        self._failed_files = 0
        self._current_file = ""
        self._current_album = ""
        self._errors = []

        duplicate_handling = settings.get("duplicate_handling", "move_only")
        asyncio.create_task(asyncio.to_thread(self._run_sort, rows, icloud_folder, duplicate_handling))
        return {"total_files": len(rows)}

    def _run_sort(self, rows: list[dict[str, str]], icloud_folder: str, duplicate_handling: str = "move_only") -> None:
        try:
            # Use persisted folder names from album_files table
            folder_map: dict[str, str] = {}
            for row in rows:
                if row["album_id"] not in folder_map and row.get("folder_name"):
                    folder_map[row["album_id"]] = row["folder_name"]

            # Build file index: filename.casefold() -> list[Path]
            root = Path(icloud_folder)
            file_index: dict[str, list[Path]] = {}
            for entry in root.rglob("*"):
                if entry.is_file():
                    key = entry.name.casefold()
                    file_index.setdefault(key, []).append(entry)

            # Track already-moved files for cross-album duplicate handling
            claimed: set[Path] = set()

            for row in rows:
                album_id = row["album_id"]
                album_name = row["album_name"]
                filename = row["filename"]

                self._current_file = filename
                self._current_album = album_name

                folder_name = folder_map.get(album_id, icloud_service._sanitize_folder_name(album_name))
                target_dir = root / folder_name

                try:
                    target_dir.mkdir(parents=True, exist_ok=True)

                    candidates = file_index.get(filename.casefold(), [])

                    if not candidates:
                        state_service.mark_album_file_failed(album_id, filename, "File not found")
                        self._failed_files += 1
                        self._errors.append({"filename": filename, "error": "File not found", "album": album_name})
                        continue

                    # Check if already in target dir
                    if duplicate_handling == "copy_to_each":
                        in_target = [c for c in candidates if c.parent == target_dir]
                    else:
                        in_target = [c for c in candidates if c.parent == target_dir and c not in claimed]
                    if in_target:
                        claimed.add(in_target[0])
                        state_service.mark_album_file_sorted(album_id, filename)
                        self._completed_files += 1
                        continue

                    if duplicate_handling == "copy_to_each":
                        source = candidates[0]

                        # Determine target path with collision handling
                        target_path = target_dir / source.name
                        if target_path.exists():
                            stem = target_path.stem
                            suffix = target_path.suffix
                            counter = 2
                            while target_path.exists():
                                target_path = target_dir / f"{stem} ({counter}){suffix}"
                                counter += 1

                        if source not in claimed:
                            os.rename(str(source), str(target_path))
                            claimed.add(source)
                            # Update file index to reflect the move
                            key = source.name.casefold()
                            if key in file_index:
                                file_index[key] = [p if p != source else target_path for p in file_index[key]]
                            claimed.add(target_path)
                        else:
                            shutil.copy2(str(source), str(target_path))

                    else:
                        # move_only mode
                        unclaimed = [c for c in candidates if c not in claimed]
                        if not unclaimed:
                            state_service.mark_album_file_failed(album_id, filename, "Already moved to another album")
                            self._failed_files += 1
                            self._errors.append({"filename": filename, "error": "Already moved to another album", "album": album_name})
                            continue

                        source = unclaimed[0]
                        claimed.add(source)

                        # Determine target path with collision handling
                        target_path = target_dir / source.name
                        if target_path.exists():
                            stem = target_path.stem
                            suffix = target_path.suffix
                            counter = 2
                            while target_path.exists():
                                target_path = target_dir / f"{stem} ({counter}){suffix}"
                                counter += 1

                        os.rename(str(source), str(target_path))

                        # Update file index to reflect the move
                        key = source.name.casefold()
                        if key in file_index:
                            file_index[key] = [p if p != source else target_path for p in file_index[key]]

                    state_service.mark_album_file_sorted(album_id, filename)
                    self._completed_files += 1

                except PermissionError as e:
                    state_service.mark_album_file_failed(album_id, filename, f"Permission denied: {e}")
                    self._failed_files += 1
                    self._errors.append({"filename": filename, "error": f"Permission denied: {e}", "album": album_name})
                except OSError as e:
                    state_service.mark_album_file_failed(album_id, filename, f"OS error: {e}")
                    self._failed_files += 1
                    self._errors.append({"filename": filename, "error": f"OS error: {e}", "album": album_name})

            self._status = "complete"
        except Exception as e:
            logger.exception("Fatal error during sort")
            self._status = "error"
            self._errors.append({"filename": "", "error": f"Fatal error: {e}", "album": ""})
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
