import type {
  LoginResponse,
  TwoFactorResponse,
  SessionResponse,
  AlbumListResponse,
  SettingsResponse,
  SettingsUpdateRequest,
  SortStartResponse,
  ErrorResponse,
  ErrorCode,
  BetaStatusResponse,
} from '../types/api';

export class ApiError extends Error {
  code: ErrorCode;

  constructor(code: ErrorCode, message: string) {
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

// Beta
export async function getBetaStatus(): Promise<BetaStatusResponse> {
  return apiFetch<BetaStatusResponse>('/api/app/beta');
}

// Sort
export async function startSort(albumIds: string[]): Promise<SortStartResponse> {
  return apiFetch<SortStartResponse>('/api/sort/start', {
    method: 'POST',
    body: JSON.stringify({ album_ids: albumIds }),
  });
}
