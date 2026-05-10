# Roadmap

This file captures future product direction and historical phase context. It is not an accepted behavior spec. Accepted current behavior lives in `openspec/specs/`; active proposed work lives in `openspec/changes/`.

## Source Of Truth Model

```text
Current behavior:  openspec/specs/* + current code
Active changes:    openspec/changes/*
Future direction:  openspec/roadmap.md
Historical notes:  .planning/*
```

When a roadmap item becomes ready for implementation, create an OpenSpec change under `openspec/changes/<change-name>/`. After implementation and archival, update accepted behavior under `openspec/specs/*`.

## Shipped Or Accepted

### Cross-Album Duplicate Handling

Status: shipped/accepted.

The app supports `duplicate_handling` with two modes:

- `move_only`: default; the local file is moved once for the first processed album and subsequent duplicate memberships are not copied.
- `copy_to_each`: the file appears in every selected album folder where it belongs, using additional disk space.

This is current product behavior, not future scope. Future changes touching sorting or settings should preserve it unless explicitly changing duplicate behavior.

### Desktop Packaging

Status: shipped/accepted at the planning level.

The intended packaging approach is PyInstaller plus pywebview for a Windows executable with a native window and no required local Python/Node installation. Future packaging work should check current code and build scripts before assuming remaining scope.

### CI/CD For Builds And Releases

Status: exists/shipped.

The repository has a GitHub Actions workflow at `.github/workflows/build.yml` that runs linting, tests, frontend build, packaged executable build, artifact upload, and tagged release publication.

Current behavior includes:

- Push and pull-request CI on `master`.
- Manual `workflow_dispatch` builds.
- Python setup, dependency install, Ruff linting, and pytest.
- Node setup, frontend dependency install, TypeScript lint/test, and Vite build.
- Frontend build artifact upload.
- PyInstaller executable build on Windows runners.
- Tagged `v*` releases zipped and published to `tokintmash/icloud-sorter-releases` using `PUBLIC_RELEASES_TOKEN`.

Future work should treat CI/CD as an existing system to modify, not an unstarted feature.

## Future Candidates

### CI/CD Improvements

Goal: improve the existing GitHub Actions pipeline as release needs evolve.

Candidate improvements:

- Add or update branch protection expectations around required checks.
- Adjust release artifact publishing if the release repository, website, or download hosting changes.
- Add installer build steps if distribution moves beyond a portable executable folder/zip.
- Add code-signing steps once a certificate is available.
- Add website/download metadata publishing if release distribution is automated through WordPress or another host.

### Code Signing

Goal: reduce Windows SmartScreen friction by signing release artifacts.

Candidate requirements:

- Purchase or obtain a Windows code-signing certificate.
- Integrate signing into the build/release pipeline.
- Store signing credentials securely in CI secrets.
- Sign the executable and/or installer during release builds.

Dependencies:

- CI/CD release pipeline.
- Code-signing certificate and identity verification.

### Website And Purchase Flow

Goal: provide a public product site, explain the app, and route purchases or downloads through controlled URLs.

Candidate direction:

- WordPress marketing site.
- Lemon Squeezy hosted checkout for paid purchases.
- Canonical `/buy/` route for purchase CTAs.
- Managed `/download/` route for the latest Windows build.
- Pages for home, how it works, prerequisites, FAQ, support, purchase success, and purchase cancelled.
- Messaging should emphasize local synced files, no iCloud binary downloads during sorting, Apple/iCloud authentication, and Windows/iCloud for Windows prerequisites.

Current assumption:

- First paid website launch may use purchase plus download-link fulfillment without in-app license enforcement.

### Licensing Integration

Goal: require a valid license or trial status inside the app before unrestricted use.

Candidate requirements:

- Choose a provider such as Lemon Squeezy, Keygen.sh, or Gumroad.
- Prompt for a license key on first launch or after trial expiry.
- Validate license keys online.
- Cache successful validation locally for offline use after initial activation.
- Show clear invalid or expired license messaging with a purchase link.

Dependencies:

- Packaged app.
- Purchase flow or license-key issuing provider.

Open question:

- Whether the first paid launch needs in-app enforcement, or whether download-link fulfillment is enough initially.

### Beta Expiry Removal Before v1.0

Goal: remove beta-expiration behavior before a stable v1.0 release.

Candidate cleanup areas:

- Backend beta endpoint and beta stamp module/script.
- Frontend beta status API type and hook.
- App initialization, expired screen, and beta banner rendering.
- Beta banner CSS.
- Build script beta stamping.
- `.gitignore` entry for generated beta stamp files.

Trigger:

- Before v1.0 or any non-beta public paid release.

### Release Distribution Automation

Goal: keep public download links current without manual link edits across the website.

Candidate options:

- Publish release assets to a public GitHub releases repo.
- Store one managed download URL in WordPress.
- Later, update WordPress release metadata via the WordPress REST API.
- Optional version history page or release archive.

Dependencies:

- Website/download route.
- CI/CD release workflow.

### Move With Cross-Reference Report

Goal: add a third duplicate mode that avoids extra disk usage while preserving album-membership information.

Candidate behavior:

- Move each duplicate file once.
- Generate a CSV or similar report listing additional album memberships.
- Use zero extra photo/video disk space beyond the single moved file.

Relationship to current behavior:

- This would be additive to existing `move_only` and `copy_to_each` modes.

## Not Currently Planned As Baseline Requirements

- Backend consent audit logging.
- External consent storage.
- WebSockets for sort progress.
- Downloading original photo/video binaries from iCloud as part of sorting.
- Replacing SQLite with a server database.
