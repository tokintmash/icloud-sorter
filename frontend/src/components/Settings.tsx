import { useState, useEffect } from 'react';
import { getSettings, updateSettings, ApiError } from '../hooks/useApi';

export default function Settings() {
  const [icloudFolder, setIcloudFolder] = useState('');
  const [duplicateHandling, setDuplicateHandling] = useState<'move_only' | 'copy_to_each'>('move_only');
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
        setDuplicateHandling(settings.duplicate_handling);
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
        duplicate_handling: duplicateHandling,
      });
      setIcloudFolder(updated.icloud_folder);
      setDuplicateHandling(updated.duplicate_handling);
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
          <div className="form-group">
            <label>Cross-Album Duplicates</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="duplicateHandling"
                  value="move_only"
                  checked={duplicateHandling === 'move_only'}
                  onChange={() => setDuplicateHandling('move_only')}
                  disabled={saving}
                />
                <div>
                  <strong>Move to first album only</strong>
                  <p className="radio-description">Each file is placed in one album folder. If a file belongs to multiple albums, it goes to the first one processed.</p>
                </div>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="duplicateHandling"
                  value="copy_to_each"
                  checked={duplicateHandling === 'copy_to_each'}
                  onChange={() => setDuplicateHandling('copy_to_each')}
                  disabled={saving}
                />
                <div>
                  <strong>Copy to each album</strong>
                  <p className="radio-description">Each file is copied into every album folder it belongs to. Uses more disk space.</p>
                </div>
              </label>
            </div>
            {duplicateHandling === 'copy_to_each' && (
              <p className="warning-message">⚠️ This will use additional disk space. A file in 3 albums will result in 3 copies on disk.</p>
            )}
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
