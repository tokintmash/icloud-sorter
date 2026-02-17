# iCloud Photos API Research Report

*Compiled: February 2026*

---

## 1. Available Libraries

### 1.1 pyicloud (Original: picklepete/pyicloud)

| Attribute | Value |
|---|---|
| **GitHub** | https://github.com/picklepete/pyicloud |
| **Stars** | ~2,800 |
| **Forks** | ~487 |
| **Last Release** | v1.0.0 — Feb 17, 2022 |
| **Commits** | 271 |
| **Open PRs** | 37 |
| **License** | MIT |
| **Python** | 3.x |
| **Status** | ⚠️ **Effectively unmaintained** — no releases in 4 years |

**Features:**
- iCloud authentication (username/password + 2FA/2SA)
- Find My iPhone, Contacts, Calendar, iCloud Drive, File Storage (Ubiquity)
- Photo Library: album listing, photo asset iteration, download (original/medium/thumb)
- Session persistence via cookie files
- Password storage via system keyring

**Limitations:**
- Does NOT support SRP (Secure Remote Password) authentication — Apple has been migrating to SRP-based auth
- No support for FIDO2/security keys
- No China mainland support
- Stale: many open issues and PRs unmerged
- Used by Home Assistant's iCloud integration, which has hit auth issues

**Photo API capabilities:**
- `api.photos.all` — "All Photos" album (sorted by added_date, newest first)
- `api.photos.albums['AlbumName']` — access named albums
- Per-asset: `photo.filename`, `photo.versions` (keys: `original`, `medium`, `thumb`), `photo.download(version)`
- Download returns a `requests` response object with `stream=True`

---

### 1.2 pyicloud (Active Fork: timlaing/pyicloud)

| Attribute | Value |
|---|---|
| **GitHub** | https://github.com/timlaing/pyicloud |
| **Stars** | ~108 |
| **Forks** | ~30 |
| **Last Release** | v2.3.0 — Jan 18, 2026 |
| **Commits** | 485 |
| **PyPI** | `pyicloud` (v2.2.0, Nov 2025 — this fork now owns the PyPI package) |
| **License** | MIT |
| **Status** | ✅ **Actively maintained** — frequent releases, CI/CD, SonarCloud quality gates |

**Additional features over the original:**
- SRP-based authentication (the modern Apple auth flow)
- FIDO2 / Security Key support for 2FA
- China mainland support (`china_mainland=True`)
- Hide My Email service
- Enhanced Calendar API (create/remove events, alarms, invitees)
- Account storage/summary plan info
- Contacts MeCard support
- Auto-accept terms and conditions (`--accept-terms`)
- Discord community for support
- Automated PyPI publishing with Sigstore attestations

**This is the recommended pyicloud for new projects.** It's the de-facto successor published to PyPI as `pyicloud`.

---

### 1.3 icloud-photos-downloader / icloudpd

| Attribute | Value |
|---|---|
| **GitHub** | https://github.com/icloud-photos-downloader/icloud_photos_downloader |
| **Stars** | ~11,600 |
| **Forks** | ~756 |
| **Last Release** | v1.32.2 — Sep 2, 2025 |
| **Total Releases** | 80 |
| **Open Issues** | ~123 |
| **Open PRs** | ~28 |
| **Contributors** | 42 |
| **License** | MIT |
| **Language** | Python 93.7% |
| **Distribution** | Standalone binary, Docker, PyPI, AUR, npm wrapper |
| **Status** | ✅ **Actively maintained** — weekly release cadence target |

**Architecture:**
- CLI tool wrapping its own **internal fork of pyicloud** (under `icloud-photos-downloader/pyicloud`)
- The internal pyicloud fork was last updated Jan 2023, but the main project integrates patches directly
- Three operational modes: **Copy** (download new), **Sync** (download + delete removed), **Move** (download + delete from iCloud)
- Supports continuous monitoring via `--watch-with-interval`

