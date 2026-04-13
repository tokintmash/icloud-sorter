import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SortProgress from '../SortProgress';
import type { SortProgressEvent } from '../../types/api';

vi.mock('../../hooks/useApi', () => ({
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

import { startSort, ApiError } from '../../hooks/useApi';

const mockStartSort = vi.mocked(startSort);

let mockEventSource: {
  onmessage: ((event: MessageEvent) => void) | null;
  onerror: (() => void) | null;
  close: ReturnType<typeof vi.fn>;
};

class MockEventSource {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  close = vi.fn();
  constructor() {
    mockEventSource = this;
  }
}

beforeEach(() => {
  vi.clearAllMocks();
  mockEventSource = {
    onmessage: null,
    onerror: null,
    close: vi.fn(),
  };
  vi.stubGlobal('EventSource', MockEventSource);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function sendSSEEvent(data: SortProgressEvent) {
  act(() => {
    mockEventSource.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  });
}

describe('SortProgress', () => {
  it('shows starting spinner initially', () => {
    mockStartSort.mockReturnValue(new Promise(() => {})); // never resolves
    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} />);
    expect(screen.getByText(/starting sort/i)).toBeInTheDocument();
  });

  it('shows progress bar after SSE events', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} />);

    await waitFor(() => {
      expect(screen.queryByText(/starting sort/i)).not.toBeInTheDocument();
    });

    sendSSEEvent({
      status: 'sorting',
      total_files: 10,
      completed_files: 5,
      failed_files: 0,
      current_file: 'IMG_001.HEIC',
      current_album: 'Vacation',
      errors: [],
    });

    expect(screen.getByText(/5 \/ 10 files/)).toBeInTheDocument();
  });

  it('shows current file and album', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} />);

    await waitFor(() => {
      expect(screen.queryByText(/starting sort/i)).not.toBeInTheDocument();
    });

    sendSSEEvent({
      status: 'sorting',
      total_files: 10,
      completed_files: 3,
      failed_files: 0,
      current_file: 'IMG_002.HEIC',
      current_album: 'Birthday',
      errors: [],
    });

    expect(screen.getByText(/IMG_002\.HEIC/)).toBeInTheDocument();
    expect(screen.getByText(/Birthday/)).toBeInTheDocument();
  });

  it('shows completion summary', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} />);

    await waitFor(() => {
      expect(screen.queryByText(/starting sort/i)).not.toBeInTheDocument();
    });

    sendSSEEvent({
      status: 'complete',
      total_files: 10,
      completed_files: 10,
      failed_files: 0,
      current_file: '',
      current_album: '',
      errors: [],
    });

    expect(screen.getByText(/sorting complete/i)).toBeInTheDocument();
    expect(screen.getByText(/done/i)).toBeInTheDocument();
  });

  it('calls onComplete when Done clicked', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });
    const onComplete = vi.fn();
    const user = userEvent.setup();

    render(<SortProgress albumIds={['a1']} onComplete={onComplete} onSessionExpired={vi.fn()} />);

    await waitFor(() => {
      expect(screen.queryByText(/starting sort/i)).not.toBeInTheDocument();
    });

    sendSSEEvent({
      status: 'complete',
      total_files: 10,
      completed_files: 10,
      failed_files: 0,
      current_file: '',
      current_album: '',
      errors: [],
    });

    await user.click(screen.getByText(/done/i));
    expect(onComplete).toHaveBeenCalled();
  });

  it('handles startSort failure with error message', async () => {
    mockStartSort.mockRejectedValue(new ApiError('file_not_found', 'iCloud folder not found'));

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/icloud folder not found/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/back to albums/i)).toBeInTheDocument();
  });

  it('shows error list with show all toggle for >5 errors', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} />);

    await waitFor(() => {
      expect(screen.queryByText(/starting sort/i)).not.toBeInTheDocument();
    });

    const errors = Array.from({ length: 7 }, (_, i) => ({
      filename: `file${i}.jpg`,
      error: 'Not found',
      album: 'Album',
    }));

    sendSSEEvent({
      status: 'sorting',
      total_files: 10,
      completed_files: 3,
      failed_files: 7,
      current_file: '',
      current_album: '',
      errors,
    });

    // Should show only 5 initially
    expect(screen.getByText(/show all 7 errors/i)).toBeInTheDocument();
  });
});
