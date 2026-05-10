import { useState, useEffect } from 'react';
import { getSession, getBetaStatus } from './hooks/useApi';
import type { BetaStatusResponse } from './types/api';
import AuthScreen from './components/AuthScreen';
import ConsentScreen from './components/ConsentScreen';
import AlbumPicker from './components/AlbumPicker';
import SortProgress from './components/SortProgress';
import Settings from './components/Settings';

type AuthState = 'loading' | 'unauthenticated' | 'awaiting_2fa' | 'authenticated';
type Tab = 'albums' | 'sorting' | 'settings';

export const DATA_ACCESS_CONSENT_STORAGE_KEY = 'icloud-sorter:data-access-consent:v1';

function hasAcceptedCurrentConsent() {
  try {
    return window.localStorage.getItem(DATA_ACCESS_CONSENT_STORAGE_KEY) === 'accepted';
  } catch {
    return false;
  }
}

export default function App() {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [appleId, setAppleId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('albums');
  const [sortState, setSortState] = useState<{ albumIds: string[] } | null>(null);
  const [betaStatus, setBetaStatus] = useState<BetaStatusResponse | null>(null); // BETA: remove for v1.0
  const [hasAcceptedConsent, setHasAcceptedConsent] = useState(false);

  useEffect(() => {
    async function init() {
      setHasAcceptedConsent(hasAcceptedCurrentConsent());

      // Check beta status first
      try {
        const beta = await getBetaStatus();
        setBetaStatus(beta);
      } catch {
        // If beta check fails, allow usage
      }

      // Then check session
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
    init();
  }, []);

  function handleAuthenticated() {
    setAuthState('authenticated');
    getSession()
      .then((s) => setAppleId(s.apple_id))
      .catch(() => {});
  }

  function handleAcceptConsent() {
    try {
      window.localStorage.setItem(DATA_ACCESS_CONSENT_STORAGE_KEY, 'accepted');
    } catch {
      // Continue to login if browser storage is unavailable.
    }
    setHasAcceptedConsent(true);
  }

  function handleSessionExpired() {
    setAuthState('unauthenticated');
    setAppleId(null);
    setSortState(null);
  }

  function handleStartSort(albumIds: string[]) {
    setSortState({ albumIds });
    setActiveTab('sorting');
  }

  function handleSortComplete() {
    setSortState(null);
    setActiveTab('albums');
  }

  const betaBanner = betaStatus?.is_beta && !betaStatus.expired && betaStatus.expires_on ? (
    <div className="beta-banner">
      This beta expires on {new Date(betaStatus.expires_on + 'T00:00:00').toLocaleDateString()}.
    </div>
  ) : null;

  if (authState === 'loading') {
    return (
      <div className="app-loading">
        <span className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  if (betaStatus?.expired) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>iCloud Photo Sorter</h1>
        </header>
        <main>
          <div className="auth-screen">
            <div className="card" style={{ textAlign: 'center' }}>
              <h2>Beta Expired</h2>
              <p>This beta version expired on {new Date(betaStatus.expires_on + 'T00:00:00').toLocaleDateString()}.</p>
              <p>Please contact the developer for a new build.</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (authState === 'unauthenticated' || authState === 'awaiting_2fa') {
    return (
      <div className="app">
        <header className="app-header">
          <h1>iCloud Photo Sorter</h1>
        </header>
        {betaBanner}
        <main>
          {authState === 'unauthenticated' && !hasAcceptedConsent ? (
            <ConsentScreen onAccept={handleAcceptConsent} />
          ) : (
            <AuthScreen
              onAuthenticated={handleAuthenticated}
              initialMode={authState === 'awaiting_2fa' ? '2fa' : 'login'}
            />
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>iCloud Photo Sorter</h1>
        <div className="header-right">
          {appleId && <span className="session-info">{appleId}</span>}
        </div>
      </header>
      {betaBanner}
      <nav className="app-nav">
        <button
          className={activeTab === 'albums' ? 'active' : ''}
          onClick={() => setActiveTab('albums')}
        >
          Albums
        </button>
        <button
          className={activeTab === 'sorting' ? 'active' : ''}
          onClick={() => setActiveTab('sorting')}
        >
          Sorting
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
          <AlbumPicker
            onSessionExpired={handleSessionExpired}
            onStartSort={handleStartSort}
          />
        )}
        {activeTab === 'sorting' && sortState && (
          <SortProgress
            albumIds={sortState.albumIds}
            onComplete={handleSortComplete}
            onSessionExpired={handleSessionExpired}
          />
        )}
        {activeTab === 'sorting' && !sortState && (
          <div className="sort-progress">
            <h2>Sorting</h2>
            <p>Select albums and click &quot;Sort Selected&quot; to start sorting.</p>
          </div>
        )}
        {activeTab === 'settings' && <Settings />}
      </main>
    </div>
  );
}
