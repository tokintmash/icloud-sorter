import { useState, useEffect } from 'react';
import { getAlbums, ApiError } from '../hooks/useApi';
import type { AlbumInfo } from '../types/api';

interface AlbumPickerProps {
  onSessionExpired: () => void;
  onStartSort: (albumIds: string[]) => void;
}

export default function AlbumPicker({ onSessionExpired, onStartSort }: AlbumPickerProps) {
  const [albums, setAlbums] = useState<AlbumInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedAlbums, setSelectedAlbums] = useState<Set<string>>(new Set());

  function handleApiError(err: unknown) {
    if (err instanceof ApiError) {
      if (err.code === 'session_expired' || err.code === 'not_authenticated') {
        onSessionExpired();
        return;
      }
      setError(err.message);
    } else {
      setError('An unexpected error occurred.');
    }
  }

  async function fetchAlbums() {
    setLoading(true);
    setError('');
    try {
      const result = await getAlbums();
      setAlbums(result.albums);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAlbums();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toggleSelection(albumId: string) {
    setSelectedAlbums((prev) => {
      const next = new Set(prev);
      if (next.has(albumId)) {
        next.delete(albumId);
      } else {
        next.add(albumId);
      }
      return next;
    });
  }

  function selectAll() {
    setSelectedAlbums(new Set(albums.map((a) => a.id)));
  }

  function deselectAll() {
    setSelectedAlbums(new Set());
  }

  if (loading) {
    return (
      <div className="album-picker">
        <h2>Albums</h2>
        <div className="loading-container">
          <span className="spinner" />
          <p>Loading albums...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="album-picker">
        <h2>Albums</h2>
        <p className="error-message">{error}</p>
        <button onClick={fetchAlbums}>Retry</button>
      </div>
    );
  }

  return (
    <div className="album-picker">
      <h2>Albums</h2>
      {albums.length === 0 ? (
        <p>No albums found.</p>
      ) : (
        <>
          <div className="album-toolbar">
            <button className="btn-secondary" onClick={selectAll}>
              Select All
            </button>
            <button className="btn-secondary" onClick={deselectAll}>
              Deselect All
            </button>
            <button className="btn-secondary" onClick={fetchAlbums}>
              Refresh from iCloud
            </button>
            <button
              disabled={selectedAlbums.size === 0}
              onClick={() => onStartSort(Array.from(selectedAlbums))}
            >
              Sort Selected ({selectedAlbums.size})
            </button>
          </div>
          <div className="album-list">
            {albums.map((album) => (
              <div key={album.id} className="card album-card">
                <label className="album-header">
                  <div className="album-header-content">
                    <input
                      type="checkbox"
                      className="album-select-checkbox"
                      checked={selectedAlbums.has(album.id)}
                      onChange={() => toggleSelection(album.id)}
                    />
                    <div className="album-info">
                      <span className="album-name">{album.name}</span>
                      <span className="album-count">
                        {album.asset_count.toLocaleString()} files
                      </span>
                    </div>
                  </div>
                  <span className="album-folder">&rarr; {album.folder_name}/</span>
                </label>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
