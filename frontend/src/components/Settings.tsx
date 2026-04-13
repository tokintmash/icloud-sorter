import { useState, useEffect } from 'react';
import { getSettings, updateSettings, ApiError } from '../hooks/useApi';

export default function Settings() {
  const [icloudFolder, setIcloudFolder] = useState('');
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
        setIcloudFolder(settings.icloud_folder);
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
        icloud_folder: icloudFolder,
      });
      setIcloudFolder(updated.icloud_folder);
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
            <label htmlFor="icloudFolder">iCloud Photos Folder</label>
            <input
              id="icloudFolder"
              type="text"
              value={icloudFolder}
              onChange={(e) => setIcloudFolder(e.target.value)}
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
