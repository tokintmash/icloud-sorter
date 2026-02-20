# Prerequisites

Before using iCloud Photo Downloader, you need to configure your iCloud account and install some software.

## iCloud Account Settings

### ⚠️ Required: Enable Web Access

You **must** enable "Access iCloud Data on the Web" for this tool to work:

1. On your iPhone/iPad: **Settings → [Your Name] → iCloud**
2. Find **"Access iCloud Data on the Web"**
3. **Turn it ON**

Without this setting, authentication will fail with an "Access Denied" error.

### ⚠️ Required: Disable Advanced Data Protection

If you have Advanced Data Protection (ADP) enabled, you **must** disable it:

1. On your iPhone/iPad: **Settings → [Your Name] → iCloud → Advanced Data Protection**
2. **Turn it OFF**

With ADP enabled, Apple encrypts your iCloud data in a way that prevents web-based access, and this tool will receive `ACCESS_DENIED` errors.

### Accept Terms of Service

Make sure you've accepted any pending iCloud Terms of Service by visiting [icloud.com](https://www.icloud.com) and logging in.

## Software Requirements

| Software | Version | Check Command |
|----------|---------|---------------|
| Python | 3.10 or higher | `python --version` |
| Node.js | 18 or higher | `node --version` |
| npm | 8 or higher | `npm --version` |
| Git | Any recent version | `git --version` |

### Installing Python

- **macOS:** `brew install python` or download from [python.org](https://www.python.org/downloads/)
- **Ubuntu/Debian:** `sudo apt install python3 python3-venv python3-pip`
- **Windows:** Download from [python.org](https://www.python.org/downloads/) (check "Add to PATH")

### Installing Node.js

- **All platforms:** Download from [nodejs.org](https://nodejs.org/) (LTS version recommended)
- **macOS:** `brew install node`
- **Ubuntu/Debian:** See [NodeSource](https://github.com/nodesource/distributions)
