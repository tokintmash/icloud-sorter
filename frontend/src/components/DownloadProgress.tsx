import { useState, useEffect, useRef } from 'react';
import { startDownload, pauseDownload, resumeDownload, cancelDownload, ApiError } from '../hooks/useApi';
import type { DownloadProgressEvent } from '../types/api';

interface DownloadProgressProps {
  albumIds: string[];
  assetSelections?: Record<string, string[]>;
  downloadPath: string;
  onComplete: () => void;
  onSessionExpired: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatSpeed(bytesPerSec: number): string {
  return `${formatBytes(bytesPerSec)}/s`;
}

function formatEta(seconds: number): string {
  if (seconds <= 0) return '--';
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

export default function DownloadProgress({
  albumIds,
  assetSelections,
  downloadPath,
  onComplete,
  onSessionExpired,
}: DownloadProgressProps) {
  const [progress, setProgress] = useState<DownloadProgressEvent | null>(null);
  const [jobInfo, setJobInfo] = useState<{ job_id: string; total_assets: number; estimated_bytes: number } | null>(null);
  const [starting, setStarting] = useState(true);
  const [error, setError] = useState('');
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [showAllErrors, setShowAllErrors] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const result = await startDownload(albumIds, downloadPath, assetSelections);
        if (cancelled) return;
        setJobInfo(result);
        setStarting(false);

        const es = new EventSource('/api/download/progress');
        eventSourceRef.current = es;

        es.onmessage = (event) => {
          const data = JSON.parse(event.data) as DownloadProgressEvent;
          setProgress(data);

          if (data.status === 'error' && data.errors.length > 0) {
            const sessionError = data.errors.find((e) => e.error === 'session_expired');
            if (sessionError) {
              es.close();
              onSessionExpired();
              return;
            }
          }

          if (data.status === 'complete' || data.status === 'cancelled' || data.status === 'error') {
            es.close();
          }
        };

        es.onerror = () => {
          // EventSource will auto-reconnect; server sends full snapshot on reconnect
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
          setError('Failed to start download.');
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

  async function handlePauseResume() {
    if (!progress) return;
    try {
      if (progress.status === 'paused') {
        await resumeDownload();
      } else {
        await pauseDownload();
      }
    } catch (err) {
      if (err instanceof ApiError && (err.code === 'session_expired' || err.code === 'not_authenticated')) {
        onSessionExpired();
      }
    }
  }

  async function handleCancel() {
    if (!confirmCancel) {
      setConfirmCancel(true);
      return;
    }
    try {
      await cancelDownload();
      setConfirmCancel(false);
    } catch (err) {
      if (err instanceof ApiError && (err.code === 'session_expired' || err.code === 'not_authenticated')) {
        onSessionExpired();
      }
    }
  }

  if (starting) {
    return (
      <div className="download-progress">
        <h2>Download Progress</h2>
        <div className="loading-container">
          <span className="spinner" />
          <p>Starting download...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="download-progress">
        <h2>Download Progress</h2>
        <div className="disk-space-error">
          <h3>Download Failed</h3>
          <p>{error}</p>
        </div>
        <button onClick={onComplete}>Back to Albums</button>
      </div>
    );
  }

  if (!progress || !jobInfo) {
    return (
      <div className="download-progress">
        <h2>Download Progress</h2>
        <div className="loading-container">
          <span className="spinner" />
          <p>Waiting for progress data...</p>
        </div>
      </div>
    );
  }

  const isTerminal = progress.status === 'complete' || progress.status === 'cancelled' || progress.status === 'error';
  const percentage = progress.bytes_total > 0
    ? Math.round((progress.bytes_downloaded / progress.bytes_total) * 100)
    : 0;

  const barClass = progress.status === 'complete'
    ? 'complete'
    : progress.status === 'error'
      ? 'error'
      : progress.status === 'paused'
        ? 'paused'
        : '';

  const statusLabel =
    progress.status === 'downloading' ? 'Downloading...'
    : progress.status === 'paused' ? 'Paused'
    : progress.status === 'complete' ? 'Complete'
    : progress.status === 'cancelled' ? 'Cancelled'
    : 'Error';

  if (isTerminal) {
    return (
      <div className="download-progress">
        <h2>Download Progress</h2>
        <div className="progress-bar-container">
          <div
            className={`progress-bar-fill ${barClass}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <div className="download-summary">
          <h3>{progress.status === 'complete' ? 'Download Complete!' : statusLabel}</h3>
          <p>
            {progress.completed_assets} files downloaded
            {progress.failed_assets > 0 && `, ${progress.failed_assets} failed`}
            {progress.skipped_assets > 0 && `, ${progress.skipped_assets} skipped`}
          </p>
          {progress.errors.length > 0 && (
            <div className="download-errors">
              <h3>Errors ({progress.errors.length})</h3>
              <ul className="error-list">
                {progress.errors.map((e) => (
                  <li key={e.asset_id}>
                    {e.filename} - {e.error} ({e.attempts} {e.attempts === 1 ? 'try' : 'tries'})
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
    <div className="download-progress">
      <h2>Download Progress</h2>

      <div className="download-status">Status: {statusLabel}</div>
      {progress.current_file && (
        <div className="download-current">
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
          {progress.completed_assets} / {progress.total_assets} files · {formatBytes(progress.bytes_downloaded)} / {formatBytes(progress.bytes_total)}
        </span>
        <span>
          Speed: {formatSpeed(progress.speed_bytes_per_sec)} · ETA: {formatEta(progress.eta_seconds)}
        </span>
      </div>

      <div className="download-actions">
        <button className="btn-secondary" onClick={handlePauseResume}>
          {progress.status === 'paused' ? 'Resume' : 'Pause'}
        </button>
        <button className="btn-danger" onClick={handleCancel}>
          {confirmCancel ? 'Confirm Cancel' : 'Cancel'}
        </button>
        {confirmCancel && (
          <button className="btn-secondary" onClick={() => setConfirmCancel(false)}>
            Never mind
          </button>
        )}
      </div>

      {progress.errors.length > 0 && (
        <div className="download-errors">
          <h3>Errors ({progress.errors.length})</h3>
          <ul className="error-list">
            {visibleErrors.map((e) => (
              <li key={e.asset_id}>
                {e.filename} - {e.error} ({e.attempts} {e.attempts === 1 ? 'try' : 'tries'})
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
