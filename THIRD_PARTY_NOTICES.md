# Third-Party Notices

This project is source-available under the PolyForm Noncommercial License 1.0.0. Third-party dependencies are licensed by their respective authors under their own license terms and are not relicensed by this project.

This file lists direct project dependencies and selected bundled runtime/transitive components used by the current build. Transitive dependencies also retain their own licenses. Before publishing public binary releases, verify the generated package contents and include any additional required notices from bundled dependencies.

## Python Runtime And Packaging Dependencies

| Package | License | Notes |
| --- | --- | --- |
| `pyicloud` | MIT | iCloud authentication and metadata access. |
| `fastapi` | MIT | Backend API framework. |
| `uvicorn` | BSD-3-Clause | ASGI server. |
| `pydantic` | MIT | Runtime schema validation used by FastAPI. |
| `starlette` | BSD-3-Clause | ASGI framework used by FastAPI. |
| `anyio` | MIT | Async runtime support used by backend dependencies. |
| `requests` | Apache-2.0 | HTTP dependency used by iCloud-related dependencies. |
| `certifi` | MPL-2.0 | Certificate authority bundle included in packaged builds. |
| `fido2` | BSD-style license | WebAuthn/FIDO support dependency included by the packaged build. |
| `pywebview` | BSD-3-Clause | Native desktop window wrapper. |
| `pythonnet` | MIT | Runtime support used by pywebview on Windows. |
| `pyinstaller` | GPL-2.0-or-later with special exception | Build tool and bootloader; exception permits distributing non-free programs built with PyInstaller. |

## Python Test And CI Dependencies

| Package | License | Notes |
| --- | --- | --- |
| `pytest` | MIT | Backend tests. |
| `pytest-asyncio` | Apache-2.0 | Async backend tests. |
| `httpx` | BSD-3-Clause | API tests. |
| `ruff` | MIT | Python linting in CI. |

## Frontend Runtime Dependencies

| Package | License | Notes |
| --- | --- | --- |
| `react` | MIT | Frontend UI runtime. |
| `react-dom` | MIT | React DOM renderer. |

## Frontend Development Dependencies

| Package | License | Notes |
| --- | --- | --- |
| `@eslint/js` | MIT | ESLint JavaScript rules. |
| `@testing-library/jest-dom` | MIT | Frontend test assertions. |
| `@testing-library/react` | MIT | React component tests. |
| `@testing-library/user-event` | MIT | Frontend user-event tests. |
| `@types/node` | MIT | TypeScript Node.js types. |
| `@types/react` | MIT | TypeScript React types. |
| `@types/react-dom` | MIT | TypeScript React DOM types. |
| `@vitejs/plugin-react` | MIT | Vite React plugin. |
| `eslint` | MIT | Frontend linting. |
| `eslint-plugin-react-hooks` | MIT | React Hooks lint rules. |
| `eslint-plugin-react-refresh` | MIT | React Refresh lint rules. |
| `globals` | MIT | Global identifier definitions for ESLint. |
| `jsdom` | MIT | Browser-like test environment. |
| `typescript` | Apache-2.0 | TypeScript compiler. |
| `typescript-eslint` | MIT | TypeScript ESLint tooling. |
| `vite` | MIT | Frontend build tool. |
| `vitest` | MIT | Frontend test runner. |

## License Compatibility Note

Permissive dependencies such as MIT, BSD, and Apache-licensed packages may be used by this source-available project while retaining their original license terms. Users receive the rights granted by each dependency's own license for that dependency; those licenses do not change the license of this project's original code.
