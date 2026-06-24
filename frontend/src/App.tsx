import { useState, useEffect } from 'react';
import { getSession, getBetaStatus, ApiError } from './hooks/useApi';
import { APP_EXPIRED_CODE, APP_EXPIRED_MESSAGE } from './appExpiry';
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
    return globalThis.localStorage.getItem(DATA_ACCESS_CONSENT_STORAGE_KEY) === 'accepted';
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
  const [expiredMessage, setExpiredMessage] = useState<string | null>(null);
  const [hasAcceptedConsent, setHasAcceptedConsent] = useState(false);

  function handleAppExpired(message = APP_EXPIRED_MESSAGE) {
    setExpiredMessage(message);
    setAuthState('unauthenticated');
    setAppleId(null);
    setSortState(null);
    setActiveTab('albums');
  }

  useEffect(() => {
    async function init() {
      setHasAcceptedConsent(hasAcceptedCurrentConsent());

      // Check beta status first
      try {
        const beta = await getBetaStatus();
        setBetaStatus(beta);
        if (beta.expired) {
          handleAppExpired(APP_EXPIRED_MESSAGE);
          return;
        }
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
      } catch (err) {
        if (err instanceof ApiError && err.code === APP_EXPIRED_CODE) {
          handleAppExpired(err.message);
          return;
        }
        setAuthState('unauthenticated');
      }
    }
    init();
  }, []);

  function handleAuthenticated() {
    setAuthState('authenticated');
    getSession()
      .then((s) => setAppleId(s.apple_id))
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.code === APP_EXPIRED_CODE) {
          handleAppExpired(err.message);
        }
      });
  }

  function handleAcceptConsent() {
    try {
      globalThis.localStorage.setItem(DATA_ACCESS_CONSENT_STORAGE_KEY, 'accepted');
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

  if (expiredMessage || betaStatus?.expired) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>iCloud Photo Sorter</h1>
        </header>
        <main>
          <div className="auth-screen">
            <div className="card" style={{ textAlign: 'center' }}>
              <h2>Beta Expired</h2>
              <p>{expiredMessage ?? APP_EXPIRED_MESSAGE}</p>
            </div>
          </div>
        </main>
      </div>
    );
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
          <h1>iCloud Photo Sorter</h1>
        </header>
        {betaBanner}
        <main>
          {authState === 'unauthenticated' && !hasAcceptedConsent ? (
            <ConsentScreen onAccept={handleAcceptConsent} />
          ) : (
            <AuthScreen
              onAuthenticated={handleAuthenticated}
              onAppExpired={handleAppExpired}
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
            onAppExpired={handleAppExpired}
            onStartSort={handleStartSort}
          />
        )}
        {activeTab === 'sorting' && sortState && (
          <SortProgress
            albumIds={sortState.albumIds}
            onComplete={handleSortComplete}
            onSessionExpired={handleSessionExpired}
            onAppExpired={handleAppExpired}
          />
        )}
        {activeTab === 'sorting' && !sortState && (
          <div className="sort-progress">
            <h2>Sorting</h2>
            <p>Select albums and click &quot;Sort Selected&quot; to start sorting.</p>
          </div>
        )}
        {activeTab === 'settings' && <Settings onAppExpired={handleAppExpired} />}
      </main>
    </div>
  );
}
