import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

vi.mock('./hooks/useApi', () => ({
  getSession: vi.fn(),
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

import { getSession, getAlbums, getSettings } from './hooks/useApi';

const mockGetSession = vi.mocked(getSession);
const mockGetAlbums = vi.mocked(getAlbums);
const mockGetSettings = vi.mocked(getSettings);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('App', () => {
  it('shows loading state initially', () => {
    mockGetSession.mockReturnValue(new Promise(() => {})); // never resolves
    render(<App />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows AuthScreen when unauthenticated', async () => {
    mockGetSession.mockResolvedValue({ authenticated: false, apple_id: null, requires_2fa: false });
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/sign in with apple id/i)).toBeInTheDocument();
    });
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
