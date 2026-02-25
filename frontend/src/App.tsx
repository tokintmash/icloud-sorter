import { useState, useEffect } from 'react';
import { getSession } from './hooks/useApi';
import AuthScreen from './components/AuthScreen';
import AlbumBrowser from './components/AlbumBrowser';
import Settings from './components/Settings';

type AuthState = 'loading' | 'unauthenticated' | 'awaiting_2fa' | 'authenticated';
type Tab = 'albums' | 'settings';

export default function App() {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [appleId, setAppleId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('albums');

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
          className={activeTab === 'settings' ? 'active' : ''}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
      </nav>
      <main>
        {activeTab === 'albums' && <AlbumBrowser onSessionExpired={handleSessionExpired} />}
        {activeTab === 'settings' && <Settings />}
      </main>
    </div>
  );
}
