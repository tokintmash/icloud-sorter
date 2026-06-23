from datetime import date

from backend import beta


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
