# Phase 3C: CI/CD for Builds & Releases — Implementation Plan

**Status:** Not started  
**Dependencies:** Phase 3B (complete)

---

## Goal

Create a GitHub Actions workflow that lints, tests, builds the frontend, packages the `.exe`, and (on tag push) publishes a GitHub Release with the artifact.

---

## Files to Create / Change

### 1. `.github/workflows/build.yml` — Main CI/CD workflow (NEW)

Single workflow file with two trigger events and a linear job pipeline.

#### Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  push:
    tags: ['v*']
```

**Note:** YAML doesn't allow duplicate `push` keys. Merge into one:

```yaml
on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]
```

#### Jobs

**Job 1: `lint-and-test`** (runs on every push/PR)

Runs on `windows-latest`. Steps:

1. **Checkout** — `actions/checkout@v4`
2. **Set up Python 3.12** — `actions/setup-python@v5` with `python-version: '3.12'`
3. **Set up Node 22** — `actions/setup-node@v4` with `node-version: '22'`
4. **Cache pip** — `actions/cache@v4`, key on `requirements*.txt` hash
5. **Cache npm** — `actions/cache@v4`, key on `frontend/package-lock.json` hash
6. **Install Python deps** — `pip install -r backend/requirements.txt`
7. **Install Node deps** — `cd frontend && npm ci`
8. **Lint Python** — `pip install ruff && ruff check backend/`
9. **Lint TypeScript** — `cd frontend && npm run lint`
10. **Test Python** — `python -m pytest backend/tests/ -v`
11. **Test TypeScript** — `cd frontend && npm run test`
12. **Build frontend** — `cd frontend && npm run build`
13. **Upload frontend dist** — `actions/upload-artifact@v4` (for the build job)

**Job 2: `build-exe`** (runs after `lint-and-test`, only on `main` push or tag push)

Runs on `windows-latest`. Condition: `if: github.event_name == 'push'`

Needs: `lint-and-test`

Steps:

1. **Checkout** — `actions/checkout@v4`
2. **Set up Python 3.12** — same as above
3. **Set up Node 22** — same as above
4. **Download frontend dist** — `actions/download-artifact@v4`
5. **Install build deps** — `pip install --pre -r requirements-build.txt`
6. **Stamp beta** — `python scripts/stamp_beta.py`
7. **Run PyInstaller** — `pyinstaller icloud_sorter.spec --noconfirm`
8. **Verify exe exists** — `Test-Path dist\iCloudPhotoSorter\iCloudPhotoSorter.exe`
9. **Upload exe artifact** — `actions/upload-artifact@v4` with `dist/iCloudPhotoSorter/` folder

**Job 3: `release`** (runs after `build-exe`, only on tag push)

Runs on `ubuntu-latest`. Condition: `if: startsWith(github.ref, 'refs/tags/v')`

Needs: `build-exe`

Steps:

1. **Download exe artifact** — `actions/download-artifact@v4`
2. **Zip the folder** — zip `iCloudPhotoSorter/` into `iCloudPhotoSorter-<tag>.zip`
3. **Create GitHub Release** — `softprops/action-gh-release@v2` with the `.zip` as an asset

---

### 2. Add `ruff` linter config — `pyproject.toml` (NEW, project root)

Minimal ruff config so the lint step has consistent rules:

```toml
[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"backend/tests/*" = ["F811"]
```

**Why ruff:** fast (written in Rust), single binary, zero config needed, covers both flake8 and isort. No existing Python linter is configured in the repo.

---

### 3. `requirements-ci.txt` (NEW, project root)

Separate from `requirements-build.txt` because CI lint/test doesn't need PyInstaller/pywebview/pythonnet:

```
-r backend/requirements.txt
ruff>=0.11.0
```

This keeps the lint-and-test job fast (avoids `pythonnet` pre-release install issues, avoids pywebview native deps).

---

## Workflow Diagram

```
push to main / PR                     push v* tag
     │                                     │
     ▼                                     ▼
┌──────────────┐                   ┌──────────────┐
│ lint-and-test│◀──────────────────│ lint-and-test│
└──────┬───────┘                   └──────┬───────┘
       │                                  │
       ▼                                  ▼
┌──────────────┐                   ┌──────────────┐
│  build-exe   │                   │  build-exe   │
└──────────────┘                   └──────┬───────┘
  (artifact only)                         │
                                          ▼
                                   ┌──────────────┐
                                   │   release    │
                                   │ (GitHub Rel.+│
                                   │  .zip asset) │
                                   └──────────────┘
```

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Runner OS | `windows-latest` for lint/test/build | App is Windows-only; tests must pass on Windows; PyInstaller builds a Windows `.exe` |
| Release runner | `ubuntu-latest` | Only needs to zip + create release; faster startup, cheaper minutes |
| Python linter | `ruff` | Fast, zero-config, single binary; no existing linter configured |
| Frontend lint | `npm run lint` (eslint) | Already configured in `eslint.config.js` |
| Python version | 3.12 | Stable, avoids 3.14 `pythonnet` incompatibility (see Phase 3B fix #8) |
| Node version | 22 | LTS, matches Vite 7 requirement |
| Artifact format | `.zip` of `onedir` output | `onedir` is the current PyInstaller mode; zip is standard for GitHub Releases |
| Tag pattern | `v*` (e.g., `v1.0.0`) | Standard convention for semver releases |

---

## Edge Cases & Notes

- **`pythonnet` on CI:** `requirements-build.txt` includes `pythonnet>=3.1.0rc0` (pre-release). The `--pre` flag in `pip install` is needed. The build job uses the same `pip install --pre -r requirements-build.txt` command as `build_windows.ps1`.
- **`fido2` data file:** The `.spec` file already handles bundling `fido2/public_suffix_list.dat` (Phase 3B fix #6). PyInstaller on CI will pick it up automatically.
- **`npm ci` vs `npm install`:** CI uses `npm ci` for deterministic installs from `package-lock.json`. Requires the lockfile to be committed.
- **Caching:** pip and npm caches speed up repeat runs. Cache keys are based on lockfile/requirements hashes.
- **Branch protection:** After the workflow works, enable "Require status checks to pass" on `main` in GitHub repo settings. This is a manual GitHub UI step, not automated.
- **WebView2 on CI:** Not needed — CI only builds the exe, doesn't run the desktop app. pywebview/pythonnet install in build job but are never invoked.

---

## Implementation Order

1. **Create `pyproject.toml`** with ruff config (2 min)
2. **Create `requirements-ci.txt`** (1 min)
3. **Create `.github/workflows/build.yml`** (20 min)
4. **Run linters locally to fix any pre-existing violations** — `ruff check backend/` and `cd frontend && npm run lint` (10 min)
5. **Push to `main` and verify workflow passes** (5 min)
6. **Test release flow:** create and push a `v0.1.0-beta` tag, verify GitHub Release is created with `.zip` (5 min)

**Estimated total: ~45 minutes**

---

## Acceptance Criteria

- [ ] `.github/workflows/build.yml` exists with lint, test, build, and release jobs
- [ ] Push to `main` triggers lint + test + frontend build + exe build
- [ ] PR against `main` triggers lint + test + frontend build (no exe build)
- [ ] Pushing a `v*` tag creates a GitHub Release with a downloadable `.zip` containing the exe
- [ ] Python lint (`ruff`) passes with zero errors
- [ ] TypeScript lint (`eslint`) passes with zero errors
- [ ] Python tests (`pytest`) pass
- [ ] Frontend tests (`vitest`) pass
- [ ] Frontend build (`tsc + vite`) succeeds
- [ ] PyInstaller produces `iCloudPhotoSorter.exe` on CI
- [ ] All jobs use caching for pip and npm dependencies