**Key Features:**
- Live Photos: downloads image and video as **separate files**
- RAW images: supports RAW+JPEG pairs
- Automatic filename de-duplication
- EXIF datetime updates (`--set-exif-datetime`)
- Incremental optimization (`--until-found`, `--recent`)
- Configurable folder structure (`--folder-structure {:%Y/%Y-%m-%d}`)
- `--auth-only` mode for session pre-authorization
- Size selection: `--size original`

**iCloud Prerequisites (important):**
- User must enable: `Settings > Apple ID > iCloud > Access iCloud Data on the Web`
- User must disable: `Settings > Apple ID > iCloud > Advanced Data Protection`
- These are required or Apple returns `ACCESS_DENIED`

**Limitations:**
- Downloads photos into date-based folders by default, **not by album** (album-based download is a frequently requested feature, Issue #1315)
- Sequential downloads (one file at a time)
- Re-authentication required approximately every **2 months**
- No GUI — CLI only (though `icloudpd-web` exists as a 3rd-party web wrapper)

---

### 1.4 icloudpd-web (AirswitchAsa/icloudpd-web)

| Attribute | Value |
|---|---|
| **GitHub** | https://github.com/AirswitchAsa/icloudpd-web |
| **Stars** | ~115 |
| **Last Release** | v2025.7.31 — Jul 31, 2025 |
| **License** | CC BY-NC-4.0 (non-commercial only) |

A web UI wrapper around icloudpd. Next.js frontend + FastAPI backend. Supports managing multiple download "policies" and monitoring progress. **Note: non-commercial license.**

---

### 1.5 iCloud-API (Node.js — ElyaConrad/iCloud-API)

| Attribute | Value |
|---|---|
| **GitHub** | https://github.com/ElyaConrad/iCloud-API |
| **Stars** | ~1,300 |
| **Forks** | ~108 |
| **npm** | `apple-icloud` |
| **License** | Not specified |
| **Status** | ⚠️ Maintenance unclear |

**Features:**
- Full JavaScript/Node.js iCloud API wrapper
- Services: Contacts, Friends (Find My), Drive, Calendar, Photos, FindMe, Reminders, Mail, Notes
- Photos: `myCloud.Photos.get()` — fetch photos
- 2FA support (message/SMS/voice)
- Session persistence support
- Push notification services

**Limitations:**
- Photos upload "still in progress"
- Auth quirks: Apple may ban accounts with too-frequent logins
- Session cookies expire; must save/reuse sessions
- FindMe requires fresh credentials every few minutes

---

### 1.6 icloud-album-parser (Rust — harperreed/icloud-album-parser)

| Attribute | Value |
|---|---|
| **GitHub** | https://github.com/harperreed/icloud-album-parser |
| **Stars** | 2 |
| **crate** | `icloud-album-rs` v0.5.0 |
| **Status** | Niche — only for **shared albums** via public tokens |

Only works with publicly shared album URLs (e.g., `https://share.icloud.com/photos/TOKEN`). Does **not** support private library access or authentication. Not suitable for our use case.

---

### 1.7 Other Notable Projects

- **Blackwood-4NT** (C/C++, Windows) — Research-grade GSA/SRP authentication library. Excellent documentation of the authentication protocol. Educational, not production-ready.
- **osxphotos** (Python, CLI) — macOS-only tool that reads the local Photos SQLite database directly. Supports export with full metadata, albums, import with metadata restoration. Not cloud-based.
- **rclone** — Does NOT support iCloud Photos yet (PR #8734 open but not merged).
- **docker-icloudpd** (boredazfcuk) — Docker wrapper for icloudpd popular in self-hosting community.

---

## 2. Authentication Flow

### 2.1 Overview

Apple ID authentication for iCloud web services uses a **reverse-engineered** protocol. There is **no official public API**. The authentication targets Apple's Identity Management Services (IdMS).

### 2.2 Authentication Endpoints

| Endpoint | Purpose |
|---|---|
| `https://idmsa.apple.com/appleauth/auth/signin/init` | SRP Init — sends client public key `A`, receives salt, iterations, server public key `B` |
| `https://idmsa.apple.com/appleauth/auth/signin/complete` | SRP Complete — sends client proof `M1`, receives server proof `M2` + auth tokens |
| `https://setup.icloud.com/setup/ws/1/accountLogin` | iCloud service setup — exchanges auth tokens for service URLs and session cookies |
| `https://gsa.apple.com/grandslam/GsService2` | Grand Slam Authentication — native app auth (plist-based, used by Blackwood-4NT) |
| `https://idmsa.apple.com/appleauth/auth/verify/trusteddevice/securitycode` | 2FA code validation |
| `https://idmsa.apple.com/appleauth/auth/2sv/trust` | Session trust request |

### 2.3 SRP Authentication Protocol (Current)

Apple uses **SRP-6a** (Secure Remote Password) with custom modifications:

1. **Init Phase:**
   - Client generates SRP keypair, sends public key `A` + account name + supported protocols (`s2k`, `s2k_fo`)
   - Server returns: `salt`, `iterations` (for PBKDF2), server public key `B`, selected protocol, session cookie `c`

2. **Password Derivation (Apple-specific):**
   - Password is first SHA-256 hashed: `password_hash = SHA256(password)`
   - Then derived via PBKDF2-SHA256 with the server-provided salt and iteration count
   - This derived key is used as the SRP password (not the raw password)

3. **Complete Phase:**
   - Client computes SRP proof `M1` and sends it with the session cookie
   - Server validates and returns `M2` (server proof) + encrypted `spd` (Server Provided Data)
   - `spd` contains the PET (Password Equivalent Token) and ADSID (Alternate Directory Services ID)

4. **iCloud Setup:**
   - PET + ADSID are exchanged at `setup.icloud.com` for per-service URLs and cookies
   - Response includes endpoints for all iCloud services (photos, contacts, drive, etc.)

**Key auth headers required:**
- `X-Apple-OAuth-Client-Id` / `X-Apple-Widget-Key`: `d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d`
- `X-Apple-OAuth-Client-Type`: `firstPartyAuth`
- `X-Apple-OAuth-Redirect-URI`: `https://www.icloud.com`

### 2.4 Two-Factor Authentication (HSA2)

Apple's 2FA implementation is called **HSA2** (HomeSteadAdmin 2 / Two-Step Authentication v2).

**Flow:**
1. After successful password auth, if 2FA is enabled, the auth response indicates `requires_2fa = true`
2. Apple automatically pushes a 6-digit code to all trusted devices
3. The client submits the code to the verification endpoint
4. After code validation, the client can request **session trust** (`trust_session()`)
5. A trusted session avoids 2FA prompts for the trust period (~2 months)

**Modes supported by pyicloud (timlaing fork):**
- **Trusted device codes** — 6-digit code pushed to Apple devices (most common)
- **SMS codes** — sent to trusted phone number
- **FIDO2/Security keys** — hardware key authentication (newest)

**Legacy 2SA (two-step authentication):**
- Older protocol: user selects a trusted device, code is sent to that specific device
- Still supported but Apple is migrating users to HSA2

### 2.5 Session Persistence

**Cookie-based sessions:**
- Authentication produces a set of cookies (`X-APPLE-WEBAUTH-TOKEN`, session IDs, `scnt` tokens)
- pyicloud stores these in a **cookie file** on disk (configurable directory)
- icloudpd uses `--cookie-directory` to persist session cookies
- Cookies include `X-APPLE-WEBAUTH-HSA-TOKEN` for 2FA-trusted sessions

**Session expiry:**
- Sessions expire after approximately **2 months** (set by Apple server-side)
- After expiry, full re-authentication including 2FA is required
- There is no way to extend this programmatically
- The `--auth-only` flag in icloudpd can be used to pre-validate/refresh sessions

**Password storage:**
- pyicloud supports OS keyring via the `keyring` Python library
- Passwords should never be stored in plaintext
- Session tokens (cookies) are stored on disk but are time-limited

### 2.6 Anisette / Machine Identity

For native-app-style auth (GSA endpoint), Apple requires **Anisette headers**:
- `X-Apple-I-MD` — One Time Password
- `X-Apple-I-MD-M` — Machine Information
- `X-Apple-I-MD-RINFO` — Routing Information
- Machine provisioning is required to generate these

**Web-style auth** (used by pyicloud/icloudpd via idmsa.apple.com) does **not** require Anisette, making it simpler but potentially more fragile.

---

## 3. Album & Asset Enumeration

### 3.1 iCloud Photos API Architecture

The iCloud Photos API is built on top of **CloudKit** (Apple's cloud database service). It uses CloudKit's web services endpoint (`ckdatabasews`) to query records.

**Service URL pattern:** `https://p{XX}-ckdatabasews.icloud.com:443/database/1/com.apple.photos.cloud/production/private`

The `{XX}` partition number is provided in the authentication response's webservice URLs.

### 3.2 Album Types

| Album Type | API Access | Notes |
|---|---|---|
| **All Photos** | ✅ `api.photos.all` | Sorted by `added_date` (newest first) |
| **User-created Albums** | ✅ `api.photos.albums['Name']` | Sorted by `asset_date` (EXIF date) |
| **Smart Albums** | ⚠️ Partial | Some system-generated albums visible (e.g., Screenshots, Selfies, Panoramas) |
| **Favorites** | ⚠️ Via filtering | `isFavorite` flag available on assets |
| **Shared Albums** | ❌ Different API | Uses a separate shared streams API; not supported by pyicloud |
| **Recently Deleted** | ❌ | Not exposed via the web API |
| **Memories** | ❌ | Server-generated, not queryable |

**How icloudpd handles albums:**
- icloudpd does NOT download by album by default — it downloads all photos into date-structured folders
- Album-based organization is the #1 feature request (Issue #1315)
- pyicloud exposes album enumeration via `api.photos.albums` which returns a dict of album names → PhotoAlbum objects

### 3.3 Asset Metadata

Each `PhotoAsset` exposes:
- `id` — unique asset identifier (CloudKit record name)
- `filename` — original filename (e.g., `IMG_1234.HEIC`)
- `size` — file size in bytes
- `dimensions` — width × height (pixel dimensions)
- `created` / `asset_date` — EXIF creation date
- `added_date` — date added to iCloud library
- `versions` — dict with keys like `original`, `medium`, `thumb`, each containing `{filename, size, width, height, url, type}`
- `item_type` — asset type indicator
- EXIF data is NOT directly available via the API; must be read from downloaded file

### 3.4 Pagination

The CloudKit-based API uses **cursor-based pagination**:

- Queries return a page of records plus a **continuation marker/cursor**
- The cursor is passed in subsequent requests to get the next page
- Default page size is controlled by the server (typically ~200 records per page but varies)
- pyicloud handles pagination transparently — iterating over a `PhotoAlbum` automatically fetches subsequent pages
- For a library with 50K+ photos, the initial enumeration involves many sequential API calls
- `startRank` and `direction` parameters control the enumeration window

**Performance considerations for large libraries:**
- Initial enumeration of 50K+ photos can take several minutes (hundreds of paginated API calls)
- icloudpd offers `--recent N` to only check the N most recent photos
- `--until-found N` stops scanning when N already-downloaded photos are found consecutively

### 3.5 Media Types in the API

| Media Type | API Representation | Notes |
|---|---|---|
| **JPEG/PNG** | Single asset, single version | Straightforward |
| **HEIC** | Single asset | Downloaded as-is; conversion must be done client-side |
| **Live Photos** | Image + video as **separate assets** | Linked by same base filename or asset metadata; icloudpd downloads both as separate files |
| **RAW+JPEG** | Separate assets or dual versions | icloudpd supports RAW+JPEG pairs |
| **Edited Photos** | `original` + `adjusted` versions | `versions` dict may contain `adjusted` key for edited version |
| **Bursts** | Multiple assets | Appears as individual photos; key photo not distinctly marked via web API |
| **Videos** | Single asset | `item_type` indicates video |

**Versions available per asset:**
- `original` — full-resolution original file
- `medium` — reduced-resolution version
- `thumb` — thumbnail
- `adjusted` — edited version (when the photo has been edited in Photos app)

You **can** download both original and adjusted versions by specifying the version parameter in `photo.download('original')` or `photo.download('adjusted')`.

---

## 4. Download Mechanics

### 4.1 Download URLs

- Download URLs are obtained from the `versions` dict of each `PhotoAsset`
- URLs point to Apple's CDN: `https://cvws.icloud-content.com/...` (varies by region)
- URLs are **pre-signed** with authentication tokens embedded as query parameters
- URLs are **time-limited** — they expire (typically within hours)
- A new URL must be requested if the old one expires (re-query the asset)

### 4.2 Download Process

```
1. Authenticate → get session cookies
2. Query photos API → get list of assets (paginated)
3. For each asset, read versions → get pre-signed download URL
4. HTTP GET the download URL → stream file to disk
5. Verify file integrity (size match)
```

pyicloud's `photo.download()` returns a `requests.Response` with `stream=True`. Caller is responsible for writing to disk.

### 4.3 Rate Limits

**Apple does NOT officially document rate limits for the web API.** Observed behavior:

| Aspect | Observation |
|---|---|
| **Concurrent downloads** | icloudpd downloads **one file at a time** (sequential) |
| **Throttling** | Users report "connection refused" errors after sustained downloading (hours of continuous downloads) |
| **Typical failure point** | Often after downloading thousands of files in a session (reports of ~50% of 80K library before failure) |
| **CloudKit throttling** | Apple confirmed CloudKit throttling exists: HTTP 503 with `retry-after` header |
| **iCloud for Windows** | Observed throttle of ~1 photo per 30 seconds in some cases |
| **Download speed** | Individual file downloads are not speed-capped; total throughput limited by sequential nature |
| **Recovery strategy** | icloudpd recommends: re-run the command; already-downloaded files are skipped |

**icloudpd's approach to rate limits:**
- Sequential downloads (naturally rate-limited)
- Skip already-downloaded files on re-runs
- No built-in retry logic for individual files (relies on re-running)
- `--watch-with-interval` for periodic re-syncing with configurable intervals
- Users report that re-running after failures eventually gets all photos

**Apple's CloudKit throttling (documented):**
- When too many requests in too short a period → HTTP 503 Service Unavailable
- Response includes `retry-after` header with wait time in seconds
- All further requests refused until retry interval expires
- Device battery level can also trigger local throttling

### 4.4 Concurrent Request Handling

- The web API does NOT appear to explicitly block concurrent requests
- However, aggressive parallelism risks triggering rate limiting or account flagging
- icloudpd deliberately uses single-threaded downloads
- Community consensus: **2-5 concurrent downloads** is likely safe; more risks throttling
- No documented hard limit on concurrent connections

### 4.5 Achievable Throughput

- Individual photo download: bounded by network speed (no per-file speed cap observed)
- Practical throughput with icloudpd: **~1-3 photos/second** depending on file sizes
- Large libraries (50K+): expect **6-24+ hours** for full initial download
- Apple's own iCloud for Windows client: observed at ~2 files/minute under throttling
- Resumable: already-downloaded files are skipped on re-run

---

## 5. Endpoint Stability

### 5.1 History of Breaking Changes

| Date (approx) | Change | Impact | Recovery Time |
|---|---|---|---|
| **2012-2013** | Initial endpoints discovered via network sniffing (ElcomSoft, others) | N/A — foundational | N/A |
| **2019** | Apple migrated some services, changed setup endpoints | Brief disruption | Days |
| **2022 (Feb)** | pyicloud original repo's last release; auth started failing for some users | Ongoing for original repo | timlaing fork created |
| **2023-2024** | Apple began requiring SRP authentication, deprecating legacy password auth | **Major breaking change** — original pyicloud completely broken for many accounts | Weeks-months; fixed in timlaing fork and icloudpd's internal pyicloud |
| **2024 (Jan 30)** | Apple SRP server outage — "Error while SRP initial authentication: Unexpected response from IDMS Server" | Global outage, all SRP-based auth failed | Hours (Apple server-side fix) |
| **2024** | Apple required "Access iCloud Data on the Web" setting to be enabled | icloudpd added prerequisite documentation | Immediate (user-side config change) |
| **2025 (May, Aug)** | Recurring SRP/IDMS server issues reported | Temporary disruptions | Hours each time |
| **Ongoing** | Apple periodically updates terms of service, requiring acceptance before API access works | Login failures until terms accepted | pyicloud added `--accept-terms` |

### 5.2 Community Adaptation Speed

- **timlaing/pyicloud fork** has been the most responsive, integrating SRP auth within weeks of the change
- **icloudpd** maintains its own pyicloud fork and typically ships fixes within 1-2 weeks
- **Home Assistant iCloud3** integration struggled longer (months) to integrate SRP changes
- The community has a pattern of: Apple changes something → initial breakage reported → fix within 1-4 weeks in active projects

### 5.3 API Versions / Endpoints in Use

Multiple endpoint "families" exist:

1. **Web Auth (idmsa.apple.com)** — Used by pyicloud/icloudpd. Simulates icloud.com web login. Most stable for third-party use.

2. **GSA (gsa.apple.com)** — Used by native apps (iTunes, iCloud for Windows). Requires Anisette machine provisioning. More complex but potentially more stable long-term.

3. **CloudKit Web Services (ckdatabasews)** — The actual data API for Photos, used after authentication. Relatively stable as it's the same API Apple's web app uses.

4. **Setup (setup.icloud.com)** — Service discovery endpoint. Returns per-service URLs (photos, contacts, drive, etc.). Stable but URLs/partition numbers can change.

### 5.4 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Apple changes auth protocol | Medium (has happened) | High — complete auth failure | Isolate auth layer; monitor pyicloud/icloudpd for fixes; implement SRP |
| Apple blocks web-based access | Low-Medium | Critical | No mitigation possible; would affect all tools |
| Rate limiting / throttling | High | Medium — slower downloads | Sequential downloads, retry logic, exponential backoff |
| Apple requires new account settings | Medium | Medium — requires user action | Document prerequisites clearly; check at startup |
| Terms of service changes | Medium | Low — auto-accept possible | Implement auto-accept (pyicloud supports this) |
| Endpoint URL changes | Low | Low-Medium | Use setup.icloud.com for service discovery (dynamic URLs) |
| Advanced Data Protection enforcement | Low-Medium | High — would block web access entirely | Cannot mitigate; user must disable ADP |

---

## Summary & Recommendations

### For this project (iCloud Photo Downloader GUI):

1. **Auth Library:** Use **timlaing/pyicloud** (PyPI: `pyicloud` v2.x). It's the only actively maintained library with SRP support, 2FA handling, and the Photos API we need.

2. **Alternative if not using Python:** Port the auth logic from pyicloud. The SRP flow is well-documented in the Blackwood-4NT project. The Node.js `iCloud-API` library is another option but less maintained.

3. **Album enumeration:** pyicloud provides album listing via `api.photos.albums`. This gives us user-created albums, but NOT shared albums or Recently Deleted.

4. **Download approach:** Use pyicloud's `photo.download()` with streaming. Implement our own:
   - Concurrent downloads (2-5 parallel, with backoff)
   - Atomic writes (temp file → rename)
   - Resume/skip logic based on asset ID + file size
   - Retry with exponential backoff on 503s

5. **Session management:** Store cookies in a configurable directory. Warn users that re-auth is needed every ~2 months. Implement `--auth-only` equivalent for session refresh.

6. **Key prerequisites to document for users:**
   - Enable "Access iCloud Data on the Web" in iOS Settings
   - Disable Advanced Data Protection
   - Accept any pending terms of service

7. **Architecture principle:** Isolate the iCloud API layer completely so it can be updated independently when Apple makes changes. This is the single biggest risk.
