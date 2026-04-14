# build_windows.ps1 — Build iCloud Photo Sorter for Windows
# Usage: .\scripts\build_windows.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "=== Step 1: Build frontend ===" -ForegroundColor Cyan
Push-Location frontend
npm install
npm run build
Pop-Location

if (-not (Test-Path "frontend\dist\index.html")) {
    Write-Error "Frontend build failed — frontend\dist\index.html not found"
    exit 1
}

Write-Host "=== Step 2: Install Python dependencies ===" -ForegroundColor Cyan
pip install -r requirements-build.txt

Write-Host "=== Step 3: Run PyInstaller ===" -ForegroundColor Cyan
pyinstaller icloud_sorter.spec --noconfirm

if (Test-Path "dist\iCloudPhotoSorter\iCloudPhotoSorter.exe") {
    Write-Host ""
    Write-Host "=== Build complete ===" -ForegroundColor Green
    Write-Host "Output: dist\iCloudPhotoSorter\iCloudPhotoSorter.exe"
} else {
    Write-Error "Build failed — exe not found"
    exit 1
}
