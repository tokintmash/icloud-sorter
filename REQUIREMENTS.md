# iCloud Photo Downloader — Business Requirements

*What the app must do from the user's perspective.*

---

## Target User

iPhone/iPad users **without a Mac** who want to download their iCloud photos organized by album to free up iCloud storage. The app does **not** delete anything from iCloud.

## Core Problem

iCloud's web interface limits downloads to 1,000 images at a time, doesn't preserve album structure, and provides no tracking of what's already been downloaded. Users with large libraries (thousands of photos, many in RAW at 70+ MB each) must manually batch, track, and organize their downloads — a tedious, error-prone process that can take days.

**This app solves that.** The core value is making it easy to download a large number of photos with full tracking of what has and hasn't been downloaded, and the ability to **resume at any point**.

## User Prerequisites

Before using the app, users must:

1. Enable "Access iCloud Data on the Web" (iOS Settings → Apple ID → iCloud)
2. Disable Advanced Data Protection (ADP)
3. Accept any pending iCloud Terms of Service

These must be documented prominently in the UI (e.g., a help link or pre-login checklist).

---

## Screens & User Flow

### 1. Login Screen

- **Inputs:** Apple ID (email) + password
- **Credential disclaimer** must be visible: "Your credentials are sent to our server. This is a school project — use at your own risk."
- On success → prompt for 2FA code
- **2FA:** User enters the 6-digit code sent to their trusted device or via SMS
- On success → navigate to Album Browser

### 2. Album Browser

- Lists all **user-created albums** and an **"All Photos"** option
- Each album shows: **name** and **photo/video count**
- User **selects one or more albums** via checkboxes
- "Download Selected" button starts the download
- **Out of scope:** Shared Albums, Smart Albums, Recently Deleted

### 3. Download Progress ⭐ Core Feature

This is the heart of the app. Downloading large libraries takes time (hours or days). The UX must make it easy to start, stop, and resume without losing track of progress.


- **Per-file status** is visible: each file shows whether it is ✅ downloaded
    - Need discuttion: if pending, downloading, ❌ failed are feasible
- **Pause** button: stops queuing new downloads; in-flight files finish
- **Resume** button: re-enqueues paused/pending files — user can close the app and come back later
- **Cancel** button: stops everything, discards pending files
- **Per-file errors** are visible (e.g., "IMG_1234.HEIC — failed, retrying…") with option to retry
- Progress updates in **real time** (SSE)

### 4. File Retrieval

- Once an album is fully downloaded, it shows **"✅ Downloaded"** in the Album Browser
- User can **download individual files** or **download the entire album as a zip**
  - ⚠️ **TBD:** Zip generation may not be feasible for large albums (e.g., thousands of RAW images at 70+ MB each). Needs discussion — may need to cap zip size, split into parts, or remove the zip option entirely.
- **Files expire after 24 hours** on the server — UI should warn about this

---

## Session & Re-authentication

- iCloud sessions last ~2 months, then the user must log in again with 2FA
- If a session expires mid-download, the UI must **notify the user** and prompt re-authentication
- After re-auth, downloads should resume (not restart from scratch)

---

## Error UX

| Scenario | What the user sees |
|----------|--------------------|
| Wrong credentials | "Invalid Apple ID or password" |
| Wrong 2FA code | "Invalid code, please try again" |
| iCloud rate limit (503) | Nothing — app retries silently with backoff |
| File download fails (after 3 retries) | File marked as ❌ failed with error message; option to retry |
| Session expired | "Session expired — please log in again" prompt |
| Storage quota reached (10 GB) | "Storage limit reached — download your completed files before starting more" |

---

## Non-Functional Requirements

- **No data deletion:** The app never deletes anything from iCloud
- **HTTPS only** in production
- **No credential logging** — credentials must never appear in server logs
- **24-hour file cleanup** — downloaded files are auto-deleted from the server after 24 hours
- **Per-user isolation** — users cannot see each other's albums or files
