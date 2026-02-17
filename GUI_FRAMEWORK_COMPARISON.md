# GUI Framework & Distribution Comparison Report

*Research date: February 2026 | For: iCloud Photo Downloader*

---

## Table of Contents

1. [Framework Comparison](#1-framework-comparison)
2. [Code Signing & Notarization](#2-code-signing--notarization)
3. [Auto-Update Strategies](#3-auto-update-strategies)
4. [Linux Distribution](#4-linux-distribution)
5. [Summary Matrix](#5-summary-matrix)
6. [Recommendation](#6-recommendation)

---

## 1. Framework Comparison

### 1.1 Electron (JavaScript/TypeScript)

| Attribute | Details |
|---|---|
| **Language** | JavaScript/TypeScript (Node.js backend + Chromium renderer) |
| **Bundle Size** | **80–120 MB** minimum (bundles full Chromium + Node.js) |
| **Memory Usage** | ~100 MB RAM idle for a basic app; grows quickly with windows |
| **Startup Time** | 1–2 seconds on mid-range hardware |
| **Maturity** | Released 2013 (GitHub). Extremely mature. Powers VS Code, Slack, Discord, 1Password 8 |
| **GitHub Stars** | ~115k |
| **Team Fit** | ✅ **Excellent** — team is proficient in JavaScript |

**Packaging & Distribution:**
- **electron-builder**: Most popular. Produces DMG/pkg (macOS), NSIS/MSI (Windows), AppImage/deb/snap (Linux). Built-in code signing and notarization support for both macOS and Windows. Directly integrates `@electron/osx-sign` and `@electron/notarize`.
- **Electron Forge**: Official Electron toolchain. Also supports macOS signing/notarization and Windows signing via `@electron/windows-sign`. Supports Azure Trusted Signing ($10/month, US/Canada only).
- Both tools have **first-class CI/CD support** (GitHub Actions workflows are well-documented).

**Auto-Update:**
- **electron-updater** (part of electron-builder): Mature, battle-tested. Supports GitHub Releases, S3, generic HTTP servers. Differential downloads on some platforms.
- **Squirrel.Windows** / **Squirrel.Mac**: Older approach, still works. Squirrel.Windows does delta updates.
- **update.electronjs.org**: Free update server for open-source projects on GitHub.

**Pros:**
- Largest ecosystem and community; extensive documentation and Stack Overflow coverage
- Widest compatibility (consistent Chromium rendering across all platforms)
- Most mature packaging and signing tooling of any framework
- Team already knows JavaScript
- Proven at scale (VS Code handles huge workspaces)

**Cons:**
- Largest bundle size and highest memory usage of all options
- Ships a full Chromium — "Chrome tab in a trench coat"
- Battery/CPU overhead on laptops
- Overkill for an app that's primarily doing network I/O

---

### 1.2 Tauri (Rust backend + Web frontend)

| Attribute | Details |
|---|---|
| **Language** | Rust (backend/core) + Any web framework (frontend) |
| **Bundle Size** | **2.5–6 MB** (uses OS native webview — WebView2/Windows, WebKit/macOS, WebKitGTK/Linux) |
| **Memory Usage** | ~30–40 MB RAM idle (58% less than Electron per benchmarks) |
| **Startup Time** | <500ms |
| **Maturity** | v2 stable (released 2024). Growing rapidly; 35% YoY adoption increase |
| **GitHub Stars** | ~88k |
| **Team Fit** | ⚠️ **Poor for backend** — team doesn't know Rust |

**Can the backend be written in something other than Rust?**
- **No, not directly.** The Tauri core and plugin system are Rust-only. Your backend logic (commands callable from JS) must be written in Rust.
- You *can* shell out to external processes (e.g., a Go or Python binary) from Rust, but this adds complexity and defeats the purpose.
- Tauri v2 plugins are also Rust-only. There is no official "write your backend in Go/JS" mode.
- **Verdict: The team would need to learn Rust** for any non-trivial backend work. For an app with heavy iCloud API logic, auth management, and download orchestration, this is a significant learning investment.

**Packaging & Distribution:**
- Built-in `tauri build` produces: DMG/app bundle (macOS), NSIS/MSI (Windows), AppImage/deb (Linux).
- **macOS notarization**: Supported via `tauri-action` GitHub Action and manual `notarytool` workflows.
- **Windows signing**: Supported by configuring certificate thumbprint in `tauri.conf.json`.
- Smaller bundle = faster downloads for users, smaller update payloads.

**Auto-Update:**
- **Built-in `tauri-plugin-updater`** (v2): First-class updater plugin. Supports static JSON files (GitHub Releases, S3, gists) and dynamic update servers. Cryptographic signature verification built in (EdDSA).
- **CrabNebula Cloud**: Official Tauri partner offering a managed update server with CDN distribution.
- Works well with **GitHub Actions + `tauri-action`** which auto-generates `latest.json`.

**Pros:**
- Dramatically smaller bundles and lower resource usage
- Built-in auto-updater with cryptographic signing
- Active, fast-growing community
- Modern security model (permissions/capabilities system)
- Mobile support (iOS/Android) in v2

**Cons:**
- **Rust learning curve is the dealbreaker** for this team
- WebView inconsistencies across platforms (WebKit on macOS vs Chromium-based WebView2 on Windows vs WebKitGTK on Linux) — CSS/JS behavior may differ
- Smaller ecosystem than Electron; fewer community resources
- Younger project — fewer production-scale references

---

### 1.3 Wails (Go backend + Web frontend)

| Attribute | Details |
|---|---|
| **Language** | Go (backend) + Any web framework (frontend) |
| **Bundle Size** | **8–19 MB** (uses OS native webview, same approach as Tauri) |
| **Memory Usage** | Similar to Tauri (~30–50 MB) |
| **Startup Time** | Fast (Go compiles to native code) |
| **Maturity** | v2.11 stable. **v3 in alpha** (nearly beta as of Dec 2025). v3 adds multi-window, system tray |
| **GitHub Stars** | ~32k |
| **Team Fit** | ✅ **Excellent** — team is proficient in Go |

**Architecture:**
- Go backend with bound methods callable from JavaScript frontend.
- Automatic TypeScript model generation from Go structs.
- Uses OS webview (WebView2 on Windows, WebKit on macOS, WebKitGTK on Linux).
- Supports Svelte, React, Vue, Preact, Lit, and vanilla JS templates.

**Packaging & Distribution:**
- `wails build` produces single binary with embedded assets.
- macOS: `.app` bundle. Windows: `.exe`. Linux: native binary.
- **Code signing guide exists** in the docs with GitHub Actions workflows for both macOS (using `gon` for notarization) and Windows (using `signtool`).
- No built-in installer format generation (no automatic DMG/NSIS) — you'd need to script this or use external tools.

**Auto-Update:**
- **No built-in auto-updater.** This is a planned feature for v3 (GitHub issue #1178, labeled "v3 TODO").
- Current approach: Use Go libraries like `go-selfupdate`, `minio/selfupdate`, or implement manually.
- Could also use **Sparkle** (macOS) + **WinSparkle** (Windows) with Go bindings (`go-winsparkle` exists).
- More work required compared to Electron or Tauri's built-in solutions.

**Wails v3 Status:**
- As of December 2025, the maintainer says it's "nearly ready" but no release date.
- v3 adds: multiple windows, system tray, improved bindings, improved build system (Taskfile), WML (declarative HTML attributes for runtime calls).
- **Recommendation: Build on v2 today** but design for easy migration to v3.

**Pros:**
- **Perfect language fit** — team knows Go; backend logic (auth, downloads, concurrency) is Go's sweet spot
- Go's goroutine model is ideal for concurrent downloads with cancellation
- Small bundle size (much smaller than Electron)
- Single binary deployment
- Active development; solid community (~32k stars)
- Apple & Microsoft Store compliant per docs

**Cons:**
- No built-in auto-updater (significant gap for desktop distribution)
- WebView inconsistencies (same issue as Tauri)
- Smaller community than Electron or Tauri
- v3 is still alpha — uncertainty around timeline
- Need to handle installer creation (DMG, NSIS) externally
- No built-in system tray in v2 (coming in v3)

---

### 1.4 Go + Fyne

| Attribute | Details |
|---|---|
| **Language** | Pure Go |
| **Bundle Size** | ~10–15 MB |
| **Look & Feel** | Custom-rendered (not native). Uses its own widget toolkit drawn via OpenGL/Metal/Vulkan |
| **Maturity** | v2.x. Active development. Growing but smaller community |
| **GitHub Stars** | ~25k |
| **Team Fit** | ✅ **Good** — team knows Go |

**Widget Set:**
- Label, Button, Entry, Select, Check, RadioGroup, Slider, ProgressBar, ProgressBarInfinite
- Form, Toolbar, Accordion, Calendar, DateEntry
- **Collections**: List, Table, Tree, GridWrap (virtualized, high performance)
- **Dialogs**: File open/save, color picker, confirm, custom
- System tray support
- Data binding system

**Packaging:**
- `fyne package` produces: `.app` bundle (macOS), `.exe` (Windows), tarball (Linux).
- **fyne-cross**: Docker-based cross-compilation tool. Builds for all platforms from any platform.
- No automatic DMG or NSIS installer generation.

**Pros:**
- Pure Go — no CGo, no external dependencies
- Cross-compiles easily
- Decent widget set (tables, lists, progress bars, file dialogs all exist)
- Single binary output
- Supports mobile (iOS/Android)

**Cons:**
- **Not native-looking** — custom-rendered UI looks "off" on each platform. Material Design-inspired but not matching any OS.
- Limited styling/theming compared to web-based UIs
- No rich text, no advanced layout system like CSS Flexbox/Grid
- File dialogs and some widgets feel less polished than native
- No built-in auto-updater
- Much smaller community and fewer third-party widgets than web-based frameworks
- Building a complex UI (progress bars per album, download queue, settings) would be significantly more work than HTML/CSS

---

### 1.5 Python + Qt (PyQt6/PySide6)

| Attribute | Details |
|---|---|
| **Language** | Python |
| **Bundle Size** | **40–100+ MB** (PyInstaller: ~77 MB typical; Nuitka: ~22–39 MB with optimization) |
| **Look & Feel** | Near-native (Qt Widgets) or custom (QML/Qt Quick) |
| **Maturity** | Qt: 30+ years. PyQt/PySide: very mature |
| **Team Fit** | ⚠️ **Moderate** — team has "some Python experience" |

**Packaging:**
- **PyInstaller**: Most popular. Produces ~77+ MB bundles. Known for false-positive virus detections (11 on VirusTotal).
- **Nuitka**: Compiles Python to C. Produces ~22–39 MB bundles. Fewer false positives (3 on VirusTotal). Better optimization.
- **cx_Freeze**: Alternative to PyInstaller. Similar size issues.
- All packaging tools struggle with dependency bloat (numpy/scipy add hundreds of MBs).

**GIL Implications:**
- Python's GIL limits true parallelism for CPU-bound work, but network I/O downloads are I/O-bound.
- `asyncio` or `threading` work fine for concurrent downloads.
- Qt has its own threading model (`QThread`) which integrates well.
- Not a significant concern for this use case (downloading files is I/O-bound).

**Pros:**
- `pyicloud` library already exists for iCloud authentication and photo access
- Qt provides excellent cross-platform native look and feel
- Extremely rich widget ecosystem
- Python is good for rapid prototyping

**Cons:**
- Packaging is painful — large binaries, false virus detections, complex dependency management
- Team has limited Python experience
- PyQt6 licensing: GPL or commercial ($550/dev/year). PySide6: LGPL (free for commercial use).
- Slower startup than compiled languages
- Distribution on Windows is particularly problematic (SmartScreen + virus false positives)

---

### 1.6 Python + Dear PyGui / customtkinter

| Attribute | Details |
|---|---|
| **Dear PyGui** | GPU-accelerated (ImGui-based). 15.2k stars. v2.1.1 (Nov 2025). Supports Windows/macOS/Linux. |
| **customtkinter** | Modern Tkinter wrapper. Consistent look across platforms. Simple API. |

**Dear PyGui:**
- Built on Dear ImGui (immediate mode). Very fast rendering.
- Good for: plots, node editors, data visualization.
- Poor for: traditional form-based desktop apps (no native file dialogs, no standard menu bars).
- Not a good fit for a download manager UI.

**customtkinter:**
- Modern-looking Tkinter. Dark/light mode. Consistent across platforms.
- Limited widget set compared to Qt (no Table widget, no Tree widget).
- Good for simple apps; struggles with complex UIs.
- Packaging same issues as all Python (PyInstaller/Nuitka).

**Verdict:** Neither is suitable for a production desktop application with the complexity needed here (album browser, download queue, progress tracking, settings). Qt is the only serious Python GUI option, and even then, packaging challenges remain.

---

## 2. Code Signing & Notarization

### 2.1 macOS

| Item | Details |
|---|---|
| **Apple Developer Program** | **$99/year** (required for Developer ID certificate) |
| **Certificate Types** | "Developer ID Application" (for signing) + "Developer ID Installer" (for pkg) |
| **Notarization Process** | 1. Sign app with `codesign` 2. Submit to Apple via `xcrun notarytool submit` 3. Wait (typically <15 min, 98% within 15 min) 4. Staple ticket: `xcrun stapler staple` |
| **Without Signing** | Gatekeeper blocks the app entirely on macOS 10.15+. Users must: right-click → Open → confirm, or use `xattr -d com.apple.quarantine`. **Extremely hostile UX.** |
| **Hardened Runtime** | Required for notarization. May need entitlements (e.g., network access, JIT). |

**Framework Signing Support:**

| Framework | macOS Signing/Notarization |
|---|---|
| **Electron** | ✅ **Best-in-class.** electron-builder and Forge both automate the entire sign+notarize+staple pipeline. Extensive docs. |
| **Tauri** | ✅ Good. `tauri-action` handles it in CI. Manual `notarytool` also documented. |
| **Wails** | ⚠️ Documented but manual. Uses `gon` tool (third-party) for signing+notarization. Requires setup. |
| **Fyne** | ⚠️ Manual. `fyne package` creates `.app` but signing/notarization is DIY. |
| **Python** | ⚠️ Manual. After PyInstaller/Nuitka builds, you sign and notarize externally. |

### 2.2 Windows

| Item | Details |
|---|---|
| **SmartScreen** | Microsoft Defender SmartScreen blocks/warns about apps without established reputation |
| **OV Certificate** | ~$170–$300/year. Signs code but does NOT bypass SmartScreen immediately. Reputation must be built "organically" over months/years of downloads. |
| **EV Certificate** | ~$300–$515/year. Requires hardware token (HSM). **As of March 2024, EV certificates NO LONGER provide instant SmartScreen bypass.** Same organic reputation building required. |
| **Azure Trusted Signing** | **$9.99/month.** Microsoft's new solution. Provides immediate SmartScreen reputation. **Only available to US/Canada organizations and individual developers.** EU organizations (but not individuals). Not available in most other countries. |
| **Without Signing** | SmartScreen shows "Windows protected your PC" with "Don't run" as the prominent option. Users must click "More info" → "Run anyway". **Most users will not do this.** |

**⚠️ Critical Note (2024+ Change):** The entire Windows code signing landscape shifted in March 2024. EV certificates, which previously gave instant SmartScreen bypass, no longer do. For indie developers, this is a significant challenge. Azure Trusted Signing is the best option if you're in the US/Canada.

**Framework Windows Signing Support:**

| Framework | Windows Signing |
|---|---|
| **Electron** | ✅ **Best.** electron-builder and Forge support traditional certs, Azure Trusted Signing, and cloud HSM providers. Well-documented. |
| **Tauri** | ✅ Good. Certificate thumbprint in config + timestamp URL. |
| **Wails** | ⚠️ Documented with `signtool` in CI but manual setup. |
| **Fyne** | ❌ No built-in support. Fully manual. |
| **Python** | ❌ No built-in support. Fully manual after packaging. |

### 2.3 Estimated Annual Signing Costs

| Item | Cost |
|---|---|
| Apple Developer Program | $99/year |
| OV Code Signing Certificate (Windows) | ~$200–$300/year |
| EV Code Signing Certificate (Windows) | ~$300–$515/year |
| Azure Trusted Signing (US/Canada only) | ~$120/year ($10/month) |
| **Total (Apple + OV Windows)** | **~$300–$400/year** |
| **Total (Apple + Azure Trusted Signing)** | **~$220/year** |

---

## 3. Auto-Update Strategies

### 3.1 Framework-Native Mechanisms

| Framework | Built-in Auto-Update | Quality |
|---|---|---|
| **Electron** | ✅ electron-updater (electron-builder), Squirrel | **Excellent.** Battle-tested. Supports GitHub Releases, S3, custom servers. Delta updates via Squirrel.Windows. |
| **Tauri** | ✅ `tauri-plugin-updater` | **Good.** Supports static JSON (GitHub Releases) and dynamic servers. Cryptographic signature verification (EdDSA). |
| **Wails** | ❌ None (planned for v3) | **N/A.** Must implement with Go libraries. |
| **Fyne** | ❌ None | **N/A.** Must implement manually. |
| **Python/Qt** | ❌ None | **N/A.** Must implement manually. |

### 3.2 External Update Libraries

| Library | Platform | Notes |
|---|---|---|
| **Sparkle** | macOS | De facto standard for macOS auto-updates. EdDSA signatures. Appcast XML format. |
| **WinSparkle** | Windows | Port of Sparkle for Windows. Same appcast format. C API with bindings for Go, Python, C#. 1.4k stars. |
| **go-selfupdate** | Cross-platform | Go library for self-updating binaries. Works with GitHub Releases. |
| **minio/selfupdate** | Cross-platform | Minimal Go self-update library. |

### 3.3 Distribution Backends

| Backend | Pros | Cons |
|---|---|---|
| **GitHub Releases** | Free, integrates with CI, trusted CDN, simple | Public only (paid for private repos), no analytics |
| **Self-hosted server** | Full control, analytics, release channels | Infrastructure cost, maintenance |
| **CrabNebula Cloud** | Managed Tauri updates, CDN, analytics | Tauri-specific, cost |
| **S3/CloudFront** | Scalable, cheap, global CDN | Setup complexity |

### 3.4 Delta vs Full Updates

| Approach | Electron | Tauri | Wails/Fyne |
|---|---|---|---|
| **Full replacement** | ✅ Default | ✅ Default | ✅ (manual) |
| **Delta/differential** | ✅ Squirrel.Windows | ❌ Not built-in | ❌ Not built-in |
| **Update size impact** | 80–120 MB per update | 2–6 MB per update | 8–19 MB per update |

Tauri's small bundle size makes delta updates less critical — a full 3 MB update is smaller than most Electron delta updates.

---

## 4. Linux Distribution

| Format | Pros | Cons | Recommendation |
|---|---|---|---|
| **AppImage** | No installation needed; single file; broadest distro support; portable | No sandboxing; no auto-updates (unless manually configured); no central repo | ✅ **Best for initial distribution** — simplest for users |
| **Flatpak** | Sandboxed; centralized repo (Flathub); auto-updates; verified publishers | Larger on disk (decompressed); requires `flatpak` runtime; initial setup on some distros | Good for long-term, but more packaging work |
| **Snap** | Auto-updates; sandboxed; Canonical-backed | Closed-source server; slower startup; controversial in community; requires `snapd` | Least recommended for third-party apps |

**Framework Linux Support:**
- **Electron**: electron-builder generates AppImage, deb, snap, Flatpak targets.
- **Tauri**: Generates AppImage and deb. Flatpak/Snap possible but not built-in.
- **Wails**: Generates native binary. AppImage packaging would need external tooling.
- **Fyne**: Generates tarball. AppImage packaging would need external tooling.

---

## 5. Summary Matrix

| Criteria | Electron | Tauri | Wails | Fyne | Python+Qt |
|---|---|---|---|---|---|
| **Team Skill Fit** | ✅ JS | ❌ Rust | ✅ Go | ✅ Go | ⚠️ Limited Python |
| **Bundle Size** | ❌ 80–120 MB | ✅ 2.5–6 MB | ✅ 8–19 MB | ✅ 10–15 MB | ⚠️ 22–100 MB |
| **Memory Usage** | ❌ ~100 MB+ | ✅ ~30–40 MB | ✅ ~30–50 MB | ✅ ~20–40 MB | ⚠️ ~60–80 MB |
| **UI Quality/Flexibility** | ✅ Full web stack | ✅ Full web stack | ✅ Full web stack | ⚠️ Custom widgets | ✅ Native Qt |
| **Packaging Maturity** | ✅ Excellent | ✅ Good | ⚠️ Basic | ⚠️ Basic | ❌ Painful |
| **Code Signing** | ✅ Automated | ✅ Good | ⚠️ Manual | ❌ Manual | ❌ Manual |
| **Auto-Update** | ✅ Built-in | ✅ Built-in | ❌ None | ❌ None | ❌ None |
| **iCloud Library Access** | ⚠️ Need to port/wrap pyicloud | ⚠️ Need to port/wrap | ⚠️ Need Go implementation | ⚠️ Need Go implementation | ✅ pyicloud exists |
| **Concurrency Model** | ⚠️ Node.js (async) | ✅ Rust (async/threads) | ✅ Go (goroutines) | ✅ Go (goroutines) | ⚠️ GIL (but I/O-bound OK) |
| **Production Readiness** | ✅ Proven at scale | ✅ Growing adoption | ⚠️ Fewer prod references | ⚠️ Fewer prod references | ✅ Qt is proven |
| **Community Size** | ✅ Largest | ✅ Large, growing | ⚠️ Moderate | ⚠️ Moderate | ✅ Large (Qt) |

---

## 6. Recommendation

### 🏆 Primary Recommendation: **Wails (Go + Web Frontend)**

**Rationale:**

1. **Perfect language fit**: The team is proficient in Go. The iCloud API client, authentication logic, concurrent download manager, and file operations are all backend-heavy — Go excels at all of these. Go's goroutine model is *ideal* for managing 50k+ photo downloads with configurable concurrency, cancellation, and progress reporting.

2. **Right-sized for the job**: This app is a download manager with a progress UI — it doesn't need Electron's 100 MB Chromium overhead. Wails' 8–19 MB bundles are practical and respectful of users' bandwidth.

3. **Web frontend flexibility**: The team knows JavaScript and can use React, Vue, or Svelte for the UI. This gives full CSS/HTML control for building a polished download progress UI.

4. **Go-to-TypeScript bindings**: Wails automatically generates TypeScript types from Go structs, giving type-safe communication between backend and frontend.

5. **The iCloud API gap is solvable**: While `pyicloud` exists only in Python, the iCloud API is HTTP-based. A Go implementation can be written (or the team can shell out to a Python process using `pyicloud`). The existing open-source `icloud-photos-downloader` (CLI, Python) can serve as the reference for endpoint behavior.

**Addressing Wails' Gaps:**

| Gap | Mitigation |
|---|---|
| No built-in auto-updater | Use `go-selfupdate` library + GitHub Releases. Or integrate Sparkle (macOS) + WinSparkle (Windows) via C bindings. ~1–2 weeks of work. |
| No built-in installer generation | Use `create-dmg` (macOS), NSIS (Windows) in CI. Well-documented patterns exist. |
| Code signing is manual | Follow Wails' signing guide with GitHub Actions. Same complexity as Tauri. |
| v3 not yet stable | Build on v2 today (stable). v3 migration is straightforward per maintainer. |
| WebView inconsistencies | For a download manager UI, this is low risk. Avoid cutting-edge CSS features. |

### 🥈 Alternative: **Electron (JavaScript/TypeScript)**

**Choose Electron if:**
- The team wants to **minimize DevOps/packaging work** — Electron's tooling is the most mature and automated
- **Auto-update is a hard Day-1 requirement** with no room for custom implementation
- The team wants the **largest possible community** for troubleshooting
- **Bundle size and memory usage are acceptable tradeoffs** for developer velocity

**Electron would be the safer but heavier choice.** It eliminates all packaging, signing, and update challenges at the cost of shipping 100+ MB of Chromium for what is essentially a download manager.

### ❌ Not Recommended for This Project

| Framework | Reason |
|---|---|
| **Tauri** | Despite superior technical metrics, the team doesn't know Rust. Learning Rust to write an iCloud API client, auth flow, and download manager is a 2–3 month detour that doesn't serve the project. |
| **Fyne** | Custom-rendered UI that doesn't look native on any platform. Limited widget flexibility for a complex download progress UI. No auto-update, no packaging automation. |
| **Python + Qt** | Team has limited Python experience. Packaging is notoriously painful (false virus detections, large bundles). Would only make sense if `pyicloud` compatibility were the top priority and the team had strong Python skills. |
| **Dear PyGui / customtkinter** | Insufficient widget sets and maturity for a production desktop application. |

---

## Open Questions for Team Decision

1. **Azure Trusted Signing**: Is the team/organization based in the US or Canada? If yes, $10/month Azure Trusted Signing is the best Windows signing option. If not, an OV certificate + organic reputation building is the path forward.

2. **Auto-update priority**: Is auto-update required for v1.0, or can the first release use manual download-from-GitHub-Releases? This significantly affects the Wails vs Electron decision.

3. **iCloud API approach**: Will the team write a Go iCloud client from scratch (using `icloud-photos-downloader` as reference), or embed/shell-out to Python `pyicloud`? This is the single biggest technical risk regardless of GUI framework choice.

4. **Linux priority**: Is Linux truly "nice-to-have" or actually required? Wails and Electron both support it well, but Wails' Linux output needs manual AppImage packaging.
