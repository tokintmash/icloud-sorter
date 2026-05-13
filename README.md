# iCloud Photo Sorter

Organize your iCloud photos locally by album. Reads iCloud album metadata, matches it to files already synced by iCloud for Windows, and moves them into album-named folders — no downloading required.

## Features

- 🔐 Secure iCloud authentication with 2FA support
- 📁 Browse and select albums to sort
- 📊 Real-time sort progress via SSE
- 🗂️ Files moved (not copied) into album-named folders — instant on same drive
- 🔄 Case-insensitive filename matching (Windows NTFS)
- ⚡ Collision handling and cross-album duplicate detection

## Prerequisites

Before getting started, please read the [Prerequisites Guide](docs/PREREQUISITES.md) — you'll need to configure your iCloud account settings.

**Required software:** Python 3.10+, Node.js 18+

## Quick Start

```bash
# Clone the repository
git clone https://github.com/tokintmash/icloud-downloader.git
cd icloud-downloader

# Set up the backend
python -m venv venv
venv\Scripts\activate           # On macOS/Linux: source venv/bin/activate
pip install -r backend/requirements.txt

# Build the frontend
cd frontend
npm install
npm run build

# Run the application
cd ..
python backend/app.py
```

Then open `http://localhost:8000` in your browser.

## Development

See the [Development Guide](docs/DEVELOPMENT.md) for running the project in development mode with hot reloading.

## Desktop App (Windows .exe)

Build a standalone desktop application that runs in a native window (no browser needed):

**Requirements:** Windows 10/11 (WebView2 is included with the OS)

```powershell
# Install build dependencies
pip install -r requirements-build.txt

# Build (frontend + PyInstaller)
.\scripts\build_windows.ps1
```

The output is `dist\iCloudPhotoSorter\iCloudPhotoSorter.exe` — double-click to run.

## Windows MSI Installer

Build an MSI installer around the PyInstaller `onedir` desktop app:

```powershell
.\scripts\build_msi.ps1
```

The MSI output is written to `dist\installer\`. See [Windows MSI Packaging](docs/PACKAGING.md) for local dependencies, signing expectations, and verification steps.

## Releasing

Push a version tag to trigger a GitHub Release in the public releases repo with the built `.zip` automatically:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

The CI pipeline runs lint, tests, builds the exe, and publishes the release artifact to `tokintmash/icloud-sorter-releases`.

Before tagging, add this GitHub Actions secret in the source repo:

- `PUBLIC_RELEASES_TOKEN`: fine-grained PAT with `Contents: Read and write` access to `tokintmash/icloud-sorter-releases`

## Testing

```bash
# Backend tests (run from project root)
python -m pytest backend/tests/ -v

# Frontend tests
cd frontend
npm test
```

## How It Works

1. **Login** with your Apple ID (2FA supported)
2. **Browse** your iCloud photo albums
3. **Select** albums to sort
4. **Sort** — files already synced by iCloud for Windows are moved into album-named folders

## Disclaimer

### Unofficial Project

This project is **not affiliated with, endorsed by, or sponsored by Apple Inc.** in any way.

"iCloud" is a trademark of Apple Inc., registered in the U.S. and other countries.

### Apple Terms of Service

Use of this tool may be subject to Apple's [iCloud Terms of Service](https://www.apple.com/legal/internet-services/icloud/). By using this tool, you accept full responsibility for compliance with Apple's terms.

This tool accesses iCloud through the same web APIs used by icloud.com. It does not reverse-engineer, decompile, or modify any Apple software.

### No Warranty

This software is provided "as is", without warranty of any kind. See the [LICENSE](LICENSE) file for details.

### Your Data

- This tool runs entirely on your local machine
- Your Apple ID credentials are sent directly to Apple's authentication servers
- No credentials or personal data are sent to any third-party server
- Session cookies are stored locally in `~/.icloud-downloader/`

## License

All rights reserved. Licensing to be determined.
