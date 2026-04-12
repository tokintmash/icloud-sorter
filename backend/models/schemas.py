from pydantic import BaseModel
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


# --- Sort ---

class SortStartRequest(BaseModel):
    album_ids: list[str]


class SortStartResponse(BaseModel):
    total_files: int


class SortError(BaseModel):
    filename: str
    error: str
    album: str


class SortProgressEvent(BaseModel):
    status: str
    total_files: int
    completed_files: int
    failed_files: int
    current_file: str
    current_album: str
    errors: list[SortError]


# --- Settings ---

class SettingsResponse(BaseModel):
    icloud_folder: str


class SettingsUpdateRequest(BaseModel):
    icloud_folder: Optional[str] = None
