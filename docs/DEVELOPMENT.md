# Development Guide

## Project Structure

```
icloud-downloader/
├── backend/          # Python FastAPI backend
│   ├── app.py        # Entry point
│   ├── routers/      # API endpoint handlers
│   ├── services/     # Business logic
│   ├── models/       # Pydantic schemas & DB
│   └── config.py     # Configuration
├── frontend/         # React + TypeScript frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # API client
│   │   └── types/        # TypeScript types
│   └── vite.config.ts
└── docs/             # Documentation
```

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running in Development

### Start the Backend (Port 8000)

```bash
cd backend
source venv/bin/activate
python app.py
```

The API server runs at `http://localhost:8000`. API docs are available at `http://localhost:8000/docs`.

### Start the Frontend Dev Server (Port 5173)

```bash
cd frontend
npm run dev
```

The Vite dev server runs at `http://localhost:5173` and proxies all `/api/*` requests to the backend on port 8000.

## Production Build

```bash
# Build frontend
cd frontend
npm run build    # Outputs to frontend/dist/

# Run backend (serves both API and frontend)
cd ../backend
python app.py    # http://localhost:8000
```

In production mode, FastAPI serves the built frontend files from `frontend/dist/` and handles SPA routing.

## API Documentation

When the backend is running, visit `http://localhost:8000/docs` for the auto-generated Swagger UI.

## Architecture Notes

- **Backend** uses FastAPI with async endpoints
- **Frontend** communicates via REST API (`/api/*`)
- **Download progress** uses Server-Sent Events (SSE)
- **State** is persisted in SQLite at `~/.icloud-downloader/state.db`
- **iCloud auth** uses `pyicloud` library with cookie-based session persistence
- See `PLANNING_MVP.md` for detailed architecture documentation
