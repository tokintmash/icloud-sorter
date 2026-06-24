from datetime import date

import pytest

from backend import beta


@pytest.fixture(autouse=True)
def clear_current_date_cache(monkeypatch):
    monkeypatch.setattr(beta, "_cached_current_date", None)
    monkeypatch.setattr(beta, "_cached_current_date_at", None)


def test_unstamped_development_build_is_not_expiry_controlled(monkeypatch):
    monkeypatch.setattr(beta, "_get_build_date", lambda: None)

    status = beta.get_beta_status()

    assert status == {
        "is_beta": False,
        "expired": False,
        "expires_on": None,
        "days_remaining": None,
    }


def test_active_stamped_build_reports_expiry(monkeypatch):
    monkeypatch.setattr(beta, "_get_build_date", lambda: date(2026, 1, 1))
    monkeypatch.setattr(beta, "_get_remote_date", lambda: date(2026, 1, 5))

    status = beta.get_beta_status()

    assert status["is_beta"] is True
    assert status["expired"] is False
    assert status["expires_on"] == "2026-01-11"
    assert status["days_remaining"] == 6


def test_expired_stamped_build_reports_expired(monkeypatch):
    monkeypatch.setattr(beta, "_get_build_date", lambda: date(2026, 1, 1))
    monkeypatch.setattr(beta, "_get_remote_date", lambda: date(2026, 1, 11))

    status = beta.get_beta_status()

    assert status["is_beta"] is True
    assert status["expired"] is True
    assert status["expires_on"] == "2026-01-11"
    assert status["days_remaining"] == 0


def test_remote_time_failure_falls_back_to_local_utc_date(monkeypatch):
    monkeypatch.setattr(beta, "_get_build_date", lambda: date(2026, 1, 1))
    monkeypatch.setattr(beta, "_get_remote_date", lambda: (_ for _ in ()).throw(OSError("offline")))
    monkeypatch.setattr(beta, "_get_local_utc_date", lambda: date(2026, 1, 12))

    status = beta.get_beta_status()

    assert status["expired"] is True
    assert status["days_remaining"] == 0


def test_beta_status_caches_remote_date(monkeypatch):
    calls = 0

    def get_remote_date():
        nonlocal calls
        calls += 1
        return date(2026, 1, 5)

    monkeypatch.setattr(beta, "_get_build_date", lambda: date(2026, 1, 1))
    monkeypatch.setattr(beta, "_get_remote_date", get_remote_date)
    monkeypatch.setattr(beta, "_get_local_utc_date", lambda: date(2026, 1, 5))

    assert beta.get_beta_status()["expired"] is False
    assert beta.get_beta_status()["expired"] is False

    assert calls == 1


def test_is_app_expired_uses_local_date_without_remote_io(monkeypatch):
    def fail_if_remote_called():
        raise AssertionError("hot-path expiry check should not call remote time")

    monkeypatch.setattr(beta, "_get_build_date", lambda: date(2026, 1, 1))
    monkeypatch.setattr(beta, "_get_remote_date", fail_if_remote_called)
    monkeypatch.setattr(beta, "_get_local_utc_date", lambda: date(2026, 1, 12))

    assert beta.is_app_expired() is True
