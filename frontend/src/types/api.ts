// Standard Error Response
export interface ErrorResponse {
  error: string;
  message: string;
}

// Auth types
export interface LoginRequest {
  apple_id: string;
  password: string;
}

export interface LoginResponse {
  authenticated: boolean;
  requires_2fa: boolean;
}

export interface TwoFactorRequest {
  code: string;
}

export interface TwoFactorResponse {
  authenticated: boolean;
}

export interface SessionResponse {
  authenticated: boolean;
  apple_id: string | null;
  requires_2fa: boolean;
}

// Album types
export interface AlbumInfo {
  id: string;
  name: string;
  asset_count: number;
  folder_name: string;
}

export interface AlbumListResponse {
  albums: AlbumInfo[];
}

export interface AssetInfo {
  id: string;
  filename: string;
  size_bytes: number;
  item_type: string;
  created_at: string;
  width: number;
  height: number;
}

export interface AssetListResponse {
  assets: AssetInfo[];
  total: number;
  offset: number;
  limit: number;
}

// Download types
export interface DownloadStartRequest {
  album_ids: string[];
  download_path: string;
}

export interface DownloadStartResponse {
  job_id: string;
  total_assets: number;
  estimated_bytes: number;
}

export interface DownloadError {
  asset_id: string;
  filename: string;
  error: string;
  attempts: number;
}

export interface DownloadProgressEvent {
  status: 'downloading' | 'paused' | 'complete' | 'cancelled' | 'error';
  total_assets: number;
  completed_assets: number;
  failed_assets: number;
  skipped_assets: number;
  bytes_downloaded: number;
  bytes_total: number;
  current_file: string;
  current_album: string;
  speed_bytes_per_sec: number;
  eta_seconds: number;
  errors: DownloadError[];
}

export interface PauseResponse {
  status: string;
}

export interface CancelResponse {
  status: string;
}

// Settings types
export interface SettingsResponse {
  download_path: string;
  concurrent_downloads: number;
  metadata_delay_ms: number;
  max_retries: number;
}

export interface SettingsUpdateRequest {
  download_path?: string;
  concurrent_downloads?: number;
  metadata_delay_ms?: number;
  max_retries?: number;
}
