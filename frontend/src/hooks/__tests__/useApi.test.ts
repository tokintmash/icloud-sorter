import { describe, it, expect, vi, beforeEach } from 'vitest';

// We need to test the actual module, so we mock `fetch` globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

// Import after mocking fetch
import { login, submit2fa, getSession, getAlbums, getSettings, updateSettings, startSort, ApiError } from '../../hooks/useApi';

function mockResponse(data: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    json: () => Promise.resolve(data),
  };
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe('apiFetch', () => {
  it('sets Content-Type for POST', async () => {
    mockFetch.mockResolvedValue(mockResponse({ authenticated: true, requires_2fa: false }));
    await login('test@apple.com', 'pass');
    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers['Content-Type']).toBe('application/json');
  });

  it('does not set Content-Type for GET', async () => {
    mockFetch.mockResolvedValue(mockResponse({ authenticated: true, apple_id: 'test', requires_2fa: false }));
    await getSession();
    const [, options] = mockFetch.mock.calls[0];
    expect(options?.headers?.['Content-Type']).toBeUndefined();
  });

  it('throws ApiError on non-OK response with JSON body', async () => {
    mockFetch.mockResolvedValue(mockResponse({ error: 'invalid_credentials', message: 'Bad creds' }, false, 401));
    await expect(login('bad', 'wrong')).rejects.toThrow(ApiError);
    try {
      await login('bad', 'wrong');
    } catch (e) {
      expect((e as ApiError).code).toBe('invalid_credentials');
    }
  });

  it('throws internal_error on non-JSON error body', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.reject(new Error('not json')),
    });
    await expect(getSession()).rejects.toThrow(ApiError);
    try {
      await getSession();
    } catch (e) {
      expect((e as ApiError).code).toBe('internal_error');
    }
  });
});

describe('endpoint functions', () => {
  it('login calls POST /api/auth/login', async () => {
    mockFetch.mockResolvedValue(mockResponse({ authenticated: true, requires_2fa: false }));
    await login('user@test.com', 'pass');
    expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({ method: 'POST' }));
  });

  it('submit2fa calls POST /api/auth/2fa', async () => {
    mockFetch.mockResolvedValue(mockResponse({ authenticated: true }));
    await submit2fa('123456');
    expect(mockFetch).toHaveBeenCalledWith('/api/auth/2fa', expect.objectContaining({ method: 'POST' }));
  });

  it('getSession calls GET /api/auth/session', async () => {
    mockFetch.mockResolvedValue(mockResponse({ authenticated: true, apple_id: 'x', requires_2fa: false }));
    await getSession();
    expect(mockFetch).toHaveBeenCalledWith('/api/auth/session', expect.anything());
  });

  it('getAlbums calls GET /api/albums', async () => {
    mockFetch.mockResolvedValue(mockResponse({ albums: [] }));
    await getAlbums();
    expect(mockFetch).toHaveBeenCalledWith('/api/albums', expect.anything());
  });

  it('getSettings calls GET /api/settings', async () => {
    mockFetch.mockResolvedValue(mockResponse({ icloud_folder: '' }));
    await getSettings();
    expect(mockFetch).toHaveBeenCalledWith('/api/settings', expect.anything());
  });

  it('updateSettings calls PUT /api/settings', async () => {
    mockFetch.mockResolvedValue(mockResponse({ icloud_folder: '/new' }));
    await updateSettings({ icloud_folder: '/new' });
    expect(mockFetch).toHaveBeenCalledWith('/api/settings', expect.objectContaining({ method: 'PUT' }));
  });

  it('startSort calls POST /api/sort/start', async () => {
    mockFetch.mockResolvedValue(mockResponse({ total_files: 10 }));
    await startSort(['a1']);
    expect(mockFetch).toHaveBeenCalledWith('/api/sort/start', expect.objectContaining({ method: 'POST' }));
  });
});
