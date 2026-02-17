# iCloud Photo Downloader — Planning Document

*February 17, 2026 — For Team Review Before Implementation*

---

## Table of Contents

1. [Executive Summary & Recommendation](#1-executive-summary--recommendation)
2. [Technology Stack](#2-technology-stack)
3. [iCloud API Approach](#3-icloud-api-approach)
4. [Architecture](#4-architecture)
5. [Data Model & State Management](#5-data-model--state-management)
6. [Media Type Handling](#6-media-type-handling)
7. [Filename & Deduplication Strategy](#7-filename--deduplication-strategy)
8. [Download Pipeline](#8-download-pipeline)
9. [Project Structure](#9-project-structure)
10. [Packaging & Signing Plan](#10-packaging--signing-plan)
11. [Risk Assessment Summary](#11-risk-assessment-summary)
12. [Open Questions for Team Decision](#12-open-questions-for-team-decision)
13. [Implementation Phases](#13-implementation-phases)

---

## 1. Executive Summary & Recommendation

### Top Recommendation: Wails (Go) + Embedded Python (pyicloud)

**Stack:** Go backend via Wails v2, React/TypeScript frontend, Python subprocess using `pyicloud` (timlaing fork) for iCloud API access, SQLite for state management.

**Rationale:**
- **Team fit:** Go is the team's strength; Go's goroutine model is ideal for concurrent downloads with cancellation and progress reporting
- **pyicloud is battle-tested:** Rather than reimplementing Apple's SRP auth + CloudKit APIs in Go (months of work, high risk), we embed Python as a subprocess for the API layer. This is the same approach docker-icloudpd uses — wrapping the proven library
- **Right-sized:** 8–19 MB bundle vs Electron's 100+ MB. This app is a download manager, not a web browser
- **Web frontend flexibility:** Team knows JS; full CSS/HTML control for a polished progress UI
- **Wails auto-generates TypeScript bindings** from Go structs, giving type-safe backend↔frontend communication

### Alternative: Electron (JavaScript/TypeScript)

Choose Electron if:
- Auto-update is a hard Day-1 requirement (Electron has the most mature updater)
- Minimizing packaging/signing DevOps is the priority
- Bundle size (100+ MB) is an acceptable tradeoff for developer velocity

The iCloud API would still need pyicloud (via a bundled Python runtime or a ported Node.js implementation using the `apple-icloud` npm package, though that's less maintained).

---

## 2. Technology Stack

### Primary Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **GUI Framework** | Wails v2.11 (Go + web frontend) | Team knows Go; small bundles; native webview |
| **Frontend** | React + TypeScript | Team knows JS; rich ecosystem for progress UIs |
| **iCloud API** | Python `pyicloud` v2.x (timlaing fork) via subprocess | Only actively maintained iCloud library with SRP, 2FA, Photos API |
| **State DB** | SQLite (via `modernc.org/sqlite` — pure Go, no CGo) | Single file, zero setup, embedded, fast |
| **Keychain** | `zalando/go-keyring` | Cross-platform OS keychain access (macOS Keychain, Windows Credential Manager, libsecret on Linux) |
| **Logging** | `zerolog` or `slog` (Go stdlib) | Structured logging, file + console output |
| **Build** | Go modules + npm/pnpm for frontend | Standard tooling |

### Python Bridge Architecture

The Go backend spawns a long-running Python subprocess that exposes a JSON-RPC (or simple JSON-over-stdin/stdout) interface:

```
┌──────────────────────────────────────────────────────┐
│  Wails App                                           │
│  ┌────────────────┐    ┌───────────────────────┐     │
│  │  React Frontend│◄──►│   Go Backend           │    │
│  │  (TypeScript)  │    │   - Download manager   │    │
│  │  - Album list  │    │   - SQLite state       │    │
│  │  - Progress UI │    │   - File I/O           │    │
│  │  - Settings    │    │   - Concurrency ctrl   │    │
│  └────────────────┘    │   - Keychain access    │    │
│                        │                         │    │
│                        │   ┌─────────────────┐   │    │
│                        │   │ Python Bridge    │   │    │
│                        │   │ (subprocess)     │   │    │
│                        │   │ - pyicloud auth  │   │    │
│                        │   │ - Album listing  │   │    │
│                        │   │ - Asset metadata │   │    │
│                        │   │ - Download URLs  │   │    │
│                        │   └─────────────────┘   │    │
│                        └───────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Why subprocess, not reimplementation:**
- Apple's SRP auth is complex and changes frequently (broke 2x in 2023-2024)
- pyicloud's timlaing fork has an active community fixing auth issues within days
- Reimplementing in Go would take months and leave us maintaining our own auth code
- The subprocess pattern is proven (docker-icloudpd, icloudpd-web)
- Python runtime is bundled with the app (~15–20 MB, or we require users to have Python installed)

**[TEAM DECISION NEEDED]:** Bundle Python runtime with the app (larger bundle, zero user setup) or require Python 3.10+ pre-installed (smaller bundle, user friction)?

---

## 3. iCloud API Approach

### Library: pyicloud v2.x (timlaing/pyicloud)

| Attribute | Value |
|-----------|-------|
| **PyPI Package** | `pyicloud` v2.3.0 (Jan 2026) |
| **Auth** | SRP-6a, 2FA (trusted device, SMS, FIDO2), session persistence |
| **Photos API** | Album listing, asset iteration with pagination, original/medium/thumb/adjusted downloads |
| **Session Lifetime** | ~2 months, then re-auth with 2FA required |
| **License** | MIT |

### What the API Provides

- **Albums:** User-created albums + "All Photos". NOT shared albums, smart albums, or Recently Deleted
- **Per asset:** ID, filename, size, dimensions, creation date, versions (original/medium/thumb/adjusted)
- **Download:** Pre-signed, time-limited CDN URLs via `photo.download(version)`
- **Pagination:** Cursor-based, ~200 records/page, handled transparently by pyicloud

### User Prerequisites (Must Document Prominently)

1. **Enable** "Access iCloud Data on the Web" in iOS Settings → Apple ID → iCloud
2. **Disable** Advanced Data Protection (ADP) — Apple returns `ACCESS_DENIED` otherwise
3. Accept any pending iCloud Terms of Service

### Rate Limiting Strategy

| Parameter | Default | Configurable |
|-----------|---------|-------------|
| Concurrent downloads | 3 | Yes (1–10) |
| Delay between metadata API calls | 200ms | Yes |
| Retry on 503 | Exponential backoff starting at 30s | Yes |
| Max retries per asset | 3 | Yes |
| Auth retry | Max 2 attempts, then wait 5 min | No |

---

## 4. Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (React + TypeScript)                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │  Auth     │ │  Album   │ │ Download │ │  Settings         │  │
│  │  Screen   │ │  Browser │ │ Progress │ │  (paths, proxy,   │  │
│  │  (2FA)    │ │  (select)│ │ (live)   │ │   concurrency)    │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │ Wails bindings (auto-generated TS)
┌─────────────────────────────────────────────────────────────────┐
│  GO BACKEND                                                      │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  AuthService  │  │ AlbumService │  │  DownloadService       │ │
│  │  - Login      │  │ - ListAlbums │  │  - Worker pool         │ │
│  │  - 2FA verify │  │ - GetAssets  │  │  - Atomic writes       │ │
│  │  - Session    │  │ - Pagination │  │  - Progress tracking   │ │
│  │    refresh    │  │              │  │  - Pause/Cancel/Resume │ │
│  └──────┬───────┘  └──────┬───────┘  │  - Retry logic         │ │
│         │                  │          └──────────┬─────────────┘ │
│         ▼                  ▼                     │               │
│  ┌─────────────────────────────────┐             │               │
│  │  iCloudBridge (Python subprocess)│◄────────────┘              │
│  │  JSON-RPC over stdin/stdout      │                            │
│  └─────────────────────────────────┘                             │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  StateDB      │  │  Keychain    │  │  Logger                │ │
│  │  (SQLite)     │  │  (go-keyring)│  │  (zerolog/slog)        │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Threading / Concurrency Model

Go's goroutine model handles this naturally:

- **Main goroutine:** Wails event loop + frontend communication
- **Python bridge goroutine:** Manages the Python subprocess lifecycle, sends requests, reads responses
- **Download worker pool:** `N` goroutines (configurable, default 3) pulling from a job channel
- **Progress reporter goroutine:** Aggregates per-file progress into per-album and overall stats, emits events to frontend via Wails `runtime.EventsEmit`
- **Cancellation:** Go's `context.Context` propagates cancel signals to all goroutines

```go
// Simplified worker pool pattern
func (s *DownloadService) Start(ctx context.Context, jobs <-chan DownloadJob) {
    var wg sync.WaitGroup
    for i := 0; i < s.concurrency; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    return
                default:
                    s.downloadOne(ctx, job)
                }
            }
        }()
    }
    wg.Wait()
}
```

### Error Handling & Retry Strategy

| Error Type | Action |
|-----------|--------|
| HTTP 503 (throttled) | Retry with exponential backoff; honor `retryAfter` header |
| HTTP 401/403 (auth expired) | Re-authenticate via Python bridge; if 2FA needed, prompt user |
| Network timeout | Retry up to 3 times with backoff |
| Disk write error | Fail the asset, log error, continue with next |
| Disk space exhausted | Pause all downloads, alert user |
| Python bridge crash | Restart subprocess, re-establish session |

### Logging

- **File log:** `~/.icloud-downloader/logs/YYYY-MM-DD.log` — structured JSON, rotated daily, 7-day retention
- **Console log:** Human-readable, shown in a "Log" tab in the GUI
- **Sensitive data:** Redact credentials, tokens, and email addresses in all logs
- **Log levels:** DEBUG (verbose API calls), INFO (operations), WARN (retries), ERROR (failures)

---

## 5. Data Model & State Management

### SQLite Schema

```sql
-- Track iCloud sessions
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY,
    apple_id    TEXT NOT NULL,
    cookie_dir  TEXT NOT NULL,  -- path to pyicloud cookie directory
    created_at  TEXT NOT NULL,
    expires_at  TEXT,           -- estimated expiry (~2 months from auth)
    last_used   TEXT NOT NULL
);

-- Albums discovered from iCloud
CREATE TABLE albums (
    id              TEXT PRIMARY KEY,   -- iCloud album ID
    name            TEXT NOT NULL,
    asset_count     INTEGER,
    last_synced_at  TEXT,
    folder_name     TEXT NOT NULL       -- sanitized filesystem name
);

-- Assets (photos/videos) in iCloud
CREATE TABLE assets (
    id              TEXT PRIMARY KEY,   -- iCloud asset ID (CloudKit record name)
    filename        TEXT NOT NULL,      -- original filename from iCloud
    size_bytes      INTEGER,
    item_type       TEXT,               -- 'image', 'video', 'live_photo'
    created_at      TEXT,               -- EXIF creation date
    has_adjustments  INTEGER DEFAULT 0, -- 1 if edited version exists
    width           INTEGER,
    height          INTEGER,
    checksum        TEXT                -- if available from API
);

-- Junction: which assets belong to which albums
CREATE TABLE album_assets (
    album_id    TEXT NOT NULL REFERENCES albums(id),
    asset_id    TEXT NOT NULL REFERENCES assets(id),
    position    INTEGER,                -- sort order within album
    PRIMARY KEY (album_id, asset_id)
);

-- Download tracking
CREATE TABLE downloads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    album_id        TEXT NOT NULL REFERENCES albums(id),
    version         TEXT NOT NULL,      -- 'original', 'adjusted'
    local_path      TEXT,               -- relative path from download root
    status          TEXT NOT NULL DEFAULT 'pending',
                    -- 'pending', 'downloading', 'complete', 'failed', 'skipped'
    file_size       INTEGER,
    bytes_downloaded INTEGER DEFAULT 0,
    error_message   TEXT,
    attempts        INTEGER DEFAULT 0,
    started_at      TEXT,
    completed_at    TEXT,
    UNIQUE(asset_id, album_id, version)
);

-- Indexes
CREATE INDEX idx_downloads_status ON downloads(status);
CREATE INDEX idx_downloads_album ON downloads(album_id, status);
CREATE INDEX idx_album_assets_album ON album_assets(album_id);
```

### Deduplication Key

**Primary key:** iCloud asset ID (CloudKit record name) — globally unique, stable across sessions.

**Incremental sync logic:**
1. Query iCloud for album assets (paginated)
2. For each asset, check `downloads` table: if `status = 'complete'` AND `file_size` matches, skip
3. If `status = 'failed'` and `attempts < max_retries`, retry
4. If asset not in DB, insert as `pending`

### State DB Location

`~/.icloud-downloader/state.db` — separate from the download directory so users can move/change download locations without losing state.

---

## 6. Media Type Handling

### Policy Summary

| Media Type | Policy | Naming |
|-----------|--------|--------|
| **JPEG/PNG** | Download original | `IMG_1234.JPG` |
| **HEIC** | Download original; optional conversion as post-process | `IMG_1234.HEIC` |
| **Live Photos** | Download both image + video | `IMG_1234.HEIC` + `IMG_1234.MOV` |
| **Edited photos** | Download original by default; both if user opts in | `IMG_1234.HEIC` (original) + `IMG_1234_edited.HEIC` |
| **RAW+JPEG** | Download both files | `IMG_1234.DNG` + `IMG_1234.JPG` (names usually differ naturally) |
| **Bursts** | Key photo only by default; all frames if user opts in | Standard naming per frame |
| **Panoramas** | Treat as regular photos | Standard naming |
| **Videos** | Download as-is | Original filename |

### Detailed Policies

**Live Photos:**
- Download both the still image and MOV video component
- They share the same base filename naturally from iCloud
- Stored in the same album folder side by side
- No special linking needed — filesystem proximity and matching names are sufficient

**HEIC/HEVC — [TEAM DECISION NEEDED]:**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A: Originals only** | Simplest, fastest, preserves quality | Users on Windows may struggle to view HEIC | ✅ **Recommended for v1** |
| **B: Optional conversion** | User-friendly | Requires bundling ffmpeg/libheif, adds complexity, doubles processing time | v2 feature |
| **C: Always convert** | Maximum compatibility | Lossy, destroys original quality, slow | ❌ Not recommended |

If conversion is added later (v2), it should be a **post-download** step using `libheif` or `ffmpeg`, configurable in settings.

**Edited vs. Original — [TEAM DECISION NEEDED]:**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A: Originals only (default)** | Simpler, smaller download, lossless | User may want their edits | ✅ **Recommended default** |
| **B: Both (opt-in)** | Complete backup | Nearly doubles download for edited photos | Setting: "Include edited versions" |
| **C: Edited only** | What user "sees" in Photos | Loses original data | ❌ Not recommended |

**Bursts — [TEAM DECISION NEEDED]:**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A: Key photo only (default)** | Smaller download, what user chose | Loses burst frames | ✅ **Recommended default** |
| **B: All frames (opt-in)** | Complete backup | Many files per burst (10-100+) | Setting: "Download all burst frames" |

Note: The web API may not clearly mark the "key photo" — if this metadata isn't available, default to downloading all frames.

### Album Scope

| Album Type | In Scope | Notes |
|-----------|----------|-------|
| **User-created albums** | ✅ Yes | Core feature |
| **"All Photos"** | ✅ Yes | As a special album option |
| **Favorites** | ✅ Yes (v2) | Filterable via asset metadata |
| **Shared Albums** | ❌ No | Different API, not supported by pyicloud |
| **Smart Albums** | ⚠️ Partial | Some system albums visible (Screenshots, Selfies); include if API provides them |
| **Recently Deleted** | ❌ No | Not exposed via web API |

---

## 7. Filename & Deduplication Strategy

### Collision Resolution (Within Album Folder)

**Strategy: Append date, then sequence number on further collision.**

```
IMG_0001.HEIC                    ← first occurrence
IMG_0001_2024-03-15.HEIC         ← second, different asset, append EXIF date
IMG_0001_2024-03-15 (2).HEIC     ← third, same date collision, append sequence
IMG_0001_2024-07-22.HEIC         ← fourth, different date
```

**Rationale:**
- Date suffix is human-readable and helps users identify photos
- Sequence number handles the rare case of same filename + same date
- Avoids opaque asset IDs in filenames (user-hostile)
- The collision check uses the `downloads` table, not filesystem scanning (faster, works even if files are moved)

**Algorithm:**
```
1. Start with original filename: "IMG_0001.HEIC"
2. Check downloads table for this (album_id, local_path) combo
3. If exists AND belongs to a different asset_id:
   a. Append date: "IMG_0001_2024-03-15.HEIC"
   b. If still collides, append sequence: "IMG_0001_2024-03-15 (2).HEIC"
4. Store final local_path in downloads table
```

### Cross-Album Duplicates

**Strategy: Download the file into each album folder independently.**

**Rationale:**
- **Simplest implementation** — no symlink/hardlink complexity
- **Works on all platforms** — Windows symlinks require admin privileges; hardlinks don't work across drives
- **Most predictable for users** — each album folder is self-contained and portable
- **Disk space tradeoff is acceptable** — most users won't download 20 overlapping albums; photos are typically a few MB each
- If disk space becomes a concern for power users, hardlinks can be added as a v2 opt-in feature (easy to add later, hard to remove)

**Dedup optimization:** Even though we download to each album folder, we can avoid re-downloading from iCloud by checking if the same `asset_id + version` already exists in the `downloads` table with `status = 'complete'`. If so, we **copy the local file** instead of re-downloading.

### Filesystem Name Sanitization

Album names → folder names:
```
1. Replace characters invalid on any OS: / \ : * ? " < > |  → _
2. Trim leading/trailing whitespace and dots
3. Truncate to 200 characters (leave room for filenames within)
4. If empty after sanitization, use "Unnamed Album"
5. If folder name collides, append " (2)", " (3)", etc.
```

---

## 8. Download Pipeline

### Atomic Writes

```
1. Create temp file: <album_folder>/.IMG_1234.HEIC.tmp
2. Stream download data to temp file
3. On completion: verify size matches expected
4. Rename: .IMG_1234.HEIC.tmp → IMG_1234.HEIC (atomic on same filesystem)
5. Update downloads table: status = 'complete'
```

Temp files use a `.` prefix (hidden on Unix) and `.tmp` suffix. On app startup, any leftover `.tmp` files indicate interrupted downloads and are deleted.

### Resume Support

HTTP Range headers could theoretically resume partial downloads, but Apple's pre-signed CDN URLs are **time-limited** (expire within hours). By the time a user resumes, the URL is likely expired and a new one must be requested. Therefore:

**Policy:** No partial file resume. Delete `.tmp` files on restart and re-download from scratch. This is simpler and more reliable. Individual photos are typically 2–10 MB (seconds to re-download).

**Exception:** For large videos (1+ GB), we could implement Range-based resume with a fresh download URL. This is a v2 optimization.

### Pause / Cancel

| Action | Behavior |
|--------|----------|
| **Pause** | Stop dispatching new jobs to worker pool. Let in-flight downloads complete (they're typically seconds away). Update UI to "Paused". Jobs remain in the channel. |
| **Resume** | Start dispatching jobs again from where we left off. |
| **Cancel** | Cancel the Go context (cancels in-flight HTTP requests). Delete any `.tmp` files. Mark remaining `pending` jobs as `skipped`. |

### Disk Space Checking

```
1. Before starting: sum expected sizes of all pending downloads
2. Check available disk space on target volume
3. If insufficient: show warning with required vs available space; let user proceed or cancel
4. During download: re-check every 100 files or 1 GB downloaded
5. If space runs low (<500 MB remaining): pause downloads, alert user
```

### Concurrent Downloads

```
Worker Pool:
  - Default: 3 concurrent downloads
  - Configurable: 1–10 via settings
  - Each worker: goroutine pulling from a buffered channel
  - Rate limiter: token bucket shared across workers (configurable requests/sec)

Download URL refresh:
  - URLs expire within hours
  - Request URLs in small batches (50 at a time) to avoid expiry
  - If URL returns 403, request a fresh URL from pyicloud
```

### Proxy Support

Proxy settings configurable in the Settings UI:
- HTTP proxy: `http://host:port`
- SOCKS5 proxy: `socks5://host:port`
- Proxy authentication: username/password
- Applied to both Go HTTP client and Python subprocess (via `HTTP_PROXY`/`HTTPS_PROXY` env vars)

---

## 9. Project Structure

```
icloud-downloader/
├── main.go                     # Wails app entry point
├── app.go                      # Wails app struct + lifecycle
├── wails.json                  # Wails config
├── go.mod / go.sum
├── build/                      # Wails build assets
│   ├── appicon.png
│   ├── darwin/                 # macOS-specific (Info.plist, entitlements)
│   ├── windows/                # Windows-specific (manifest, icon.ico)
│   └── linux/
│
├── internal/                   # Go backend packages
│   ├── icloud/                 # Python bridge + iCloud types
│   │   ├── bridge.go           # Subprocess management, JSON-RPC communication
│   │   ├── types.go            # Go types for albums, assets, auth state
│   │   └── bridge_test.go
│   ├── downloader/             # Download pipeline
│   │   ├── service.go          # Worker pool, job dispatch
│   │   ├── atomic.go           # Atomic file writes
│   │   ├── progress.go         # Progress tracking + event emission
│   │   └── service_test.go
│   ├── state/                  # SQLite state management
│   │   ├── db.go               # Schema, migrations, queries
│   │   ├── models.go           # DB models
│   │   └── db_test.go
│   ├── keychain/               # OS keychain integration
│   │   └── keychain.go
│   ├── config/                 # App configuration
│   │   └── config.go           # Settings struct, load/save
│   └── logger/                 # Logging setup
│       └── logger.go
│
├── python/                     # Python iCloud bridge
│   ├── bridge.py               # Main bridge script (JSON-RPC over stdio)
│   ├── requirements.txt        # pyicloud, etc.
│   └── README.md
│
├── frontend/                   # React + TypeScript (Wails frontend)
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── AuthScreen.tsx
│   │   │   ├── AlbumBrowser.tsx
│   │   │   ├── DownloadProgress.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── LogViewer.tsx
│   │   ├── hooks/              # React hooks for backend calls
│   │   ├── types/              # Auto-generated from Go (wails generate)
│   │   └── styles/
│   └── index.html
│
├── scripts/                    # Build & release scripts
│   ├── build-macos.sh          # Sign + notarize
│   ├── build-windows.ps1       # Sign + NSIS installer
│   ├── build-linux.sh          # AppImage packaging
│   └── bundle-python.sh        # Bundle Python runtime
│
├── docs/
│   ├── PREREQUISITES.md        # User setup guide (iCloud settings)
│   ├── ARCHITECTURE.md
│   └── DEVELOPMENT.md
│
├── .github/
│   └── workflows/
│       ├── build.yml           # CI: test + build
│       └── release.yml         # CD: sign + notarize + publish
│
├── LICENSE                     # MIT
├── README.md
├── DISCLAIMER.md               # Apple TOS disclaimer
└── PLANNING.md                 # This document
```

---

## 10. Packaging & Signing Plan

### macOS

| Item | Detail | Cost |
|------|--------|------|
| **Apple Developer Program** | Required for Developer ID certificate | **$99/year** |
| **Certificate** | "Developer ID Application" + "Developer ID Installer" | Included in program |
| **Signing** | `codesign --deep --force --sign "Developer ID Application: ..."` | Automated in CI |
| **Notarization** | `xcrun notarytool submit` → wait → `xcrun stapler staple` | Automated in CI; typically <15 min |
| **Installer format** | DMG (drag to Applications) | Created via `create-dmg` |
| **Without signing** | Gatekeeper blocks entirely; user must right-click → Open. Hostile UX. | **Not acceptable for distribution** |

### Windows

| Item | Detail | Cost |
|------|--------|------|
| **Code signing** | OV certificate OR Azure Trusted Signing | **$200–$300/year** (OV) or **$120/year** (Azure, US/CA only) |
| **SmartScreen** | EV certs NO LONGER bypass SmartScreen (changed March 2024). Reputation builds organically. | N/A |
| **Installer format** | NSIS installer (.exe) | Free, scriptable |
| **Without signing** | SmartScreen shows scary "Windows protected your PC" warning. Most users won't proceed. | **Acceptable for initial beta, not for GA** |

**[TEAM DECISION NEEDED]:** Is the team/org based in US or Canada? If yes, Azure Trusted Signing ($10/mo) is the best Windows option.

### Linux

| Item | Detail | Cost |
|------|--------|------|
| **Format** | AppImage (single portable file) | Free |
| **Signing** | Not required; optional GPG signatures | Free |
| **Distribution** | GitHub Releases | Free |

### Auto-Update Strategy

Wails has no built-in auto-updater. Recommended approach:

| Platform | Solution |
|----------|----------|
| **macOS** | Sparkle framework (de facto standard for macOS apps) via CGo binding or bundled helper |
| **Windows** | WinSparkle (Sparkle port for Windows) via `go-winsparkle` |
| **Linux** | Check GitHub Releases API on startup; notify user of updates; manual download |
| **Update feed** | Appcast XML hosted on GitHub Pages or as part of GitHub Releases |

**Estimated effort:** 1–2 weeks of development. Can be deferred to post-v1.0.

### Estimated Annual Costs

| Item | Cost |
|------|------|
| Apple Developer Program | $99 |
| Windows code signing (OV) | $250 |
| **Total** | **~$350/year** |

With Azure Trusted Signing (if eligible): **~$220/year**

---

## 11. Risk Assessment Summary

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|-----------|------------|
| 1 | **Apple changes auth endpoints** | 🔴 High | Near-certain (1–2x/year) | Python bridge uses pyicloud; community fixes within days–weeks. Isolate API layer. |
| 2 | **Apple blocks non-browser clients** | 🔴 High | Medium | Browser mimicry; potential Playwright fallback as escape hatch |
| 3 | **Rate limiting / throttling** | 🟡 Medium | Likely for large libraries | Conservative defaults (3 concurrent, backoff); honor 503 retryAfter |
| 4 | **Session token compromise** | 🔴 High severity | Low if secured | OS keychain storage; never plaintext |
| 5 | **icloudpd/pyicloud ecosystem stagnation** | 🟡 Medium | Medium (maintainer seeking successor) | We depend on pyicloud for auth only; monitor and contribute fixes upstream |
| 6 | **Legal action from Apple** | 🟡 Medium severity | Very low | MIT license, disclaimers, interoperability framing; 9+ years of precedent with no action |
| 7 | **Python bundling complexity** | 🟡 Medium | Medium | Spike this early in Phase 1; fallback to requiring Python pre-installed |
| 8 | **Wails v2 → v3 migration** | 🟢 Low | Certain (v3 coming) | v3 migration is straightforward per maintainer; design for it |

### Critical Mitigation: API Abstraction Layer

All iCloud API interactions are behind a Go interface:

```go
type iCloudService interface {
    Authenticate(appleID, password string) (AuthResult, error)
    Verify2FA(code string) error
    TrustSession() error
    ListAlbums() ([]Album, error)
    GetAlbumAssets(albumID string) ([]Asset, error)
    GetDownloadURL(assetID, version string) (string, error)
    SessionValid() bool
}
```

The Python bridge implements this interface today. If needed, a pure-Go or pure-Node.js implementation can replace it without touching any other code.

---

## 12. Open Questions for Team Decision

These decisions should be resolved before implementation begins:

### High Priority

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | **Python bundling** | A) Bundle Python runtime (~15–20 MB added to package) <br> B) Require Python 3.10+ pre-installed <br> C) Rewrite iCloud client in Go (months of work) | **A for macOS/Windows, B for Linux**. Spike in Phase 1. |
| 2 | **HEIC conversion** | A) Originals only (v1) <br> B) Optional conversion (v1) | **A** — keep v1 simple. Add conversion in v2. |
| 3 | **Edited vs Original** | A) Originals only (default) <br> B) User chooses in settings | **B** — download originals by default, checkbox for "also download edited versions" |
| 4 | **Burst photos** | A) Key photo only <br> B) All frames <br> C) User chooses | **C** — default to key photo, setting to download all |
| 5 | **Auto-update for v1.0?** | A) Yes (adds ~2 weeks) <br> B) No (manual download from GitHub) | **B** — ship v1 without auto-update; add in v1.1 |

