from pydantic import BaseModel, Field
from typing import Optional


# --- Standard Error ---

class ErrorResponse(BaseModel):
    error: str
    message: str


# --- Auth ---

class LoginRequest(BaseModel):
    apple_id: str
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    requires_2fa: bool


class TwoFactorRequest(BaseModel):
    code: str


class TwoFactorResponse(BaseModel):
    authenticated: bool


class SessionResponse(BaseModel):
    authenticated: bool
    apple_id: str | None
    requires_2fa: bool


# --- Albums ---

class AlbumInfo(BaseModel):
    id: str
    name: str
    asset_count: int
    folder_name: str


class AlbumListResponse(BaseModel):
    albums: list[AlbumInfo]


class AssetInfo(BaseModel):
    id: str
    filename: str
    size_bytes: int
    item_type: str
    created_at: str
    width: int
    height: int


class AssetListResponse(BaseModel):
    assets: list[AssetInfo]
    total: int
    offset: int
    limit: int


# --- Download ---

class DownloadError(BaseModel):
    asset_id: str
    filename: str
    error: str
    attempts: int


class DownloadStartRequest(BaseModel):
    album_ids: list[str] = []
    asset_selections: dict[str, list[str]] | None = None
    download_path: str


class DownloadStartResponse(BaseModel):
    job_id: str
    total_assets: int
    estimated_bytes: int


class DownloadProgressEvent(BaseModel):
    status: str
    total_assets: int
    completed_assets: int
    failed_assets: int
    skipped_assets: int
    bytes_downloaded: int
    bytes_total: int
    current_file: str
    current_album: str
    speed_bytes_per_sec: int
    eta_seconds: int
    errors: list[DownloadError]


class PauseResponse(BaseModel):
    status: str


class CancelResponse(BaseModel):
    status: str


# --- Settings ---

class SettingsResponse(BaseModel):
    download_path: str
    concurrent_downloads: int
    metadata_delay_ms: int
    max_retries: int


class SettingsUpdateRequest(BaseModel):
    download_path: Optional[str] = None
    concurrent_downloads: Optional[int] = Field(default=None, ge=1, le=10)
    metadata_delay_ms: Optional[int] = Field(default=None, ge=0)
    max_retries: Optional[int] = Field(default=None, ge=1, le=10)
