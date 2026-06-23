import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App, { DATA_ACCESS_CONSENT_STORAGE_KEY } from './App';
import { APP_EXPIRED_MESSAGE } from './appExpiry';

vi.mock('./hooks/useApi', () => ({
  getSession: vi.fn(),
  getBetaStatus: vi.fn(),
  login: vi.fn(),
  submit2fa: vi.fn(),
  getAlbums: vi.fn(),
  getSettings: vi.fn(),
  updateSettings: vi.fn(),
  startSort: vi.fn(),
  ApiError: class ApiError extends Error {
    code: string;
    constructor(code: string, message: string) {
      super(message);
      this.code = code;
      this.name = 'ApiError';
    }
  },
}));

import { getSession, getBetaStatus, getAlbums, getSettings, ApiError } from './hooks/useApi';

const mockGetSession = vi.mocked(getSession);
const mockGetBetaStatus = vi.mocked(getBetaStatus);
const mockGetAlbums = vi.mocked(getAlbums);
const mockGetSettings = vi.mocked(getSettings);

beforeEach(() => {
  vi.clearAllMocks();
  globalThis.localStorage.clear();
  mockGetBetaStatus.mockResolvedValue({
    is_beta: false,
    expired: false,
    expires_on: null,
    days_remaining: null,
  });
});

describe('App', () => {
  it('shows loading state initially', () => {
    mockGetSession.mockReturnValue(new Promise(() => {})); // never resolves
    render(<App />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows consent before AuthScreen when unauthenticated without local consent', async () => {
    mockGetSession.mockResolvedValue({ authenticated: false, apple_id: null, requires_2fa: false });
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/review data access/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/sign in with apple id/i)).not.toBeInTheDocument();
  });

  it('shows AuthScreen when unauthenticated with accepted local consent', async () => {
    globalThis.localStorage.setItem(DATA_ACCESS_CONSENT_STORAGE_KEY, 'accepted');
    mockGetSession.mockResolvedValue({ authenticated: false, apple_id: null, requires_2fa: false });
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/sign in with apple id/i)).toBeInTheDocument();
    });
  });

  it('remembers accepted consent and continues to AuthScreen', async () => {
    mockGetSession.mockResolvedValue({ authenticated: false, apple_id: null, requires_2fa: false });
    const user = userEvent.setup();

    render(<App />);

    await user.click(await screen.findByRole('button', { name: /i understand and agree/i }));

    expect(globalThis.localStorage.getItem(DATA_ACCESS_CONSENT_STORAGE_KEY)).toBe('accepted');
    expect(screen.getByText(/sign in with apple id/i)).toBeInTheDocument();
  });

  it('shows beta expired before consent or AuthScreen', async () => {
    mockGetBetaStatus.mockResolvedValue({
      is_beta: true,
      expired: true,
      expires_on: '2026-01-01',
      days_remaining: 0,
    });
    mockGetSession.mockResolvedValue({ authenticated: false, apple_id: null, requires_2fa: false });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/beta expired/i)).toBeInTheDocument();
    });
    expect(screen.getByText(APP_EXPIRED_MESSAGE)).toBeInTheDocument();
    expect(screen.queryByText(/review data access/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sign in with apple id/i)).not.toBeInTheDocument();
    expect(mockGetSession).not.toHaveBeenCalled();
  });

  it('keeps active beta builds in the existing flow', async () => {
    mockGetBetaStatus.mockResolvedValue({
      is_beta: true,
      expired: false,
      expires_on: '2026-01-01',
      days_remaining: 1,
    });
    mockGetSession.mockResolvedValue({ authenticated: false, apple_id: null, requires_2fa: false });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/review data access/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/this beta expires on/i)).toBeInTheDocument();
  });

  it('shows expiration screen when protected API reports app_expired', async () => {
    mockGetSession.mockResolvedValue({ authenticated: true, apple_id: 'test@apple.com', requires_2fa: false });
    mockGetAlbums.mockRejectedValue(new ApiError('app_expired', APP_EXPIRED_MESSAGE));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/beta expired/i)).toBeInTheDocument();
    });
    expect(screen.getByText(APP_EXPIRED_MESSAGE)).toBeInTheDocument();
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  });

  it('shows nav and AlbumPicker when authenticated', async () => {
    mockGetSession.mockResolvedValue({ authenticated: true, apple_id: 'test@apple.com', requires_2fa: false });
    mockGetAlbums.mockResolvedValue({ albums: [] });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
    const nav = screen.getByRole('navigation');
    expect(nav).toHaveTextContent('Albums');
    expect(nav).toHaveTextContent('Sorting');
    expect(nav).toHaveTextContent('Settings');
  });

  it('navigates to Settings tab', async () => {
    mockGetSession.mockResolvedValue({ authenticated: true, apple_id: 'test@apple.com', requires_2fa: false });
    mockGetAlbums.mockResolvedValue({ albums: [] });
    mockGetSettings.mockResolvedValue({ icloud_folder: '/test', duplicate_handling: 'move_only' });
    const user = userEvent.setup();

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Settings'));

    await waitFor(() => {
      expect(screen.getByDisplayValue('/test')).toBeInTheDocument();
    });
  });
});
