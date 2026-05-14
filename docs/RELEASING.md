# Releasing

This document is for maintainers publishing release artifacts. General packaging instructions are in [PACKAGING.md](PACKAGING.md).

## Automated Release Flow

Push a version tag to trigger a GitHub Release in the public releases repository with the built ZIP artifact:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

The CI pipeline runs linting, tests, the frontend build, the PyInstaller desktop app build, the MSI build, and release artifact publishing.

The release workflow publishes `iCloudPhotoSorter-latest.zip` to `tokintmash/icloud-sorter-releases`. The ZIP contains the versioned MSI installer.

## Required Repository Secret

Before tagging, configure this GitHub Actions secret in the source repository:

- `PUBLIC_RELEASES_TOKEN`: fine-grained personal access token with `Contents: Read and write` access to `tokintmash/icloud-sorter-releases`

## Local Release Checks

Local release builds require Windows 10/11, PowerShell 5.1 or newer, Python build dependencies from `requirements-build.txt`, Node.js/npm, .NET SDK 8 or newer, and WiX Toolset CLI v5 or newer.

Before publishing a release tag, run the local verification steps that match CI:

```powershell
ruff check backend/
python -m pytest backend/tests/ -v
cd frontend
npm run lint
npm run test
npm run build
cd ..
.\scripts\build_msi.ps1
```

Verify the generated MSI in `dist\installer\` before tagging.
