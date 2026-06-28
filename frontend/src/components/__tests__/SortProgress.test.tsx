import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SortProgress from '../SortProgress';
import type { SortProgressEvent } from '../../types/api';

vi.mock('../../hooks/useApi', () => ({
  startSort: vi.fn(),
  getBetaStatus: vi.fn(),
  ApiError: class ApiError extends Error {
    code: string;
    constructor(code: string, message: string) {
      super(message);
      this.code = code;
      this.name = 'ApiError';
    }
  },
}));

import { startSort, getBetaStatus, ApiError } from '../../hooks/useApi';

const mockStartSort = vi.mocked(startSort);
const mockGetBetaStatus = vi.mocked(getBetaStatus);

class MockEventSource {
  static latest: MockEventSource | null = null;

  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  close = vi.fn();

  constructor() {
    MockEventSource.latest = this;
  }
}

function getMockEventSource(): MockEventSource {
  if (!MockEventSource.latest) {
    throw new Error('EventSource has not been initialized');
  }

  return MockEventSource.latest;
}

beforeEach(() => {
  vi.clearAllMocks();
  MockEventSource.latest = null;
  mockGetBetaStatus.mockResolvedValue({
    is_beta: true,
    expired: false,
    expires_on: '2026-01-01',
    days_remaining: 1,
  });
  vi.stubGlobal('EventSource', MockEventSource);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function sendSSEEvent(data: SortProgressEvent) {
  act(() => {
    getMockEventSource().onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  });
}

describe('SortProgress', () => {
  it('shows starting spinner initially', () => {
    mockStartSort.mockReturnValue(new Promise(() => {})); // never resolves
    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} onAppExpired={vi.fn()} />);
    expect(screen.getByText(/starting sort/i)).toBeInTheDocument();
  });

  it('shows progress bar after SSE events', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} onAppExpired={vi.fn()} />);

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

  it('reconnects to progress without starting a duplicate sort when already started', async () => {
    render(
      <SortProgress
        albumIds={['a1']}
        hasStarted={true}
        onComplete={vi.fn()}
        onSessionExpired={vi.fn()}
        onAppExpired={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/waiting for progress data/i)).toBeInTheDocument();
    });

    expect(mockStartSort).not.toHaveBeenCalled();
    expect(getMockEventSource()).toBeDefined();
  });

  it('shows current file and album', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} onAppExpired={vi.fn()} />);

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

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} onAppExpired={vi.fn()} />);

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

    render(<SortProgress albumIds={['a1']} onComplete={onComplete} onSessionExpired={vi.fn()} onAppExpired={vi.fn()} />);

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

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} onAppExpired={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/icloud folder not found/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/back to albums/i)).toBeInTheDocument();
  });

  it('shows error list with show all toggle for >5 errors', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} onAppExpired={vi.fn()} />);

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

  it('checks expiry status when EventSource fails and routes expired builds', async () => {
    mockStartSort.mockResolvedValue({ total_files: 10 });
    mockGetBetaStatus.mockResolvedValue({
      is_beta: true,
      expired: true,
      expires_on: '2026-01-01',
      days_remaining: 0,
    });
    const onAppExpired = vi.fn();

    render(<SortProgress albumIds={['a1']} onComplete={vi.fn()} onSessionExpired={vi.fn()} onAppExpired={onAppExpired} />);

    await waitFor(() => {
      expect(screen.queryByText(/starting sort/i)).not.toBeInTheDocument();
    });

    act(() => {
      getMockEventSource().onerror?.();
    });

    await waitFor(() => {
      expect(onAppExpired).toHaveBeenCalledWith('This beta has expired. Contact the author of the app to get an up-to-date version.');
    });
    expect(getMockEventSource().close).toHaveBeenCalled();
  });
});