### Medium Priority

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 6 | **Team location (for Windows signing)** | US/Canada → Azure Trusted Signing ($10/mo) <br> Other → OV certificate ($250/year) | Depends on team |
| 7 | **License** | MIT vs Apache 2.0 | **MIT** — matches pyicloud and icloudpd |
| 8 | **Linux priority** | Nice-to-have vs required for v1 | Nice-to-have; Wails supports it but we don't invest in AppImage/signing until demand exists |
| 9 | **Open source?** | Open source from day 1 vs private initially | **Open source** — lower legal risk, community contributions, matches ecosystem |

---

## 13. Implementation Phases

### Phase 1: Foundation (Weeks 1–3)

**Goal:** Authenticate with iCloud and list albums in a GUI.

- [ ] Scaffold Wails project with React + TypeScript frontend
- [ ] Build Python bridge (JSON-RPC over stdin/stdout)
- [ ] Implement auth flow: login → 2FA → session persistence
- [ ] Implement album listing via pyicloud
- [ ] Build Auth screen (Apple ID, password, 2FA code entry)
- [ ] Build Album browser (list albums with asset counts)
- [ ] Set up SQLite schema and state management
- [ ] **Spike:** Python runtime bundling (test on macOS + Windows)

### Phase 2: Download Engine (Weeks 4–6)

