# Docs — Agent Instructions

## Scope

Root-level documentation and `docs/` directory.

## Owned Files

- `README.md` — Project overview, setup instructions (clone → run), screenshots placeholder
- `docs/PREREQUISITES.md` — iCloud settings users must configure (ADP off, web access on, TOS accepted)
- `docs/DEVELOPMENT.md` — Developer setup (Python venv, Node, running backend + frontend)
- `docs/CODE_REVIEW.md` — Active code review issues tracker (see below)
- `DISCLAIMER.md` — Apple TOS disclaimer, unofficial project notice
- `LICENSE` — MIT
- `.gitignore` — Python (`venv/`, `__pycache__/`, `*.pyc`, `.env`), Node (`node_modules/`, `frontend/dist/`), app data (`*.db`, `.tmp`)

---

## Constraints

- Setup instructions must match the actual project structure in `backend/` and `frontend/`
- Prerequisites must prominently warn about "Access iCloud Data on the Web" and Advanced Data Protection
- README should include the user setup commands from `PLANNING_MVP.md` §10
- DEVELOPMENT.md must document: running backend (`python app.py` on port 8000), running frontend dev server (`npm run dev` on port 5173), Vite proxy to backend
- Do not duplicate the full planning docs — reference `PLANNING_MVP.md` for architecture details

---

## Code Review Tracker (`docs/CODE_REVIEW.md`)

This is a living document. Agents must:

- **Check** this file before working on related code
- **Mark issues as fixed** (`[x]`) when addressed, with a short note
- **Add new issues** discovered during implementation or review
- **Move resolved issues** to the "Resolved Issues" section after verification
