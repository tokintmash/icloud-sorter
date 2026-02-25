import { useState, useEffect } from 'react';
import { getSession, getSettings } from './hooks/useApi';
import AuthScreen from './components/AuthScreen';
import AlbumBrowser from './components/AlbumBrowser';
import DownloadProgress from './components/DownloadProgress';
import Settings from './components/Settings';

type AuthState = 'loading' | 'unauthenticated' | 'awaiting_2fa' | 'authenticated';
type Tab = 'albums' | 'downloads' | 'settings';

export default function App() {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [appleId, setAppleId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('albums');
  const [downloadState, setDownloadState] = useState<{ albumIds: string[]; downloadPath: string } | null>(null);

  useEffect(() => {
    async function checkSession() {
      try {
        const session = await getSession();
        if (session.authenticated) {
          setAuthState('authenticated');
          setAppleId(session.apple_id);
        } else if (session.requires_2fa) {
          setAuthState('awaiting_2fa');
        } else {
          setAuthState('unauthenticated');
        }
      } catch {
        setAuthState('unauthenticated');
      }
    }
    checkSession();
  }, []);

  function handleAuthenticated() {
    setAuthState('authenticated');
    getSession()
      .then((s) => setAppleId(s.apple_id))
      .catch(() => {});
  }

  function handleSessionExpired() {
    setAuthState('unauthenticated');
    setAppleId(null);
    setDownloadState(null);
  }

  async function handleStartDownload(albumIds: string[]) {
    try {
      const settings = await getSettings();
      setDownloadState({ albumIds, downloadPath: settings.download_path });
      setActiveTab('downloads');
    } catch {
      setDownloadState({ albumIds, downloadPath: '~/icloud-photos' });
      setActiveTab('downloads');
    }
  }

  function handleDownloadComplete() {
    setDownloadState(null);
    setActiveTab('albums');
  }

  if (authState === 'loading') {
    return (
      <div className="app-loading">
        <span className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  if (authState === 'unauthenticated' || authState === 'awaiting_2fa') {
    return (
      <div className="app">
        <header className="app-header">
          <h1>iCloud Photo Downloader</h1>
        </header>
        <main>
          <AuthScreen
            onAuthenticated={handleAuthenticated}
            initialMode={authState === 'awaiting_2fa' ? '2fa' : 'login'}
          />
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>iCloud Photo Downloader</h1>
        <div className="header-right">
          {appleId && <span className="session-info">{appleId}</span>}
        </div>
      </header>
      <nav className="app-nav">
        <button
          className={activeTab === 'albums' ? 'active' : ''}
          onClick={() => setActiveTab('albums')}
        >
          Albums
        </button>
        <button
          className={activeTab === 'downloads' ? 'active' : ''}
          onClick={() => setActiveTab('downloads')}
        >
          Downloads
        </button>
        <button
          className={activeTab === 'settings' ? 'active' : ''}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
      </nav>
      <main>
        {activeTab === 'albums' && (
          <AlbumBrowser
            onSessionExpired={handleSessionExpired}
            onStartDownload={handleStartDownload}
          />
        )}
        {activeTab === 'downloads' && downloadState && (
          <DownloadProgress
            albumIds={downloadState.albumIds}
            downloadPath={downloadState.downloadPath}
            onComplete={handleDownloadComplete}
            onSessionExpired={handleSessionExpired}
          />
        )}
        {activeTab === 'downloads' && !downloadState && (
          <div className="download-progress">
            <h2>Downloads</h2>
            <p>Select albums and click &quot;Download Selected&quot; to start a download.</p>
          </div>
        )}
        {activeTab === 'settings' && <Settings />}
      </main>
    </div>
  );
}
