# iCloud Photo Sorter

Organize your iCloud photos locally by album. The app reads iCloud album metadata, matches it to files already synced by iCloud for Windows, and moves or copies those local files into album-named folders. No photo or video downloading from iCloud is performed during sorting.

## Status

This project is currently in beta. It works for the core sorting flow, but you should treat it carefully, test with a small album first, and keep backups of important photos before running large sorts.

The app is focused on Windows and iCloud for Windows, where photos are already synced locally.

## What It Does

- Authenticates with iCloud and supports two-factor authentication
- Reads album names, asset filenames, and album membership metadata
- Finds matching files in your local iCloud Photos folder
- Moves files into album-named folders, or copies duplicates into each album when configured
- Shows live sorting progress and per-file errors

## What It Does Not Do

- It does not download photo or video binaries from iCloud during sorting
- It does not upload your files or photo library to a third-party service
- It does not modify Apple software or integrate with iCloud for Windows internals

## Features

- 🔐 Secure iCloud authentication with 2FA support
- 📁 Browse and select albums to sort
- 📊 Real-time sort progress via SSE
- 🗂️ Files moved or copied into album-named folders
- 🔄 Case-insensitive filename matching (Windows NTFS)
- ⚡ Collision handling and cross-album duplicate detection

## Requirements

- Windows 10/11
- iCloud for Windows installed and syncing photos locally
- Python 3.10+ and Node.js 18+ for local development

## Prerequisites

Before getting started, please read the [Prerequisites Guide](docs/PREREQUISITES.md) — you'll need to configure your iCloud account settings.

## Quick Start

From a local checkout:

```bash
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

## Architecture

- Backend: FastAPI with Pydantic schemas
- Frontend: React, TypeScript, and Vite
- Local state: SQLite in `~/.icloud-sorter/state.db`
- iCloud access: `pyicloud` for authentication and metadata
- Progress updates: Server-Sent Events
- Desktop packaging: PyInstaller and pywebview
- Windows installer: MSI built from the packaged app bundle

The accepted behavior is tracked in `openspec/specs/`. Historical planning notes live in `.planning/`, and future candidates live in `openspec/roadmap.md`.

## Development Process

This project was built using a structured agent-assisted development workflow.

The early phases were driven by Markdown planning files in `.planning/`: one agent researched the problem, another converted the research into an implementation plan, later agents split the plan into phases, implemented individual phases, and reviewed the resulting code.

More recent changes use OpenSpec. Accepted behavior lives in `openspec/specs/`, active changes live in `openspec/changes/`, and future ideas live in `openspec/roadmap.md`.

The goal was to keep AI assistance structured and reviewable: research, plan, split, implement, review, and update the source-of-truth documents as the project evolved.

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

**MSI build requirements:** Windows 10/11, PowerShell 5.1+, Python build dependencies, Node.js/npm, .NET SDK 8+, and WiX Toolset CLI v5+.

```powershell
.\scripts\build_msi.ps1
```

The MSI output is written to `dist\installer\`. See [Windows MSI Packaging](docs/PACKAGING.md) for local dependencies, signing expectations, and verification steps.

## Releasing

Maintainer release instructions live in [docs/RELEASING.md](docs/RELEASING.md).

## Testing

```bash
# Backend tests (run from project root)
python -m pytest backend/tests/ -v

# Frontend tests
cd frontend
npm test
```

## Contributing

Feedback, bug reports, and security observations are welcome.

Code contributions may require separate contributor terms before they can be accepted, because the project is source-available and the maintainer may offer official commercial binaries or commercial licenses in the future.

## How It Works

1. **Login** with your Apple ID (2FA supported)
2. **Browse** your iCloud photo albums
3. **Select** albums to sort
4. **Sort** — files already synced by iCloud for Windows are moved or copied into album-named folders

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
- Your Apple ID credentials are submitted to the local backend login flow and used only to authenticate with Apple/iCloud
- Your Apple ID password is not stored by the app
- No credentials or personal data are sent to any third-party server
- Session cookies and local state are stored locally in `~/.icloud-sorter/`

## License

This project is source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE).

Noncommercial use, review, modification, and redistribution are permitted under that license. Commercial use, commercial redistribution, resale, or paid hosting requires separate written permission from the maintainer.

This is not an OSI-approved open-source license.

Third-party dependencies are licensed by their respective authors under their own licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
