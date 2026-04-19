# Sonar Remediation Plan

Source: `sonar-issues.json` exported on 2026-04-19

This plan groups the current SonarQube Cloud findings by impact severity so they can be handled in separate sessions or batches.

Current totals:
- High: 3 issues
- Medium: 13 issues
- Low: 13 issues
- Total: 29 issues

Recommended fix order:
1. High
2. Medium
3. Low

## High

These are the most important findings because they affect reliability or point to risky test behavior.

- `backend/services/sorter_service.py:63` — `python:S7502` — Save the created asyncio task in a variable to avoid premature garbage collection.
- `backend/services/sorter_service.py:66` — `python:S3776` — Refactor the sorter function to reduce cognitive complexity from 61 to 15 or lower.
- `frontend/src/components/__tests__/SortProgress.test.tsx:35` — `typescript:S7740` — Stop assigning `this` to `mockEventSource`.

Suggested batch for next session:
- Stabilize the sorter background task lifecycle first.
- Refactor the large sorter function into smaller helpers while preserving behavior.
- Clean up the `SortProgress` test mock pattern and rerun frontend tests.

## Medium

These are worth addressing after the high-impact issues because they affect accessibility, test clarity, or code readability.

- `frontend/src/components/Settings.tsx:86` — `typescript:S6853` — A form label must be associated with a control.
- `frontend/src/components/Settings.tsx:88` — `typescript:S6853` — A form label must have accessible text.
- `frontend/src/components/Settings.tsx:102` — `typescript:S6853` — A form label must have accessible text.
- `backend/tests/test_icloud_service.py:76` — `python:S112` — Replace a generic `Exception` with a more specific exception.
- `backend/tests/test_icloud_service.py:77` — `python:S112` — Replace a generic `Exception` with a more specific exception.
- `backend/tests/test_icloud_service.py:86` — `python:S112` — Replace a generic `Exception` with a more specific exception.
- `backend/tests/test_icloud_service.py:96` — `python:S112` — Replace a generic `Exception` with a more specific exception.
- `backend/tests/test_icloud_service.py:373` — `python:S112` — Replace a generic `Exception` with a more specific exception.
- `backend/tests/test_routers.py:21` — `python:S2068` — Review the potentially hard-coded `"password"` credential in tests.
- `backend/tests/test_routers.py:29` — `python:S2068` — Review the potentially hard-coded `"password"` credential in tests.
- `backend/tests/test_routers.py:37` — `python:S2068` — Review the potentially hard-coded `"password"` credential in tests.
- `frontend/src/components/SortProgress.tsx:114` — `typescript:S3358` — Extract the nested ternary into a standalone statement.
- `frontend/src/components/SortProgress.tsx:120` — `typescript:S3358` — Extract the nested ternary into a standalone statement.

Suggested batch for next session:
- Fix `Settings.tsx` accessibility issues together.
- Replace generic exceptions in `test_icloud_service.py` in one pass.
- Adjust test passwords in `test_routers.py` to safer fixture names or generated values.
- Simplify the nested ternaries in `SortProgress.tsx`.

## Low

These are mostly cleanup and maintainability improvements. They are good final-pass items once the higher-impact work is complete.

- `backend/config.py:39` — `python:S5713` — Remove a redundant exception type from an `except` chain.
- `backend/config.py:41` — `python:S5713` — Remove a redundant exception type from an `except` chain.
- `desktop_launcher.py:90` — `python:S5713` — Remove a redundant exception type from an `except` chain.
- `backend/tests/test_icloud_service.py:76` — `python:S7500` — Replace a comprehension with a direct iterable passed to the collection constructor.
- `backend/tests/test_icloud_service.py:77` — `python:S7500` — Replace a comprehension with a direct iterable passed to the collection constructor.
- `backend/tests/test_icloud_service.py:86` — `python:S7500` — Replace a comprehension with a direct iterable passed to the collection constructor.
- `backend/tests/test_icloud_service.py:96` — `python:S7500` — Replace a comprehension with a direct iterable passed to the collection constructor.
- `backend/tests/test_icloud_service.py:290` — `python:S7500` — Replace a comprehension with a direct iterable passed to the collection constructor.
- `backend/tests/test_icloud_service.py:291` — `python:S7500` — Replace a comprehension with a direct iterable passed to the collection constructor.
- `backend/tests/test_icloud_service.py:373` — `python:S7500` — Replace a comprehension with a direct iterable passed to the collection constructor.
- `frontend/src/components/AlbumPicker.tsx:10` — `typescript:S6759` — Mark component props as read-only.
- `frontend/src/components/SortProgress.tsx:11` — `typescript:S6759` — Mark component props as read-only.
- `frontend/src/components/AuthScreen.tsx:9` — `typescript:S6759` — Mark component props as read-only.

Suggested batch for next session:
- Clean up redundant `except` clauses in backend startup/config paths.
- Apply the collection-constructor simplifications in `test_icloud_service.py`.
- Mark React component prop types as `Readonly<...>` or equivalent.

## Notes For The Next Session

- Use this plan together with `sonar-issues.json`; the JSON still contains the full Sonar metadata and rule IDs.
- Start with the High section even if some Low items look quicker.
- After each batch, rerun the relevant verification:
- Backend: `./venv/Scripts/python.exe -m pytest` or the project’s current pytest entry point
- Frontend: `cd frontend && npm run build`
