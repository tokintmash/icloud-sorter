# iCloud Photo Downloader — Cloud Planning Document

*February 2026 — School Project / AWS + Kubernetes + Docker*

---

## What Is This?

iCloud Photo Downloader is a web application that lets you download your photos from iCloud by albums without the need of having a Mac. You pick the albums you want, and the app downloads them. No Mac needed.

### Who Is This For?

The app is built for iPhone and iPad users who don't have a Mac. They've been using iCloud to store and organize their photos into albums, but they're running out of iCloud storage. They want to download their photos and videos to their computer — organized by album, exactly as they are, with no reformatting or conversion — so they can then free up space by deleting them from iCloud manually.

The app does not delete anything from iCloud. Once an album is fully downloaded, it's marked as "✅ Downloaded" in the UI, and the user can delete it from iCloud at their own pace via icloud.com or their device.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Technology Stack](#2-technology-stack)
3. [iCloud API Approach](#3-icloud-api-approach)
4. [Architecture](#4-architecture)
5. [Data Model & State Management](#5-data-model--state-management)
6. [Media Type Handling](#6-media-type-handling)
7. [Filename & Deduplication Strategy](#7-filename--deduplication-strategy)
8. [Download Pipeline](#8-download-pipeline)
9. [Project Structure](#9-project-structure)
10. [Docker & Kubernetes](#10-docker--kubernetes)
11. [AWS Infrastructure](#11-aws-infrastructure)
12. [Risk Assessment](#12-risk-assessment)
13. [Implementation Phases](#13-implementation-phases)

---

## 1. Executive Summary

### Approach: Cloud-Native Web App on AWS (Docker + Kubernetes)

**Stack:** Python (FastAPI) backend using `pyicloud` directly, Celery workers for background downloads, React/TypeScript frontend (Vite) served by Nginx, PostgreSQL for state, Redis for sessions + task queue, S3 for file delivery — all containerized and deployed on AWS EKS.

**Rationale:**
- **School requirement:** Must use AWS, Kubernetes, and Docker
- **Same core stack as MVP:** FastAPI + React — the app logic doesn't change, just the deployment model
- **Cloud-native patterns:** Demonstrates containerization, orchestration, managed services, and scalable architecture
- **pyicloud is used directly:** No bridge needed — Python calls pyicloud natively
- **Team fit:** Team knows JavaScript and has some Python experience; this stack uses both

### What Changed From the MVP Plan

| MVP (local) | Cloud |
|-------------|-------|
| `python app.py` on localhost | Dockerized, deployed on AWS EKS |
| SQLite (single file) | PostgreSQL (RDS) — multi-user capable |
| In-process `ThreadPoolExecutor` | Celery workers as separate pods (scalable) |
| Downloads to local disk | Downloads to S3, user gets presigned URL |
| FastAPI serves React build | Nginx container serves frontend, proxies API |
| Single user, no auth | Session-based user isolation |
| No infra cost | AWS Free Tier where possible, ~$50–100/mo otherwise |

### Credential Disclaimer

> **⚠️ School Project Disclaimer:** In this architecture, users send their Apple ID credentials to our server. In a production application this would be a serious security/trust concern. This is acceptable for a school project demonstration. The app should display a clear warning to users that credentials are transmitted to a remote server.

---

## 2. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend API** | Python 3.12 with FastAPI | Async-capable, auto-generates OpenAPI docs |
| **iCloud API** | `pyicloud` v2.x (timlaing fork) | Only actively maintained iCloud library with SRP, 2FA, Photos API |
| **Task Queue** | Celery + Redis | Background download jobs, decoupled from API process |
| **Frontend** | React + TypeScript (Vite) | Team knows JS; rich ecosystem for progress UIs |
| **Frontend Server** | Nginx (Alpine) | Serves static build, reverse-proxies `/api` to backend |
| **State DB** | PostgreSQL 16 (AWS RDS) | Multi-user, production-grade, managed by AWS |
| **Session / Queue** | Redis 7 (AWS ElastiCache or pod) | Fast session store + Celery broker |
| **File Storage** | AWS S3 | Temp storage for completed downloads; presigned URLs for user retrieval |
| **Container Runtime** | Docker | Containerize all services |
| **Orchestration** | Kubernetes (AWS EKS) | Deploy, scale, and manage containers |
| **Container Registry** | AWS ECR | Private Docker image registry |
| **Build** | pip + npm | Standard tooling |

### Why Celery Instead of ThreadPoolExecutor

The MVP uses `ThreadPoolExecutor` inside the FastAPI process. This works locally but not in a cloud deployment:

- **Scalability:** Celery workers run as separate pods — scale download capacity independently from the API
- **Reliability:** If the API pod restarts, in-flight download tasks aren't lost (Celery persists tasks in Redis)
- **Isolation:** A slow/stuck download doesn't block API responses
- **Kubernetes-native:** Worker pods can be scaled with HPA (Horizontal Pod Autoscaler) based on queue depth

### Why PostgreSQL Instead of SQLite

- SQLite doesn't work well across multiple pods (no concurrent write access over network storage)
- PostgreSQL handles multiple API pods and worker pods reading/writing simultaneously
- AWS RDS provides managed backups, patching, and monitoring
- Minimal code change — swap `sqlite3` calls for `asyncpg` or `SQLAlchemy`

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
| Concurrent downloads (Celery workers) | 3 | Yes (1–10) |
| Delay between metadata API calls | 200ms | Yes |
| Retry on 503 | Exponential backoff starting at 30s | Yes |
| Max retries per asset | 3 | Yes |

### Session Persistence in Cloud

pyicloud stores session cookies in a local directory. In the cloud:

- Store the cookie directory path per user in PostgreSQL
- Mount a shared volume (EFS) or serialize cookies to the database
- On worker startup, restore cookies from DB to a temp directory
- **Simpler alternative:** Store the serialized `PyiCloudService` session in Redis with a per-user key and TTL matching the session lifetime (~2 months)

---

## 4. Architecture

### Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│  USER BROWSER                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐               │
│  │  Auth     │ │  Album   │ │ Download │ │  Settings     │               │
│  │  Screen   │ │  Browser │ │ Progress │ │               │               │
│  │  (2FA)    │ │  (select)│ │ (live)   │ │               │               │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘               │
└──────────────────────────────────────────────────────────────────────────┘
                          │ HTTPS (ALB)
┌──────────────────────────────────────────────────────────────────────────┐
│  AWS EKS CLUSTER                                                         │
│                                                                          │
│  ┌─────────────────────────────────┐                                     │
│  │  Ingress (ALB Ingress Controller)│                                    │
│  │  - /        → frontend service  │                                     │
│  │  - /api/*   → backend service   │                                     │
│  └────────┬───────────┬────────────┘                                     │
│           │           │                                                  │
│  ┌────────▼────┐  ┌───▼──────────────────────────┐                       │
│  │  Frontend   │  │  Backend Pod(s)               │                      │
│  │  Pod        │  │  FastAPI                      │                      │
│  │  (Nginx)    │  │  ┌──────────┐ ┌────────────┐  │                      │
│  │  - React    │  │  │AuthRouter│ │AlbumRouter │  │                      │
│  │    static   │  │  │POST /login│ │GET /albums│  │                      │
│  │    files    │  │  │POST /2fa │ │GET /assets │  │                      │
│  │             │  │  └────┬─────┘ └─────┬──────┘  │                      │
│  │             │  │       ▼             ▼         │                      │
│  │             │  │  ┌──────────────────────────┐ │                      │
│  │             │  │  │ iCloudService (pyicloud)  │ │                      │
│  │             │  │  └──────────────────────────┘ │                      │
│  │             │  │                               │                      │
│  │             │  │  ┌──────────────────────────┐ │                      │
│  │             │  │  │ DownloadRouter           │ │                      │
│  │             │  │  │ POST /download/start     │ │                      │
│  │             │  │  │  → enqueue Celery tasks  │ │                      │
│  │             │  │  │ GET /download/progress   │ │                      │
│  │             │  │  │  → SSE from Redis state  │ │                      │
│  │             │  │  │ GET /download/files      │ │                      │
│  │             │  │  │  → S3 presigned URLs     │ │                      │
│  │             │  │  └──────────────────────────┘ │                      │
│  └─────────────┘  └───────────────────────────────┘                      │
│                                                                          │
│  ┌──────────────────────────────────────────┐                            │
│  │  Celery Worker Pod(s)                     │                           │
│  │  - Pulls jobs from Redis queue            │                           │
│  │  - Downloads from iCloud CDN              │                           │
│  │  - Uploads completed files to S3          │                           │
│  │  - Updates progress in Redis + PostgreSQL │                           │
│  └──────────────────────────────────────────┘                            │
│                                                                          │
│  ┌──────────────┐                                                        │
│  │  Redis Pod   │   (or AWS ElastiCache)                                 │
│  │  - Sessions  │                                                        │
│  │  - Celery    │                                                        │
│  │    broker    │                                                        │
│  │  - Progress  │                                                        │
│  │    state     │                                                        │
│  └──────────────┘                                                        │
└──────────────────────────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│  AWS RDS     │    │  AWS S3           │
│  PostgreSQL  │    │  - Downloaded     │
│  - Users     │    │    photos/videos  │
│  - Albums    │    │  - Lifecycle rule: │
│  - Assets    │    │    delete after   │
│  - Downloads │    │    24 hours       │
└──────────────┘    └──────────────────┘
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/login` | Login with Apple ID + password |
| `POST` | `/api/auth/2fa` | Submit 2FA code |
| `GET` | `/api/auth/session` | Check session status |
| `GET` | `/api/albums` | List all albums with asset counts |
| `GET` | `/api/albums/:id/assets` | List assets in an album (paginated) |
| `POST` | `/api/download/start` | Enqueue download jobs for selected albums |
| `GET` | `/api/download/progress` | SSE stream of download progress |
| `POST` | `/api/download/pause` | Pause downloads |
| `POST` | `/api/download/cancel` | Cancel downloads |
| `GET` | `/api/download/files` | List completed files with S3 presigned download URLs |
| `POST` | `/api/download/zip` | Generate a zip of completed album and return presigned URL |
| `GET` | `/api/settings` | Get current settings |
| `PUT` | `/api/settings` | Update settings |

### Concurrency Model

Downloads run as Celery tasks in separate worker pods:

```python
from celery import Celery

celery_app = Celery("icloud_downloader", broker="redis://redis:6379/0")

@celery_app.task(bind=True, max_retries=3)
def download_asset(self, user_id: str, asset_id: str, album_id: str, version: str):
    """Download a single asset from iCloud and upload to S3."""
    try:
        # Restore pyicloud session from Redis
        icloud = restore_session(user_id)

        # Download from iCloud CDN
        photo = icloud.photos.get(asset_id)
        response = photo.download(version)

        # Upload to S3
        s3_key = f"downloads/{user_id}/{album_id}/{filename}"
        s3_client.upload_fileobj(response.raw, BUCKET, s3_key)

        # Update state
        update_download_status(asset_id, album_id, "complete", s3_key=s3_key)

    except Exception as exc:
        update_download_status(asset_id, album_id, "failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
```

### Progress Updates via SSE

The API pod reads progress from Redis (updated by workers) and streams to the frontend:

```python
@router.get("/api/download/progress")
async def progress_stream(request: Request, user_id: str = Depends(get_current_user)):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            progress = await redis.hgetall(f"progress:{user_id}")
            yield f"data: {json.dumps(progress)}\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### File Delivery to User

Since the server can't write to the user's local filesystem:

1. **Worker downloads** from iCloud CDN → **uploads to S3** with key `downloads/{user_id}/{album_name}/{filename}`
2. **API generates presigned S3 URLs** (valid 1 hour) for the frontend
3. **Frontend shows a "Download" button** per album → triggers browser download via presigned URL
4. **Zip option:** API creates a zip of an album's files in S3 and returns a presigned URL for the zip
5. **S3 lifecycle policy** auto-deletes files after 24 hours to control storage costs

### Error Handling & Retry Strategy

| Error Type | Action |
|-----------|--------|
| HTTP 503 (throttled) | Celery retry with exponential backoff; honor `retryAfter` header |
| HTTP 401/403 (auth expired) | Mark task as `auth_required`; notify user via SSE to re-authenticate |
| Network timeout | Celery retry up to 3 times with backoff |
| S3 upload error | Retry upload (separate from iCloud download retry) |
| Celery worker crash | Task returns to queue automatically (acks_late=True) |

---

## 5. Data Model & State Management

### PostgreSQL Schema

```sql
-- User sessions (maps browser sessions to iCloud sessions)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_token   TEXT UNIQUE NOT NULL,    -- browser session cookie
    apple_id        TEXT,                    -- set after login
    icloud_cookies  BYTEA,                  -- serialized pyicloud cookies
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Albums discovered from iCloud
CREATE TABLE albums (
    id              TEXT NOT NULL,           -- iCloud album ID
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    asset_count     INTEGER,
    last_synced_at  TIMESTAMPTZ,
    folder_name     TEXT NOT NULL,           -- sanitized name for S3 key / zip
    PRIMARY KEY (id, user_id)
);

-- Assets (photos/videos) in iCloud
CREATE TABLE assets (
    id              TEXT NOT NULL,           -- iCloud asset ID
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    size_bytes      BIGINT,
    item_type       TEXT,
    created_at      TIMESTAMPTZ,
    has_adjustments BOOLEAN DEFAULT FALSE,
    width           INTEGER,
    height          INTEGER,
    PRIMARY KEY (id, user_id)
);

-- Junction: which assets belong to which albums
CREATE TABLE album_assets (
    album_id    TEXT NOT NULL,
    asset_id    TEXT NOT NULL,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    position    INTEGER,
    PRIMARY KEY (album_id, asset_id, user_id)
);

-- Download tracking
CREATE TABLE downloads (
    id              SERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id        TEXT NOT NULL,
    album_id        TEXT NOT NULL,
    version         TEXT NOT NULL,
    s3_key          TEXT,                   -- S3 object key (replaces local_path)
    status          TEXT NOT NULL DEFAULT 'pending',
                    -- 'pending', 'queued', 'downloading', 'complete', 'failed', 'skipped'
    file_size       BIGINT,
    error_message   TEXT,
    attempts        INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    UNIQUE(user_id, asset_id, album_id, version)
);

CREATE INDEX idx_downloads_user_status ON downloads(user_id, status);
CREATE INDEX idx_downloads_album ON downloads(user_id, album_id, status);
CREATE INDEX idx_album_assets_album ON album_assets(user_id, album_id);
```

### Key Differences From MVP Schema

| MVP (SQLite) | Cloud (PostgreSQL) |
|---|---|
| No `user_id` — single user | `user_id` on every table for multi-tenancy |
| `local_path` for downloaded files | `s3_key` pointing to S3 object |
| `bytes_downloaded` for partial progress | Progress tracked in Redis (ephemeral), not DB |
| `INTEGER` for booleans | Native `BOOLEAN` type |
| `TEXT` for timestamps | `TIMESTAMPTZ` for proper timezone handling |

### Deduplication Key

**Primary key:** iCloud asset ID + user_id — globally unique per user.

**Incremental sync logic:**
1. Query iCloud for album assets (paginated)
2. For each asset, check `downloads` table: if `status = 'complete'` AND S3 object exists, skip
3. If `status = 'failed'` and `attempts < max_retries`, re-enqueue
4. If asset not in DB, insert as `pending` and enqueue Celery task

---

## 6. Media Type Handling

### Policy Summary (MVP)

| Media Type | Policy | S3 Key Example |
|-----------|--------|----------------|
| **JPEG/PNG** | Download original | `downloads/{user_id}/Vacation/IMG_1234.JPG` |
| **HEIC** | Download original (no conversion) | `downloads/{user_id}/Vacation/IMG_1234.HEIC` |
| **Live Photos** | Download both image + video | `...IMG_1234.HEIC` + `...IMG_1234.MOV` |
| **Videos** | Download as-is | Original filename |
| **Edited photos** | Download original only | `...IMG_1234.HEIC` |
| **RAW+JPEG** | Download both files | `...IMG_1234.DNG` + `...IMG_1234.JPG` |
| **Bursts** | All frames | Standard naming per frame |

### Album Scope

| Album Type | In Scope | Notes |
|-----------|----------|-------|
| **User-created albums** | ✅ Yes | Core feature |
| **"All Photos"** | ✅ Yes | As a special album option |
| **Shared Albums** | ❌ No | Different API, not supported by pyicloud |
| **Smart Albums** | ⚠️ Partial | Include if pyicloud exposes them |
| **Recently Deleted** | ❌ No | Not exposed via web API |

---

## 7. Filename & Deduplication Strategy

### Collision Resolution (Within Album)

**Strategy: Append date, then sequence number on further collision.**

```
IMG_0001.HEIC                    ← first occurrence
IMG_0001_2024-03-15.HEIC         ← second, different asset, append EXIF date
IMG_0001_2024-03-15 (2).HEIC     ← third, same date collision, append sequence
IMG_0001_2024-07-22.HEIC         ← fourth, different date
```

### Cross-Album Duplicates

**Strategy:** Each album gets its own S3 prefix. Same asset in multiple albums = stored once in S3, referenced by multiple download records with the same `s3_key`.

**Optimization:** If the same `asset_id + version` already has `status = 'complete'` for this user, **copy the S3 object** (S3 server-side copy, free and instant) instead of re-downloading from iCloud.

### S3 Key Sanitization

Album names → S3 key components:
```
1. Replace characters problematic in S3/URLs: / \ : * ? " < > | # % & { }  → _
2. Trim leading/trailing whitespace and dots
3. Truncate to 200 characters
4. If empty after sanitization, use "Unnamed_Album"
5. If key collides, append "_2", "_3", etc.
```

---

## 8. Download Pipeline

### Cloud Pipeline (iCloud → S3)

```
1. Celery worker picks up download_asset task from Redis queue
2. Restore pyicloud session from Redis/DB for this user
3. Get download URL from iCloud CDN (pre-signed, time-limited)
4. Stream download from iCloud CDN
5. Upload stream directly to S3: downloads/{user_id}/{album_name}/{filename}
6. Verify S3 object size matches expected
7. Update PostgreSQL: status = 'complete', s3_key = '...'
8. Update Redis progress hash for SSE
```

### User File Retrieval

```
1. User clicks "Download Album" in frontend
2. API generates presigned S3 URLs for all completed assets in album
3. Option A: Frontend downloads individual files via presigned URLs
4. Option B: API creates a zip in S3 (using streaming), returns presigned URL
5. S3 lifecycle policy deletes files after 24 hours
```

### No Atomic Writes Needed

The MVP used temp files + rename for atomicity on local disk. In the cloud:
- S3 PutObject is atomic — an object either fully exists or doesn't
- Failed uploads simply don't create the S3 object
- No cleanup of temp files needed

### Pause / Cancel

| Action | Behavior |
|--------|----------|
| **Pause** | Revoke pending Celery tasks. In-flight tasks complete (Celery can't interrupt mid-download). |
| **Resume** | Re-enqueue all `pending` and `queued` download records as new Celery tasks. |
| **Cancel** | Revoke all pending tasks. Mark remaining `pending`/`queued` as `skipped`. Optionally delete S3 objects. |

### Storage Cost Control

```
1. S3 lifecycle policy: delete objects in downloads/ prefix after 24 hours
2. Per-user storage quota: max 10 GB in S3 at any time
3. Warn user if quota approached
4. Completed downloads show "Download to your computer" button prominently
```

---

## 9. Project Structure

```
icloud-downloader/
├── backend/
│   ├── Dockerfile                  # Python API + Celery image
│   ├── requirements.txt            # pyicloud, fastapi, uvicorn, celery, redis, boto3, asyncpg
│   ├── app.py                      # FastAPI app entry point
│   ├── celery_app.py               # Celery configuration
│   ├── routers/
│   │   ├── auth.py                 # /api/auth/* endpoints
│   │   ├── albums.py               # /api/albums/* endpoints
│   │   ├── download.py             # /api/download/* endpoints
│   │   └── settings.py             # /api/settings endpoints
│   ├── services/
│   │   ├── icloud_service.py       # pyicloud wrapper (auth, albums, assets)
│   │   ├── download_service.py     # Celery task definitions
│   │   ├── s3_service.py           # S3 upload, presigned URLs, zip generation
│   │   └── state_service.py        # PostgreSQL state management
│   ├── models/
│   │   ├── schemas.py              # Pydantic models for API request/response
│   │   └── db.py                   # SQLAlchemy models / raw SQL queries
│   └── config.py                   # App configuration (env vars)
│
├── frontend/
│   ├── Dockerfile                  # Multi-stage: Node build → Nginx serve
│   ├── nginx.conf                  # Nginx config (serve static + proxy /api)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── AuthScreen.tsx
│       │   ├── AlbumBrowser.tsx
│       │   ├── DownloadProgress.tsx
│       │   ├── FileList.tsx         # List completed files with download links
│       │   └── Settings.tsx
│       ├── hooks/
│       │   └── useApi.ts           # API client hooks
│       ├── types/
│       │   └── api.ts              # TypeScript types matching Pydantic schemas
│       └── styles/
│
├── k8s/                             # Kubernetes manifests
│   ├── namespace.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── celery-worker-deployment.yaml
│   ├── redis-deployment.yaml
│   ├── redis-service.yaml
│   ├── ingress.yaml                # ALB Ingress Controller
│   ├── configmap.yaml              # Non-secret configuration
│   └── secrets.yaml                # DB password, S3 credentials (or use AWS Secrets Manager)
│
├── terraform/                       # (Optional) Infrastructure as Code
│   ├── main.tf                     # EKS cluster, RDS, S3, ECR, VPC
│   ├── variables.tf
│   └── outputs.tf
│
├── docker-compose.yaml              # Local development (all services)
│
├── docs/
│   ├── PREREQUISITES.md            # User setup guide (iCloud settings)
│   ├── DEVELOPMENT.md              # Developer setup guide
│   └── DEPLOYMENT.md               # AWS deployment guide
│
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Test + lint
│       └── deploy.yml              # Build images → push ECR → deploy to EKS
│
├── LICENSE                         # MIT
├── README.md
├── DISCLAIMER.md                   # Apple TOS + credential trust disclaimer
├── PLANNING.md                     # Full desktop plan (reference)
├── PLANNING_MVP.md                 # Local MVP plan (reference)
└── PLANNING_CLOUD.md               # This document
```

---

## 10. Docker & Kubernetes

### Dockerfiles

**Backend (`backend/Dockerfile`):**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run the API server. Override CMD for Celery worker.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend (`frontend/Dockerfile`):**

```dockerfile
# Stage 1: Build React app
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

**Nginx config (`frontend/nginx.conf`):**

```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # In K8s, the Ingress handles /api routing.
    # This is only used for docker-compose local dev.
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;             # Required for SSE
    }
}
```

### docker-compose.yaml (Local Development)

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/icloud_downloader
      - REDIS_URL=redis://redis:6379/0
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - AWS_REGION=${AWS_REGION}
    depends_on:
      - db
      - redis

  celery-worker:
    build: ./backend
    command: celery -A celery_app worker --loglevel=info --concurrency=3
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/icloud_downloader
      - REDIS_URL=redis://redis:6379/0
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - AWS_REGION=${AWS_REGION}
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: icloud_downloader
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### Kubernetes Manifests (Key Examples)

**Backend Deployment (`k8s/backend-deployment.yaml`):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: icloud-downloader
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: <account-id>.dkr.ecr.<region>.amazonaws.com/icloud-downloader-backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secrets
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

**Celery Worker Deployment (`k8s/celery-worker-deployment.yaml`):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: icloud-downloader
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
        - name: celery-worker
          image: <account-id>.dkr.ecr.<region>.amazonaws.com/icloud-downloader-backend:latest
          command: ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=3"]
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secrets
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
```

**Ingress (`k8s/ingress.yaml`):**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: icloud-downloader-ingress
  namespace: icloud-downloader
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
    - http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

---

## 11. AWS Infrastructure

### Required Services

| Service | Purpose | Free Tier | Estimated Cost (Beyond Free Tier) |
|---------|---------|-----------|-----------------------------------|
| **EKS** | Kubernetes control plane | ❌ No free tier | $0.10/hr (~$73/mo) |
| **EC2** (EKS nodes) | Worker nodes (2× t3.small) | 750 hrs/mo t2.micro (too small) | ~$30/mo (2× t3.small) |
| **ECR** | Docker image registry | 500 MB/mo free | ~$0 (images are small) |
| **RDS** (PostgreSQL) | State database | 750 hrs/mo db.t3.micro | ~$0 if using free tier instance |
| **ElastiCache** (Redis) | Sessions + Celery broker | ❌ No free tier | ~$12/mo (cache.t3.micro) |
| **S3** | Downloaded file temp storage | 5 GB free | ~$0.023/GB/mo |
| **ALB** | Load balancer (via Ingress) | ❌ No free tier | ~$16/mo + $0.008/LCU-hr |

**Estimated total:** ~$130–$150/month

### Cost-Saving Alternatives for School Project

| Saving | Change | Impact |
|--------|--------|--------|
| **-$73/mo** | Use **k3s on EC2** instead of EKS | Same K8s API, self-managed control plane |
| **-$12/mo** | Run Redis as a **K8s pod** instead of ElastiCache | No HA, but fine for school |
| **-$16/mo** | Use **NodePort** + direct EC2 access instead of ALB | No HTTPS/load balancing, but works for demo |
| **-$30/mo** | Use **single t3.medium** instead of 2× t3.small | All pods on one node |

**Budget option:** Single t3.medium EC2 ($33/mo) + k3s + Redis pod + RDS free tier + S3 = **~$35/month**

### S3 Lifecycle Policy

```json
{
  "Rules": [
    {
      "ID": "delete-downloads-after-24h",
      "Filter": { "Prefix": "downloads/" },
      "Status": "Enabled",
      "Expiration": { "Days": 1 }
    }
  ]
}
```

---

## 12. Risk Assessment

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|-----------|------------|
| 1 | **Apple changes auth endpoints** | 🔴 High | Near-certain (1–2x/year) | pyicloud community fixes within days–weeks. Pin version, update when needed. |
| 2 | **Rate limiting / throttling** | 🟡 Medium | Likely for large libraries | Conservative defaults (3 concurrent, backoff); honor 503 retryAfter |
| 3 | **pyicloud ecosystem stagnation** | 🟡 Medium | Medium | We depend on pyicloud directly; monitor and update |
| 4 | **Session expiry (every ~2 months)** | 🟢 Low | Certain | Clear UX for re-authentication |
| 5 | **Credential trust** | 🟡 Medium | N/A (accepted for school) | Display clear disclaimer; HTTPS only; don't log credentials |
| 6 | **AWS costs overrun** | 🟡 Medium | Medium | Use budget alerts; k3s instead of EKS; shut down when not demoing |
| 7 | **S3 storage costs** | 🟢 Low | Low | 24-hour lifecycle policy; per-user quota (10 GB) |
| 8 | **K8s complexity** | 🟡 Medium | Medium | Start with docker-compose locally; move to K8s once app works |

### New Risks (vs MVP Plan)

These risks are new in the cloud deployment:

- **Credential trust:** Users send Apple credentials to our server (accepted for school project)
- **AWS costs:** Monthly infrastructure costs; mitigated with budget option
- **Kubernetes learning curve:** Team must learn K8s deployment, debugging, and manifests
- **Session persistence across pods:** pyicloud sessions must be shared (solved via Redis)

### Removed Risks (vs MVP Plan)

- ~~Python version issues on user machines~~ — Python runs in Docker, version is fixed

---

## 13. Implementation Phases

### Phase 1: App Logic — Local with docker-compose (Weeks 1–3)

**Goal:** Working app running locally via `docker-compose up`. Login, browse albums, download photos.

- [ ] Scaffold FastAPI backend + React (Vite) frontend
- [ ] Implement `icloud_service.py` — login, 2FA, session persistence using pyicloud
- [ ] Implement auth API endpoints (`/api/auth/login`, `/api/auth/2fa`, `/api/auth/session`)
- [ ] Implement album listing endpoint (`/api/albums`)
- [ ] Build Auth screen (Apple ID, password, 2FA code entry)
- [ ] Build Album browser (list albums with photo counts)
- [ ] Set up PostgreSQL schema
- [ ] Write `Dockerfile` for backend and frontend
- [ ] Write `docker-compose.yaml` with all services (backend, frontend, db, redis)
- [ ] Verify everything works with `docker-compose up`

### Phase 2: Download Engine (Weeks 4–5)

**Goal:** Download selected albums via Celery workers, store in S3, deliver to user.

- [ ] Set up Celery with Redis broker
- [ ] Implement `download_service.py` — Celery task for downloading assets
- [ ] Implement `s3_service.py` — upload to S3, presigned URLs, zip generation
- [ ] SSE progress streaming (API reads from Redis, streams to frontend)
- [ ] Build Download Progress screen (progress bars, speed, ETA)
- [ ] Build File List screen (completed files with download links)
- [ ] Pause / Cancel support
- [ ] Add Celery worker service to docker-compose
- [ ] Test full pipeline: iCloud → Celery → S3 → browser download

### Phase 3: Kubernetes + AWS Deployment (Weeks 6–7)

**Goal:** Deploy to AWS EKS (or k3s on EC2). App accessible via public URL.

- [ ] Push Docker images to ECR
- [ ] Write Kubernetes manifests (Deployments, Services, Ingress, ConfigMaps, Secrets)
- [ ] Set up EKS cluster (or k3s on EC2 for budget option)
- [ ] Set up RDS PostgreSQL instance
- [ ] Set up S3 bucket with lifecycle policy
- [ ] Set up ALB Ingress Controller (or NodePort for budget)
- [ ] Deploy all services to K8s
- [ ] Verify app works end-to-end on AWS
- [ ] Set up CI/CD pipeline (GitHub Actions → ECR → EKS)

### Phase 4: Polish (Week 8)

**Goal:** Handle edge cases, documentation, presentation-ready.

- [ ] Retry logic with exponential backoff
- [ ] Handle auth re-prompts (session expired mid-download)
- [ ] Error reporting UI (per-file errors with retry)
- [ ] Logging (structured, viewable via `kubectl logs`)
- [ ] README with setup instructions + prerequisites
- [ ] Deployment documentation
- [ ] Credential trust disclaimer on login page
- [ ] Testing with real iCloud libraries
- [ ] Cost monitoring / budget alerts

---

*This cloud plan builds on top of the MVP architecture (PLANNING_MVP.md) and adds Docker, Kubernetes, and AWS infrastructure. The core app logic (FastAPI + pyicloud + React) remains the same — only the deployment model changes.*
