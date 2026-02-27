import type {
  LoginResponse,
  TwoFactorResponse,
  SessionResponse,
  AlbumListResponse,
  AssetListResponse,
  SettingsResponse,
  SettingsUpdateRequest,
  DownloadStartResponse,
  PauseResponse,
  CancelResponse,
  ErrorResponse,
} from '../types/api';

export class ApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = 'ApiError';
  }
}

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {};
  const method = options?.method?.toUpperCase();

  if (method === 'POST' || method === 'PUT') {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...(options?.headers as Record<string, string> | undefined),
    },
  });

  if (!response.ok) {
    let errorData: ErrorResponse;
    try {
      errorData = (await response.json()) as ErrorResponse;
    } catch {
      throw new ApiError('internal_error', `Request failed with status ${response.status}`);
    }
    throw new ApiError(errorData.error, errorData.message);
  }

  return (await response.json()) as T;
}

// Auth
export async function login(appleId: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ apple_id: appleId, password }),
  });
}

export async function submit2fa(code: string): Promise<TwoFactorResponse> {
  return apiFetch<TwoFactorResponse>('/api/auth/2fa', {
    method: 'POST',
    body: JSON.stringify({ code }),
  });
}

export async function getSession(): Promise<SessionResponse> {
  return apiFetch<SessionResponse>('/api/auth/session');
}

// Albums
export async function getAlbums(): Promise<AlbumListResponse> {
  return apiFetch<AlbumListResponse>('/api/albums');
}

export async function getAlbumAssets(
  albumId: string,
  offset = 0,
  limit = 200,
): Promise<AssetListResponse> {
  return apiFetch<AssetListResponse>(
    `/api/albums/${encodeURIComponent(albumId)}/assets?offset=${offset}&limit=${limit}`,
  );
}

// Settings
export async function getSettings(): Promise<SettingsResponse> {
  return apiFetch<SettingsResponse>('/api/settings');
}

export async function updateSettings(settings: SettingsUpdateRequest): Promise<SettingsResponse> {
  return apiFetch<SettingsResponse>('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

// Download
export async function startDownload(
  albumIds: string[],
  downloadPath: string,
  assetSelections?: Record<string, string[]>,
): Promise<DownloadStartResponse> {
  return apiFetch<DownloadStartResponse>('/api/download/start', {
    method: 'POST',
    body: JSON.stringify({
      album_ids: albumIds,
      download_path: downloadPath,
      ...(assetSelections && { asset_selections: assetSelections }),
    }),
  });
}

export async function pauseDownload(): Promise<PauseResponse> {
  return apiFetch<PauseResponse>('/api/download/pause', { method: 'POST' });
}

export async function resumeDownload(): Promise<PauseResponse> {
  return apiFetch<PauseResponse>('/api/download/resume', { method: 'POST' });
}

export async function cancelDownload(): Promise<CancelResponse> {
  return apiFetch<CancelResponse>('/api/download/cancel', { method: 'POST' });
}
