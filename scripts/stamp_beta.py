"""Stamp the build date into backend/_beta_stamp.py.

Run this before PyInstaller to embed the build date.
Usage: python scripts/stamp_beta.py
"""

from datetime import date, timezone, datetime
from pathlib import Path

STAMP_FILE = Path(__file__).resolve().parent.parent / "backend" / "_beta_stamp.py"


def main() -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    STAMP_FILE.write_text(
        f'"""Auto-generated at build time. Do not edit."""\n'
        f'BUILD_DATE_ISO = "{today}"\n'
    )
    print(f"Beta stamp written: {today} -> {STAMP_FILE}")


if __name__ == "__main__":
    main()
