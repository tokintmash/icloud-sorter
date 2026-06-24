import { useState, useEffect, useRef } from 'react';
import { startSort, getBetaStatus, ApiError } from '../hooks/useApi';
import { APP_EXPIRED_CODE, APP_EXPIRED_MESSAGE } from '../appExpiry';
import type { SortProgressEvent } from '../types/api';

interface SortProgressProps {
  readonly albumIds: string[];
  readonly onComplete: () => void;
  readonly onSessionExpired: () => void;
  readonly onAppExpired: (message?: string) => void;
}

function getProgressPercentage(progress: SortProgressEvent): number {
  if (progress.total_files <= 0) {
    return 0;
  }

  return Math.round((progress.completed_files / progress.total_files) * 100);
}

function getProgressBarClass(status: SortProgressEvent['status']): string {
  if (status === 'complete') {
    return 'complete';
  }

  if (status === 'error') {
    return 'error';
  }

  return '';
}

function getStatusLabel(status: SortProgressEvent['status']): string {
  if (status === 'sorting') {
    return 'Sorting...';
  }

  if (status === 'complete') {
    return 'Complete';
  }

  return 'Error';
}

function getCompletionHeading(status: SortProgressEvent['status']): string {
  if (status === 'complete') {
    return 'Sorting Complete!';
  }

  return 'Sort Error';
}

export default function SortProgress({
  albumIds,
  onComplete,
  onSessionExpired,
  onAppExpired,
}: SortProgressProps) {
  const [progress, setProgress] = useState<SortProgressEvent | null>(null);
  const [starting, setStarting] = useState(true);
  const [error, setError] = useState('');
  const [showAllErrors, setShowAllErrors] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const terminalReceivedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        await startSort(albumIds);
        if (cancelled) return;
        setStarting(false);

        const es = new EventSource('/api/sort/progress');
        eventSourceRef.current = es;

        es.onmessage = (event) => {
          const data = JSON.parse(event.data) as SortProgressEvent;
          setProgress(data);

          if (data.status === 'complete' || data.status === 'error') {
            terminalReceivedRef.current = true;
            es.close();
            if (data.error_code === APP_EXPIRED_CODE) {
              onAppExpired(data.message ?? APP_EXPIRED_MESSAGE);
            }
          }
        };

        es.onerror = async () => {
          if (terminalReceivedRef.current) return;

          try {
            const beta = await getBetaStatus();
            if (beta.expired) {
              terminalReceivedRef.current = true;
              es.close();
              onAppExpired(APP_EXPIRED_MESSAGE);
            }
          } catch {
            // EventSource will auto-reconnect when this is not an expiry refusal.
          }
        };
      } catch (err) {
        if (cancelled) return;
        setStarting(false);
        if (err instanceof ApiError) {
          if (err.code === APP_EXPIRED_CODE) {
            onAppExpired(err.message);
            return;
          }
          if (err.code === 'session_expired' || err.code === 'not_authenticated') {
            onSessionExpired();
            return;
          }
          setError(err.message);
        } else {
          setError('Failed to start sorting.');
        }
      }
    }

    init();

    return () => {
      cancelled = true;
      eventSourceRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (starting) {
    return (
      <div className="sort-progress">
        <h2>Sort Progress</h2>
        <div className="loading-container">
          <span className="spinner" />
          <p>Starting sort...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="sort-progress">
        <h2>Sort Progress</h2>
        <div className="disk-space-error">
          <h3>Sort Failed</h3>
          <p>{error}</p>
        </div>
        <button onClick={onComplete}>Back to Albums</button>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="sort-progress">
        <h2>Sort Progress</h2>
        <div className="loading-container">
          <span className="spinner" />
          <p>Waiting for progress data...</p>
        </div>
      </div>
    );
  }

  const isTerminal = progress.status === 'complete' || progress.status === 'error';
  const percentage = getProgressPercentage(progress);
  const barClass = getProgressBarClass(progress.status);
  const statusLabel = getStatusLabel(progress.status);

  if (isTerminal) {
    return (
      <div className="sort-progress">
        <h2>Sort Progress</h2>
        <div className="progress-bar-container">
          <div
            className={`progress-bar-fill ${barClass}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <div className="sort-summary">
          <h3>{getCompletionHeading(progress.status)}</h3>
          <p>
            {progress.completed_files} files sorted
            {progress.failed_files > 0 && `, ${progress.failed_files} failed`}
          </p>
          {progress.errors.length > 0 && (
            <div className="sort-errors">
              <h3>Skipped files ({progress.errors.length})</h3>
              <ul className="error-list">
                {progress.errors.map((e, i) => (
                  <li key={`${e.filename}-${i}`}>
                    {e.filename} ({e.album}) — {e.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <button className="btn-success" onClick={onComplete}>Done</button>
        </div>
      </div>
    );
  }

  const visibleErrors = showAllErrors ? progress.errors : progress.errors.slice(0, 5);
  const errorToggleLabel = showAllErrors ? 'Show fewer' : `Show all ${progress.errors.length} errors`;

  return (
    <div className="sort-progress">
      <h2>Sort Progress</h2>

      <div className="sort-status">Status: {statusLabel}</div>
      {progress.current_file && (
        <div className="sort-current">
          Current: {progress.current_file}
          {progress.current_album && ` (${progress.current_album})`}
        </div>
      )}

      <div className="progress-bar-container">
        <div
          className={`progress-bar-fill ${barClass}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="progress-stats">
        <span>
          {progress.completed_files} / {progress.total_files} files
        </span>
        {progress.failed_files > 0 && (
          <span>{progress.failed_files} failed</span>
        )}
      </div>

      {progress.errors.length > 0 && (
        <div className="sort-errors">
          <h3>Skipped files ({progress.errors.length})</h3>
          <ul className="error-list">
            {visibleErrors.map((e, i) => (
              <li key={`${e.filename}-${i}`}>
                {e.filename} ({e.album}) — {e.error}
              </li>
            ))}
          </ul>
          {progress.errors.length > 5 && (
            <button
              className="btn-secondary"
              style={{ marginTop: '8px', fontSize: '13px' }}
              onClick={() => setShowAllErrors((v) => !v)}
            >
              {errorToggleLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
