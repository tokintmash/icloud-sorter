# Phase 3C Plan — Review Findings

**Reviewed:** 2026-04-15

---

## Issues to Fix Before Implementation

- [x] **`workflow_dispatch` can't build exe:** Added `|| github.event_name == 'workflow_dispatch'` to `build-exe` job condition.

- [x] **Frontend dist artifact path mismatch:** Set `path: frontend/dist` in the `download-artifact` step of `build-exe` job.

- [x] **`requirements-ci.txt` isn't used in the workflow:** Workflow Job 1 now installs from `requirements-ci.txt` (which includes `backend/requirements.txt` + `ruff`).

- [x] **Missing `--pre` flag in Job 1:** Verified `backend/requirements.txt` has no pre-release deps — `--pre` not needed.

- [x] **Ruff `E501` ignored + `line-length: 120`:** Removed `line-length` from `pyproject.toml` since `E501` is ignored anyway.

- [x] **Spec file implicit dependency on `certifi`/`fido2`:** Added a comment in the workflow's `build-exe` job documenting this.
