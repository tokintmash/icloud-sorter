import { useState, useEffect, useRef } from 'react';
import { startSort, ApiError } from '../hooks/useApi';
import type { SortProgressEvent } from '../types/api';

interface SortProgressProps {
  albumIds: string[];
  onComplete: () => void;
  onSessionExpired: () => void;
}

export default function SortProgress({
  albumIds,
  onComplete,
  onSessionExpired,
}: SortProgressProps) {
  const [progress, setProgress] = useState<SortProgressEvent | null>(null);
  const [starting, setStarting] = useState(true);
  const [error, setError] = useState('');
  const [showAllErrors, setShowAllErrors] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

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
            es.close();
          }
        };

        es.onerror = () => {
          // EventSource will auto-reconnect
        };
      } catch (err) {
        if (cancelled) return;
        setStarting(false);
        if (err instanceof ApiError) {
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
  const percentage = progress.total_files > 0
    ? Math.round((progress.completed_files / progress.total_files) * 100)
    : 0;

  let barClass = '';
  if (progress.status === 'complete') {
    barClass = 'complete';
  } else if (progress.status === 'error') {
    barClass = 'error';
  }

  let statusLabel = 'Error';
  if (progress.status === 'sorting') {
    statusLabel = 'Sorting...';
  } else if (progress.status === 'complete') {
    statusLabel = 'Complete';
  }

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
          <h3>{progress.status === 'complete' ? 'Sorting Complete!' : 'Sort Error'}</h3>
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
              {showAllErrors ? 'Show fewer' : `Show all ${progress.errors.length} errors`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
