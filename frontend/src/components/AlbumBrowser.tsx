import { useState, useEffect } from 'react';
import { getAlbums, getAlbumAssets, ApiError } from '../hooks/useApi';
import type { AlbumInfo, AssetInfo } from '../types/api';

interface AlbumBrowserProps {
  onSessionExpired: () => void;
  onStartDownload: (albumIds: string[]) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

interface ExpandedAlbumState {
  assets: AssetInfo[];
  total: number;
  offset: number;
  loading: boolean;
  error: string;
}

export default function AlbumBrowser({ onSessionExpired, onStartDownload }: AlbumBrowserProps) {
  const [albums, setAlbums] = useState<AlbumInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<Record<string, ExpandedAlbumState>>({});
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

  async function toggleAlbum(albumId: string) {
    if (expanded[albumId]) {
      setExpanded((prev) => {
        const next = { ...prev };
        delete next[albumId];
        return next;
      });
      return;
    }

    setExpanded((prev) => ({
      ...prev,
      [albumId]: { assets: [], total: 0, offset: 0, loading: true, error: '' },
    }));

    try {
      const result = await getAlbumAssets(albumId, 0, 200);
      setExpanded((prev) => ({
        ...prev,
        [albumId]: {
          assets: result.assets,
          total: result.total,
          offset: result.offset + result.assets.length,
          loading: false,
          error: '',
        },
      }));
    } catch (err) {
      if (err instanceof ApiError && (err.code === 'session_expired' || err.code === 'not_authenticated')) {
        onSessionExpired();
        return;
      }
      const message = err instanceof ApiError ? err.message : 'Failed to load assets.';
      setExpanded((prev) => ({
        ...prev,
        [albumId]: { assets: [], total: 0, offset: 0, loading: false, error: message },
      }));
    }
  }

  async function loadMore(albumId: string) {
    const state = expanded[albumId];
    if (!state) return;

    setExpanded((prev) => ({
      ...prev,
      [albumId]: { ...prev[albumId], loading: true },
    }));

    try {
      const result = await getAlbumAssets(albumId, state.offset, 200);
      setExpanded((prev) => ({
        ...prev,
        [albumId]: {
          ...prev[albumId],
          assets: [...prev[albumId].assets, ...result.assets],
          total: result.total,
          offset: prev[albumId].offset + result.assets.length,
          loading: false,
          error: '',
        },
      }));
    } catch (err) {
      if (err instanceof ApiError && (err.code === 'session_expired' || err.code === 'not_authenticated')) {
        onSessionExpired();
        return;
      }
      const message = err instanceof ApiError ? err.message : 'Failed to load more assets.';
      setExpanded((prev) => ({
        ...prev,
        [albumId]: { ...prev[albumId], loading: false, error: message },
      }));
    }
  }

  if (loading) {
    return (
      <div className="album-browser">
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
      <div className="album-browser">
        <h2>Albums</h2>
        <p className="error-message">{error}</p>
        <button onClick={fetchAlbums}>Retry</button>
      </div>
    );
  }

  return (
    <div className="album-browser">
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
            <button
              disabled={selectedAlbums.size === 0}
              onClick={() => onStartDownload(Array.from(selectedAlbums))}
            >
              Download Selected ({selectedAlbums.size})
            </button>
          </div>
          <div className="album-list">
            {albums.map((album) => {
              const state = expanded[album.id];
              return (
                <div key={album.id} className="card album-card">
                  <div
                    className="album-header"
                    onClick={() => toggleAlbum(album.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') toggleAlbum(album.id);
                    }}
                  >
                    <div className="album-header-content">
                      <input
                        type="checkbox"
                        className="album-select-checkbox"
                        checked={selectedAlbums.has(album.id)}
                        onChange={() => toggleSelection(album.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <div className="album-info">
                        <span className="album-name">{album.name}</span>
                        <span className="album-count">{album.asset_count} items</span>
                      </div>
                    </div>
                    <span className={`album-chevron ${state ? 'open' : ''}`}>▶</span>
                  </div>
                  {state && (
                    <div className="asset-list">
                      {state.error && <p className="error-message">{state.error}</p>}
                      {state.assets.length > 0 && (
                        <table>
                          <thead>
                            <tr>
                              <th>Filename</th>
                              <th>Type</th>
                              <th>Size</th>
                              <th>Dimensions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {state.assets.map((asset) => (
                              <tr key={asset.id}>
                                <td>{asset.filename}</td>
                                <td>{asset.item_type}</td>
                                <td>{formatSize(asset.size_bytes)}</td>
                                <td>
                                  {asset.width > 0 && asset.height > 0
                                    ? `${asset.width}×${asset.height}`
                                    : '—'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                      {state.loading && (
                        <div className="loading-container">
                          <span className="spinner" />
                        </div>
                      )}
                      {!state.loading && state.offset < state.total && (
                        <button className="load-more" onClick={() => loadMore(album.id)}>
                          Load More ({state.total - state.offset} remaining)
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
