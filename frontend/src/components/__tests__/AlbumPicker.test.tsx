import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AlbumPicker from '../AlbumPicker';

vi.mock('../../hooks/useApi', () => ({
  getAlbums: vi.fn(),
  ApiError: class ApiError extends Error {
    code: string;
    constructor(code: string, message: string) {
      super(message);
      this.code = code;
      this.name = 'ApiError';
    }
  },
}));

import { getAlbums, ApiError } from '../../hooks/useApi';

const mockGetAlbums = vi.mocked(getAlbums);

const sampleAlbums = {
  albums: [
    { id: 'a1', name: 'Vacation', asset_count: 10, folder_name: 'Vacation' },
    { id: 'a2', name: 'Birthday', asset_count: 5, folder_name: 'Birthday' },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('AlbumPicker', () => {
  it('renders loading spinner then album list', async () => {
    mockGetAlbums.mockResolvedValue(sampleAlbums);

    render(<AlbumPicker onSessionExpired={vi.fn()} onStartSort={vi.fn()} />);
    expect(screen.getByText(/loading albums/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Vacation')).toBeInTheDocument();
      expect(screen.getByText('Birthday')).toBeInTheDocument();
    });
  });

  it('selects and deselects albums via checkbox', async () => {
    mockGetAlbums.mockResolvedValue(sampleAlbums);
    const user = userEvent.setup();

    render(<AlbumPicker onSessionExpired={vi.fn()} onStartSort={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Vacation')).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[0]);
    expect(checkboxes[0]).toBeChecked();

    await user.click(checkboxes[0]);
    expect(checkboxes[0]).not.toBeChecked();
  });

  it('select all / deselect all', async () => {
    mockGetAlbums.mockResolvedValue(sampleAlbums);
    const user = userEvent.setup();

    render(<AlbumPicker onSessionExpired={vi.fn()} onStartSort={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Vacation')).toBeInTheDocument();
    });

    await user.click(screen.getByText(/^select all$/i));
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach((cb) => expect(cb).toBeChecked());

    await user.click(screen.getByText(/^deselect all$/i));
    checkboxes.forEach((cb) => expect(cb).not.toBeChecked());
  });

  it('sort button disabled when none selected', async () => {
    mockGetAlbums.mockResolvedValue(sampleAlbums);

    render(<AlbumPicker onSessionExpired={vi.fn()} onStartSort={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Vacation')).toBeInTheDocument();
    });

    const sortButton = screen.getByText(/sort selected/i);
    expect(sortButton).toBeDisabled();
  });

  it('calls onStartSort with selected IDs', async () => {
    mockGetAlbums.mockResolvedValue(sampleAlbums);
    const onStartSort = vi.fn();
    const user = userEvent.setup();

    render(<AlbumPicker onSessionExpired={vi.fn()} onStartSort={onStartSort} />);

    await waitFor(() => {
      expect(screen.getByText('Vacation')).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[0]);
    await user.click(screen.getByText(/sort selected/i));

    expect(onStartSort).toHaveBeenCalledWith(expect.arrayContaining(['a1']));
  });

  it('shows error and retry on API failure', async () => {
    mockGetAlbums.mockRejectedValue(new ApiError('internal_error', 'Server error'));

    render(<AlbumPicker onSessionExpired={vi.fn()} onStartSort={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/retry/i)).toBeInTheDocument();
  });

  it('calls onSessionExpired on not_authenticated error', async () => {
    mockGetAlbums.mockRejectedValue(new ApiError('not_authenticated', 'Not authenticated'));
    const onSessionExpired = vi.fn();

    render(<AlbumPicker onSessionExpired={onSessionExpired} onStartSort={vi.fn()} />);

    await waitFor(() => {
      expect(onSessionExpired).toHaveBeenCalled();
    });
  });
});
