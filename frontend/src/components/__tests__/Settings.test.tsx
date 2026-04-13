import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Settings from '../Settings';

vi.mock('../../hooks/useApi', () => ({
  getSettings: vi.fn(),
  updateSettings: vi.fn(),
  ApiError: class ApiError extends Error {
    code: string;
    constructor(code: string, message: string) {
      super(message);
      this.code = code;
      this.name = 'ApiError';
    }
  },
}));

import { getSettings, updateSettings, ApiError } from '../../hooks/useApi';

const mockGetSettings = vi.mocked(getSettings);
const mockUpdateSettings = vi.mocked(updateSettings);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('Settings', () => {
  it('loads and displays current icloud_folder', async () => {
    mockGetSettings.mockResolvedValue({ icloud_folder: '/photos/icloud', duplicate_handling: 'move_only' });

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('/photos/icloud')).toBeInTheDocument();
    });
  });

  it('saves updated value and shows success', async () => {
    mockGetSettings.mockResolvedValue({ icloud_folder: '/old', duplicate_handling: 'move_only' });
    mockUpdateSettings.mockResolvedValue({ icloud_folder: '/new', duplicate_handling: 'move_only' });
    const user = userEvent.setup();

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('/old')).toBeInTheDocument();
    });

    const input = screen.getByDisplayValue('/old');
    await user.clear(input);
    await user.type(input, '/new');
    await user.click(screen.getByText(/save settings/i));

    await waitFor(() => {
      expect(screen.getByText(/settings saved/i)).toBeInTheDocument();
    });
  });

  it('shows error on save failure', async () => {
    mockGetSettings.mockResolvedValue({ icloud_folder: '/old', duplicate_handling: 'move_only' });
    mockUpdateSettings.mockRejectedValue(new ApiError('internal_error', 'Save failed'));
    const user = userEvent.setup();

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('/old')).toBeInTheDocument();
    });

    await user.click(screen.getByText(/save settings/i));

    await waitFor(() => {
      expect(screen.getByText(/save failed/i)).toBeInTheDocument();
    });
  });
});
