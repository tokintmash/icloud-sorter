import { useState } from 'react';
import { login, submit2fa, ApiError } from '../hooks/useApi';

interface AuthScreenProps {
  readonly onAuthenticated: () => void;
  readonly initialMode: 'login' | '2fa';
}

export default function AuthScreen({ onAuthenticated, initialMode }: AuthScreenProps) {
  const [mode, setMode] = useState<'login' | '2fa'>(initialMode);
  const [appleId, setAppleId] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(appleId, password);
      if (result.requires_2fa) {
        setMode('2fa');
      } else if (result.authenticated) {
        onAuthenticated();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred.');
      }
    } finally {
      setLoading(false);
    }
  }

  async function handle2fa(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await submit2fa(code);
      if (result.authenticated) {
        onAuthenticated();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred.');
      }
    } finally {
      setLoading(false);
    }
  }

  if (mode === '2fa') {
    return (
      <div className="auth-screen">
        <div className="card">
          <h2>Two-Factor Authentication</h2>
          <p>Enter the 6-digit code sent to your trusted device.</p>
          <form onSubmit={handle2fa}>
            <div className="form-group">
              <label htmlFor="code">Verification Code</label>
              <input
                id="code"
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="000000"
                disabled={loading}
                autoFocus
              />
            </div>
            {error && <p className="error-message">{error}</p>}
            <button type="submit" disabled={loading || code.length !== 6}>
              {loading ? <span className="spinner" /> : 'Verify'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-screen">
      <div className="card">
        <h2>Sign in with Apple ID</h2>
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="appleId">Apple ID</label>
            <input
              id="appleId"
              type="email"
              value={appleId}
              onChange={(e) => setAppleId(e.target.value)}
              placeholder="you@example.com"
              disabled={loading}
              autoFocus
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              disabled={loading}
            />
          </div>
          {error && <p className="error-message">{error}</p>}
          <button type="submit" disabled={loading || !appleId || !password}>
            {loading ? <span className="spinner" /> : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
