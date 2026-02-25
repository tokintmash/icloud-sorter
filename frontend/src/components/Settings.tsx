import { useState, useEffect } from 'react';
import { getSettings, updateSettings, ApiError } from '../hooks/useApi';

export default function Settings() {
  const [downloadPath, setDownloadPath] = useState('');
  const [concurrentDownloads, setConcurrentDownloads] = useState(3);
  const [metadataDelayMs, setMetadataDelayMs] = useState(200);
  const [maxRetries, setMaxRetries] = useState(3);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError('');
      try {
        const settings = await getSettings();
        setDownloadPath(settings.download_path);
        setConcurrentDownloads(settings.concurrent_downloads);
        setMetadataDelayMs(settings.metadata_delay_ms);
        setMaxRetries(settings.max_retries);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('Failed to load settings.');
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const updated = await updateSettings({
        download_path: downloadPath,
        concurrent_downloads: concurrentDownloads,
        metadata_delay_ms: metadataDelayMs,
        max_retries: maxRetries,
      });
      setDownloadPath(updated.download_path);
      setConcurrentDownloads(updated.concurrent_downloads);
      setMetadataDelayMs(updated.metadata_delay_ms);
      setMaxRetries(updated.max_retries);
      setSuccess('Settings saved successfully.');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to save settings.');
      }
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="settings">
        <h2>Settings</h2>
        <div className="loading-container">
          <span className="spinner" />
          <p>Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="settings">
      <h2>Settings</h2>
      <div className="card">
        <form onSubmit={handleSave}>
          <div className="form-group">
            <label htmlFor="downloadPath">Download Path</label>
            <input
              id="downloadPath"
              type="text"
              value={downloadPath}
              onChange={(e) => setDownloadPath(e.target.value)}
              disabled={saving}
            />
          </div>
          <div className="form-group">
            <label htmlFor="concurrentDownloads">Concurrent Downloads (1–10)</label>
            <input
              id="concurrentDownloads"
              type="number"
              min={1}
              max={10}
              value={concurrentDownloads}
              onChange={(e) => setConcurrentDownloads(Number(e.target.value))}
              disabled={saving}
            />
          </div>
          <div className="form-group">
            <label htmlFor="metadataDelay">Metadata Delay (ms)</label>
            <input
              id="metadataDelay"
              type="number"
              min={0}
              value={metadataDelayMs}
              onChange={(e) => setMetadataDelayMs(Number(e.target.value))}
              disabled={saving}
            />
          </div>
          <div className="form-group">
            <label htmlFor="maxRetries">Max Retries (1–10)</label>
            <input
              id="maxRetries"
              type="number"
              min={1}
              max={10}
              value={maxRetries}
              onChange={(e) => setMaxRetries(Number(e.target.value))}
              disabled={saving}
            />
          </div>
          {error && <p className="error-message">{error}</p>}
          {success && <p className="success-message">{success}</p>}
          <button type="submit" disabled={saving}>
            {saving ? <span className="spinner" /> : 'Save Settings'}
          </button>
        </form>
      </div>
    </div>
  );
}
