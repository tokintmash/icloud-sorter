# build_windows.ps1 - Build iCloud Photo Sorter for Windows
# Usage: .\scripts\build_windows.ps1

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..

Write-Host "=== Step 1: Build frontend ===" -ForegroundColor Cyan
Push-Location frontend
cmd /c "npm install 2>&1"
if ($LASTEXITCODE -ne 0) { Write-Error "npm install failed"; exit 1 }
cmd /c "npm run build 2>&1"
if ($LASTEXITCODE -ne 0) { Write-Error "npm run build failed"; exit 1 }
Write-Host "[DEBUG] npm done, LASTEXITCODE=$LASTEXITCODE" -ForegroundColor Yellow
Pop-Location
Write-Host "[DEBUG] Pop-Location done, pwd=$(Get-Location)" -ForegroundColor Yellow

if (-not (Test-Path "frontend\dist\index.html")) {
    Write-Error "Frontend build failed - frontend\dist\index.html not found"
    exit 1
}
Write-Host "[DEBUG] dist check passed" -ForegroundColor Yellow

Write-Host "=== Step 2: Install Python dependencies ===" -ForegroundColor Cyan
pip install --pre -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed"; exit 1 }

Write-Host "=== Step 3: Stamp beta build date ===" -ForegroundColor Cyan
python scripts/stamp_beta.py
if ($LASTEXITCODE -ne 0) { Write-Error "Beta stamp failed"; exit 1 }

Write-Host "=== Step 4: Run PyInstaller ===" -ForegroundColor Cyan
pyinstaller icloud_sorter.spec --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller failed"; exit 1 }

if (Test-Path "dist\iCloudPhotoSorter\iCloudPhotoSorter.exe") {
    Write-Host ""
    Write-Host "=== Build complete ===" -ForegroundColor Green
    Write-Host "Output: dist\iCloudPhotoSorter\iCloudPhotoSorter.exe"
} else {
    Write-Error "Build failed - exe not found"
    exit 1
}
