// Standard Error Response
export type ErrorCode =
  | 'invalid_credentials'
  | '2fa_required'
  | '2fa_failed'
  | 'session_expired'
  | 'not_authenticated'
  | 'sort_in_progress'
  | 'file_not_found'
  | 'permission_denied'
  | 'app_expired'
  | 'internal_error'
  | 'not_found'
  | 'not_available';

export interface ErrorResponse {
  error: ErrorCode;
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

// Sort types
export interface SortStartRequest {
  album_ids: string[];
}

export interface SortStartResponse {
  total_files: number;
}

export interface SortError {
  filename: string;
  error: string;
  album: string;
}

export interface SortProgressEvent {
  status: 'sorting' | 'complete' | 'error';
  total_files: number;
  completed_files: number;
  failed_files: number;
  current_file: string;
  current_album: string;
  errors: SortError[];
  error_code?: ErrorCode | null;
  message?: string | null;
}

// Beta types
export interface BetaStatusResponse {
  is_beta: boolean;
  expired: boolean;
  expires_on: string | null;
  days_remaining: number | null;
}

// Settings types
export interface SettingsResponse {
  icloud_folder: string;
  duplicate_handling: 'move_only' | 'copy_to_each';
}

export interface SettingsUpdateRequest {
  icloud_folder?: string;
  duplicate_handling?: 'move_only' | 'copy_to_each';
}
