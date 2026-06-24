"""Beta expiry logic.

At build time, `scripts/stamp_beta.py` writes the build date into
`backend/_beta_stamp.py`. At runtime we read that stamp, add 10 days,
and check the current date against an external time API.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime, timedelta, timezone

BETA_DAYS = 10
APP_EXPIRED_ERROR = "app_expired"
APP_EXPIRED_MESSAGE = "This beta has expired. Contact the author of the app to get an up-to-date version."
_CURRENT_DATE_CACHE_TTL = timedelta(minutes=15)
_cached_current_date: date | None = None
_cached_current_date_at: datetime | None = None

# WorldTimeAPI — open source, no API key required
_TIME_API_URL = "https://worldtimeapi.org/api/timezone/Etc/UTC"


def _get_build_date() -> date | None:
    """Return the build date from the stamp file, or None in dev mode."""
    try:
        from backend._beta_stamp import BUILD_DATE_ISO

        return date.fromisoformat(BUILD_DATE_ISO)
    except (ImportError, ValueError):
        return None


def _get_remote_date() -> date:
    """Fetch today's date (UTC) from WorldTimeAPI."""
    req = urllib.request.Request(_TIME_API_URL, headers={"User-Agent": "iCloudPhotoSorter/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    # datetime field is like "2026-04-15T12:34:56.123456+00:00"
    return date.fromisoformat(data["datetime"][:10])


def _get_local_utc_date() -> date:
    """Return today's local UTC date."""
    return _get_utc_now().date()


def _get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_cached_current_date(now: datetime) -> date | None:
    if _cached_current_date is None or _cached_current_date_at is None:
        return None

    if now - _cached_current_date_at >= _CURRENT_DATE_CACHE_TTL:
        return None

    return _cached_current_date


def _set_cached_current_date(today: date, now: datetime) -> None:
    global _cached_current_date, _cached_current_date_at
    _cached_current_date = today
    _cached_current_date_at = now


def _get_current_date(refresh_remote: bool) -> date:
    """Return current UTC date without doing remote I/O on hot paths."""
    now = _get_utc_now()
    local_today = _get_local_utc_date()
    cached_today = _get_cached_current_date(now)

    if cached_today is not None:
        return max(cached_today, local_today)

    if not refresh_remote:
        return local_today

    try:
        today = _get_remote_date()
    except Exception:
        today = local_today

    _set_cached_current_date(today, now)
    return today


def _get_expiry(build_date: date) -> date:
    return build_date + timedelta(days=BETA_DAYS)


def get_beta_status(refresh_remote: bool = True) -> dict:
    """Return beta status info.

    Returns dict with keys:
      - is_beta: bool — True if a build stamp exists
      - expired: bool — True if the beta period has elapsed
      - expires_on: str | None — ISO date string of expiry (or None)
      - days_remaining: int | None — days left (0 if expired)
    """
    build_date = _get_build_date()
    if build_date is None:
        # Dev mode — no stamp, not a beta build
        return {"is_beta": False, "expired": False, "expires_on": None, "days_remaining": None}

    expires_on = _get_expiry(build_date)
    today = _get_current_date(refresh_remote)

    expired = today >= expires_on
    days_remaining = max(0, (expires_on - today).days)

    return {
        "is_beta": True,
        "expired": expired,
        "expires_on": expires_on.isoformat(),
        "days_remaining": days_remaining,
    }


def is_app_expired() -> bool:
    """Return whether this stamped build has expired without remote I/O."""
    return bool(get_beta_status(refresh_remote=False)["expired"])
