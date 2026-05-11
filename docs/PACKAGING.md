# Windows MSI Packaging

This project uses PyInstaller `onedir` output as the MSI payload. The MSI is intentionally a thin installer around `dist\iCloudPhotoSorter\` so runtime behavior stays independent from MSI-only side effects and remains compatible with a future MSIX package.

## Packaging Decisions

- MSI authoring tool: WiX Toolset CLI v5 or newer, invoked with `wix build`.
- Required local dependencies: Windows 10/11, PowerShell 5.1 or newer, Python build dependencies from `requirements-build.txt`, Node.js 18 or newer, npm, and WiX Toolset CLI on `PATH`.
- Product name: `iCloud Photo Sorter`.
- Manufacturer: `tokintmash`.
- Version source: `packaging\metadata.json`, overridable with `-Version` on the MSI build script.
- Upgrade code: `5F0502E9-2F53-4C08-A0DE-29B4A8C7A2A1`.
- Output naming: `dist\installer\iCloudPhotoSorter-<version>-x64.msi`.
- Install scope: per-user, under `%LocalAppData%\Programs\iCloud Photo Sorter`, with a Start Menu launch entry.

The per-user scope avoids requiring elevation for normal installs and avoids machine-wide PATH mutation, services, shell extensions, drivers, installer-time authentication, or installer-time iCloud folder detection.

The WiX authoring uses only declarative installer features: file components, a Start Menu shortcut, per-user uninstall metadata, and component removal. No MSI custom actions are required.

## Build The MSI Locally

From a clean checkout on Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-build.txt
cd frontend
npm install
cd ..

# Install WiX separately if `wix --version` is not available.
# Example: dotnet tool install --global wix --version 5.*
# You may need to reopen the shell after installing a .NET global tool.

.\scripts\build_msi.ps1
```

The script performs the full packaging flow:

1. Builds `frontend\dist`.
2. Builds the PyInstaller `onedir` bundle from `icloud_sorter.spec`.
3. Generates WiX payload authoring from `dist\iCloudPhotoSorter`.
4. Builds the MSI into `dist\installer`.

To reuse an existing PyInstaller bundle while iterating on WiX authoring:

```powershell
.\scripts\build_msi.ps1 -SkipBuild
```

To override the MSI version for a release build:

```powershell
.\scripts\build_msi.ps1 -Version 1.2.3
```

## Signing Expectations

Unsigned MSI files are acceptable for local development packaging tests. Release MSI files should be Authenticode-signed with the release certificate before distribution to reduce SmartScreen friction and align with future MSIX requirements. MSIX packaging will require signing; keep signing as a packaging/release step rather than a runtime dependency.

The current packaging scripts do not sign automatically because certificate storage and timestamping policy are release-environment concerns.

## Runtime Compatibility Notes

- Bundled frontend assets are loaded through `backend.runtime_paths.frontend_dist()`, which resolves to `frontend\dist` under the PyInstaller bundle root when frozen.
- App state is kept outside the install directory: SQLite state, settings, sessions, and cookies use `%USERPROFILE%\.icloud-sorter`.
- Photo sorting uses the configured iCloud Photos folder from settings and creates album folders under that configured photo root, not under the installed app directory.
- Normal launch is the packaged executable plus its local backend server. The MSI does not configure PATH, services, machine-wide runtime registry settings, or custom actions.

## Manual Verification Checklist

- MSI creation: run `.\scripts\build_msi.ps1` and confirm it writes `dist\installer\iCloudPhotoSorter-<version>-x64.msi`.
- Install: install the MSI for the current user and confirm app files appear under `%LocalAppData%\Programs\iCloud Photo Sorter`.
- Launch entry: confirm the Start Menu contains `iCloud Photo Sorter` and launches `iCloudPhotoSorter.exe`.
- Frontend serving: launch the installed app and confirm the desktop window serves the bundled UI without `npm run dev` or a separate browser server.
- User data separation: log in or save settings and confirm app state is written under `%USERPROFILE%\.icloud-sorter`, not the install directory.
- Photo location: perform a small sort against a test iCloud Photos folder and confirm file operations occur only in the configured folder.
- Side effects: confirm normal launch does not require PATH changes, machine-wide runtime registry writes, service registration, or custom actions.
- Uninstall: uninstall through Windows app management and confirm installed files and the Start Menu entry are removed.
- User data preservation: after uninstall, confirm `%USERPROFILE%\.icloud-sorter` and the configured iCloud Photos folder still exist.
- Clean Windows: verify install and launch on a clean Windows 10/11 environment with the declared prerequisites and WebView2 availability.
