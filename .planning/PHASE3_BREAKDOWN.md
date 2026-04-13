# Phase 3: Polish & Package — Breakdown

Phase 3 from `PLANNING_SORTER_v2.md` is split into 6 independent sub-phases with clear dependencies.

---

## Phase 3A: Cross-Album Duplicate Handling

**Status:** Not started  
**Dependencies:** None (standalone)

### Requirements
- Add setting for "copy to each album" vs "move to first album only"
- Enable the currently-greyed-out option in Settings UI
- Update `sorter_service.py` to support copy mode (`shutil.copy2` alongside `shutil.move`)
- Update `state_service.py` if schema changes are needed (e.g., tracking which album a file was moved to)
- Update `PUT /api/settings` to accept and persist the new option
- Frontend: enable the disabled radio buttons in Settings

### Acceptance Criteria
- User can choose between copy and move for cross-album duplicates
- Copy mode: file appears in every album folder it belongs to
- Move mode (current default): file moves to first album, skipped in subsequent
- Setting persists across app restarts

---

## Phase 3B: Desktop Packaging

**Status:** Not started  
**Dependencies:** None (standalone)

### Requirements
- Bundle backend + frontend into a single distributable `.exe`
- Decide packaging approach:
  - **Option A: PyInstaller** — bundle Python backend + pre-built `frontend/dist/` into one executable
  - **Option B: Electron** — wrap React frontend in Electron, spawn Python backend as child process
- Auto-detect iCloud folder on first launch (registry lookup + known paths)
- App should launch with a single click — no Python/Node installation required
- Installer or portable `.exe`

### Acceptance Criteria
- User downloads one file, runs it, app opens in browser or native window
- No manual dependency installation required
- Works on Windows 10/11 x64

---

## Phase 3C: CI/CD for Builds & Releases

**Status:** Not started  
**Dependencies:** Phase 3B (needs a package to build)

### Requirements
- GitHub Actions workflow (`.github/workflows/build.yml`):
  - Lint (Python + TypeScript)
  - Run tests (pytest + vitest if applicable)
  - Build frontend (`npm run build`)
  - Build packaged `.exe` (from Phase 3B)
- Automated release: on git tag push, create GitHub Release with `.exe` artifact
- Runs on GitHub-hosted Windows runners (free for public repos, 2000 mins/month for private)

### Acceptance Criteria
- Push to `main` triggers lint + test + build
- Pushing a `v*` tag creates a GitHub Release with downloadable `.exe`
- Build failures block merge (branch protection)

### Infrastructure Notes
- **No VM or web page required** — GitHub Actions provides free Windows runners
- Public repos: unlimited minutes; private repos: 2000 mins/month free tier

---

## Phase 3D: Code Signing

**Status:** Not started  
**Dependencies:** Phase 3B + Phase 3C

### Requirements
- Obtain a Windows code-signing certificate (e.g., SSL.com OV certificate, ~$70/year)
- Integrate `signtool.exe` or equivalent into CI/CD pipeline
- Sign the `.exe` and/or installer during the build process
- Removes "Windows protected your PC" SmartScreen warning for users

### Acceptance Criteria
- Built `.exe` is signed with a valid certificate
- SmartScreen does not block the app on first run
- Signing is automated in CI/CD (certificate stored as GitHub secret)

### Blockers
- Requires purchasing a code-signing certificate
- Some CAs require identity verification (can take days)

---

## Phase 3E: Website + Purchase Flow

**Status:** Not started  
**Dependencies:** None (standalone)

### Requirements
- Landing page with:
  - Product description and screenshots
  - Download link (or purchase button if licensing is added)
  - System requirements (Windows 10/11, iCloud for Windows installed)
- Hosting options (all free tier):
  - GitHub Pages (simplest, from the same repo)
  - Vercel or Netlify (more features, custom domain support)
- Custom domain (optional, ~$10/year)

### Acceptance Criteria
- Public URL serves a landing page describing the app
- Download link points to latest GitHub Release (or purchase flow)
- Page is responsive and professional-looking

---

## Phase 3F: Licensing Integration

**Status:** Not started  
**Dependencies:** Phase 3B (packaged app) + Phase 3E (purchase flow)

### Requirements
- Choose a licensing provider:
  - **LemonSqueezy** — handles payments + license key generation
  - **Keygen.sh** — license key validation API
  - **Gumroad** — simple purchase + license keys
- Integrate license key validation in the app:
  - On first launch, prompt for license key
  - Validate key against provider API
  - Cache validation locally (allow offline use after initial validation)
- Optional: trial period (e.g., 7 days or 3 sorts) before requiring a license
- Purchase flow on website (Phase 3E) generates license keys

### Acceptance Criteria
- App requires a valid license key to operate (or runs in trial mode)
- Purchasing on the website provides a license key
- License validation works online; cached validation allows offline use
- Invalid/expired keys show a clear error with link to purchase

---

## Dependency Graph

```
Phase 3A (Cross-Album Duplicates)     ── standalone
Phase 3E (Website + Purchase Flow)    ── standalone

Phase 3B (Desktop Packaging)
  └─▶ Phase 3C (CI/CD)
        └─▶ Phase 3D (Code Signing)

Phase 3B (Desktop Packaging) ─┐
Phase 3E (Website)            ├─▶ Phase 3F (Licensing)
                              │
```

## Suggested Implementation Order

1. **3A** — small, self-contained feature improvement
2. **3B** — packaging (unlocks everything else)
3. **3E** — website (can be done in parallel with 3B)
4. **3C** — CI/CD (after 3B)
5. **3D** — code signing (after 3C)
6. **3F** — licensing (after 3B + 3E)
