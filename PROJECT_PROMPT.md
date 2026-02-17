# Amp Project Kickoff Prompt

Use the following prompt to start a new Amp thread:

---

I want to plan and build a new desktop application: **iCloud Photo Downloader**.

## Goal

A GUI application that lets users safely authenticate with their iCloud account and download photos/videos organized by album — each album becomes a folder on disk.

## Core Requirements

1. **iCloud Authentication** — Support Apple ID login including 2FA/2SV. Must handle session persistence so users don't re-auth every run. No credentials should be stored in plaintext.
2. **Album Browsing** — List all iCloud Photo Library albums and let users select which ones to download.
3. **Download by Album** — Download selected albums into folders named after each album (e.g., `./Downloads/Vacation 2024/IMG_1234.jpg`). Preserve original filenames and metadata (EXIF).
4. **Incremental/Resume** — Skip already-downloaded files. Support resuming interrupted downloads.
5. **Progress UI** — Show per-album and overall progress with speed, ETA, and error reporting.
6. **Cross-platform GUI** — Must run on macOS and Windows at minimum. Linux is a nice-to-have.
7. **Safety & Privacy** — No telemetry, no third-party credential sharing. Credentials/session tokens stored securely (OS keychain or encrypted at rest). All iCloud communication over HTTPS.

## Team Experience

Our team is proficient in **PHP, JavaScript, Go, and C**, with some **Python** experience. Prefer a stack that leverages these skills — avoid languages we'd need to learn from scratch unless there's a compelling reason.

## Media Type Handling

iCloud Photos contains many asset types beyond simple JPEGs. The plan must address each of these:

- **Live Photos** — An image+video pair. Should we download both components? How do we keep them associated on disk?
- **HEIC/HEVC** — Should we offer conversion to JPEG/MP4 or download originals only? *(Decision needed during planning.)*
- **Edited vs. Original** — iCloud stores both. Should we download originals, edited versions, or both?
- **RAW files** — RAW+JPEG pairs need the same pairing strategy as Live Photos.
- **Bursts & Panoramas** — How should burst sequences be handled? All frames or just the key photo?
- **Shared Albums vs. Smart Albums** — These behave differently from regular albums at the API level. Define which album types are in scope.

## Filename & Deduplication Strategy

"Preserve original filenames" will collide immediately — `IMG_0001.HEIC` appears hundreds of times across different dates. The plan must define:

- **Collision resolution** — Strategy for duplicate filenames within a single album folder (e.g., append date, sequence number, or asset ID).
- **Cross-album duplicates** — The same asset can exist in multiple albums. Define the policy: duplicate the file into each folder, use symlinks/hardlinks, or download once and reference?
- **Dedup key** — What uniquely identifies an asset for incremental sync? (Asset ID, checksum, filename+size?)

## Operational Requirements

- **Disk space** — Check available disk space before starting downloads; warn or abort if insufficient.
- **Concurrent downloads** — Configurable limit on parallel downloads (respect rate limiting).
- **Atomic writes** — Download to a temp file, then rename on completion to avoid partial/corrupt files.
- **Pause/Cancel** — Users must be able to pause and cancel downloads mid-run without corrupting state.
- **Logging & diagnostics** — File-based logging for troubleshooting failed downloads, auth issues, and API errors.
- **Proxy support** — Users behind corporate proxies need to configure HTTP/SOCKS proxy settings.

## API Risk Tolerance

There is no official Apple API for accessing iCloud Photos programmatically. All known approaches use reverse-engineered endpoints (as used by `pyicloud` and `icloud-photos-downloader`). **We accept the risk of using reverse-engineered endpoints**, with the understanding that:

- Apple may change or break these endpoints without notice.
- The app should be designed to isolate the API layer so it can be updated independently.
- We will not redistribute Apple credentials or tokens; all auth happens on the user's own machine for their own account.

*(If the team's risk tolerance is different, update this section before planning begins.)*

## Packaging & Distribution

The plan must cover platform-specific distribution realities:

- **macOS** — Code signing and notarization are required for Gatekeeper to allow the app to run. Do we need an Apple Developer account ($99/year)?
- **Windows** — Unsigned apps trigger SmartScreen warnings. EV code signing certificates and their cost/process should be evaluated.
- **Auto-updates** — Strategy for delivering updates to users (built-in updater, app store, manual download?).
- **Installer format** — DMG/pkg for macOS, MSI/NSIS for Windows, AppImage/Flatpak for Linux.

## What I Need From You

Before writing any code, help me plan:

1. **Language & framework selection** — Evaluate options (Python + Qt/Tk, Rust + egui/Tauri, Electron, Go + Fyne, etc.) considering:
   - Maturity of iCloud/Apple authentication libraries
   - GUI framework quality and cross-platform support
   - Packaging/distribution ease (single binary or simple installer)
   - Performance for large libraries (50k+ photos)

2. **iCloud API approach** — Research how to interact with iCloud Photos:
   - Existing open-source libraries (e.g., `pyicloud`, `icloud-photos-downloader`)
   - Apple's official APIs vs reverse-engineered endpoints
   - Legal/TOS considerations
   - Handling of rate limiting and large libraries

3. **Architecture** — Propose a high-level architecture:
   - How auth, album listing, downloading, and GUI interact
   - Threading/async model for non-blocking downloads
   - State management (tracking what's downloaded)
   - Error handling and retry strategy
   - Atomic downloads (temp→rename), pause/cancel mechanics
   - Logging and diagnostics approach

4. **Media & filename strategy** — Recommend concrete policies for each media type, filename collisions, and cross-album deduplication (see sections above). Flag any decisions that need team input.

5. **Project structure** — Suggest a repo layout, build system, and dependency management approach.

6. **Packaging & signing plan** — Lay out what's needed for code signing, notarization, and distribution on each target platform, including costs and account requirements.

7. **Risk assessment** — What are the biggest risks (Apple blocking access, API changes, auth complexity) and how to mitigate them?

## Execution Strategy

Conduct the research phase using **parallel subagents** (Amp's Task tool). 
Spawn these research tasks simultaneously, then synthesize their outputs 
into a single planning document:

1. **iCloud API & Auth** — Research available libraries (pyicloud, icloud-photos-downloader, 
   etc.), how 2FA/session persistence works in practice, endpoint stability, rate limits, 
   and album/asset enumeration APIs.

2. **GUI Framework & Packaging** — Compare Electron/Tauri/Qt/Fyne against our team skills 
   (JS, Go, Python, C). Evaluate cross-platform packaging, code signing costs, 
   notarization, and auto-update strategies.

3. **Data Model & Media Strategy** — Design the download pipeline: asset identity keys, 
   local state DB (SQLite?), atomic writes, Live Photo/HEIC/edited-vs-original handling, 
   filename collision resolution, and cross-album dedup policy.

4. **Risk & Legal** — Assess reverse-engineered API risks, Apple TOS implications, 
   mitigation strategies, and what happens if endpoints break.

Please present your analysis as a structured document I can review before we start coding. Include your top recommendation with rationale, plus one alternative approach. **For any open questions marked above, list them explicitly so we can resolve them before implementation begins.**

---
