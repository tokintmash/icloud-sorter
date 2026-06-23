import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AuthScreen from '../AuthScreen';

vi.mock('../../hooks/useApi', () => ({
  login: vi.fn(),
  submit2fa: vi.fn(),
  ApiError: class ApiError extends Error {
    code: string;
    constructor(code: string, message: string) {
      super(message);
      this.code = code;
      this.name = 'ApiError';
    }
  },
}));

import { login, ApiError } from '../../hooks/useApi';

const mockLogin = vi.mocked(login);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('AuthScreen', () => {
  it('renders login form by default', () => {
    render(<AuthScreen onAuthenticated={vi.fn()} onAppExpired={vi.fn()} initialMode="login" />);
    expect(screen.getByLabelText(/apple id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('renders 2FA form when initialMode is 2fa', () => {
    render(<AuthScreen onAuthenticated={vi.fn()} onAppExpired={vi.fn()} initialMode="2fa" />);
    expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument();
  });

  it('submits login and transitions to 2FA on requires_2fa', async () => {
    mockLogin.mockResolvedValue({ authenticated: false, requires_2fa: true });
    const user = userEvent.setup();

    render(<AuthScreen onAuthenticated={vi.fn()} onAppExpired={vi.fn()} initialMode="login" />);

    await user.type(screen.getByLabelText(/apple id/i), 'test@test.com');
    await user.type(screen.getByLabelText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument();
    });
  });

  it('calls onAuthenticated on successful login', async () => {
    mockLogin.mockResolvedValue({ authenticated: true, requires_2fa: false });
    const onAuth = vi.fn();
    const user = userEvent.setup();

    render(<AuthScreen onAuthenticated={onAuth} onAppExpired={vi.fn()} initialMode="login" />);

    await user.type(screen.getByLabelText(/apple id/i), 'test@test.com');
    await user.type(screen.getByLabelText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(onAuth).toHaveBeenCalled();
    });
  });

  it('shows error on ApiError', async () => {
    mockLogin.mockRejectedValue(new ApiError('invalid_credentials', 'Bad credentials'));
    const user = userEvent.setup();

    render(<AuthScreen onAuthenticated={vi.fn()} onAppExpired={vi.fn()} initialMode="login" />);

    await user.type(screen.getByLabelText(/apple id/i), 'test@test.com');
    await user.type(screen.getByLabelText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/bad credentials/i)).toBeInTheDocument();
    });
  });

  it('disables button when fields are empty', () => {
    render(<AuthScreen onAuthenticated={vi.fn()} onAppExpired={vi.fn()} initialMode="login" />);
    const button = screen.getByRole('button', { name: /sign in/i });
    expect(button).toBeDisabled();
  });
});