**Goal:** Download selected albums with progress tracking.

- [ ] Implement download worker pool with configurable concurrency
- [ ] Atomic writes (temp → rename)
- [ ] Filename collision resolution
- [ ] Cross-album file copy optimization (avoid re-downloading)
- [ ] Per-file, per-album, and overall progress tracking
- [ ] Build Download Progress screen (live progress bars, speed, ETA)
- [ ] Disk space checking (pre-flight + periodic)
- [ ] Pause / Cancel / Resume support

### Phase 3: Robustness (Weeks 7–8)

**Goal:** Handle errors, edge cases, and large libraries.

- [ ] Retry logic with exponential backoff
- [ ] Handle auth re-prompts (session expired mid-download)
- [ ] Handle all media types (Live Photos, RAW pairs, edited versions)
- [ ] Logging system (file + GUI log viewer)
- [ ] Proxy support (HTTP/SOCKS5, configured in settings)
- [ ] Settings persistence (download path, concurrency, proxy, media options)
- [ ] Error reporting UI (per-file errors with retry option)

### Phase 4: Polish & Distribution (Weeks 9–10)

**Goal:** Production-ready packaging and distribution.

- [ ] macOS: Code signing + notarization + DMG
- [ ] Windows: Code signing + NSIS installer
- [ ] Linux: AppImage (if prioritized)
- [ ] CI/CD pipeline (GitHub Actions: test → build → sign → release)
- [ ] User documentation (prerequisites, usage guide)
- [ ] Beta testing with real iCloud libraries (small and large)
- [ ] Disclaimers and license

### Phase 5: Post-Launch (Ongoing)

- [ ] Auto-update (Sparkle/WinSparkle)
- [ ] HEIC → JPEG conversion option
- [ ] Favorites filter
- [ ] Shared album support (if API access becomes available)
- [ ] Monitor pyicloud/icloudpd for API changes; update bridge as needed

---

*This document should be reviewed and all items in [Section 12](#12-open-questions-for-team-decision) resolved before starting Phase 1.*
