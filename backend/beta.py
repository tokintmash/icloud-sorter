"""Beta expiry logic.

At build time, `scripts/stamp_beta.py` writes the build date into
`backend/_beta_stamp.py`. At runtime we read that stamp, add 10 days,
and check the current date against an external time API.
"""

from __future__ import annotations

import urllib.request
import json
from datetime import date, timedelta

BETA_DAYS = 10

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


def get_beta_status() -> dict:
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

    expires_on = build_date + timedelta(days=BETA_DAYS)

    try:
        today = _get_remote_date()
    except Exception:
        # If we can't reach the time API, allow usage (don't lock out)
        return {
            "is_beta": True,
            "expired": False,
            "expires_on": expires_on.isoformat(),
            "days_remaining": None,
        }

    expired = today >= expires_on
    days_remaining = max(0, (expires_on - today).days)

    return {
        "is_beta": True,
        "expired": expired,
        "expires_on": expires_on.isoformat(),
        "days_remaining": days_remaining,
    }
