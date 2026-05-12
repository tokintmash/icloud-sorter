# build_msi.ps1 - Build the Windows MSI installer
# Usage: .\scripts\build_msi.ps1 [-Version 1.2.3] [-SkipBuild]

[CmdletBinding()]
param(
    [string]$Version,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function ConvertTo-XmlValue {
    param([Parameter(Mandatory=$true)][string]$Value)
    return [System.Security.SecurityElement]::Escape($Value)
}

function ConvertTo-WixId {
    param(
        [Parameter(Mandatory=$true)][string]$Prefix,
        [Parameter(Mandatory=$true)][string]$Seed
    )
    $md5 = [System.Security.Cryptography.MD5]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Seed.ToLowerInvariant())
        $hash = [BitConverter]::ToString($md5.ComputeHash($bytes)).Replace("-", "")
        return "{0}_{1}" -f $Prefix, $hash.Substring(0, 32)
    } finally {
        $md5.Dispose()
    }
}

function ConvertTo-StableGuid {
    param([Parameter(Mandatory=$true)][string]$Seed)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes("icloud-photo-sorter-msi:$($Seed.ToLowerInvariant())")
        $hashBytes = $md5.ComputeHash($bytes)
        $hashBytes[6] = [byte](($hashBytes[6] -band 0x0F) -bor 0x30)
        $hashBytes[8] = [byte](($hashBytes[8] -band 0x3F) -bor 0x80)
        return ([Guid]::new($hashBytes)).ToString("D").ToUpperInvariant()
    } finally {
        $md5.Dispose()
    }
}

function Get-RelativePath {
    param(
        [Parameter(Mandatory=$true)][string]$BasePath,
        [Parameter(Mandatory=$true)][string]$TargetPath
    )
    $baseFullPath = (Resolve-Path -LiteralPath $BasePath).ProviderPath.TrimEnd("\") + "\"
    $targetFullPath = (Resolve-Path -LiteralPath $TargetPath).ProviderPath
    $baseUri = [Uri]$baseFullPath
    $targetUri = [Uri]$targetFullPath
    return [Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace("/", "\")
}

function Get-ParentRelativePath {
    param([Parameter(Mandatory=$true)][string]$RelativePath)
    $parent = Split-Path -Path $RelativePath -Parent
    if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq ".") {
        return ""
    }
    return $parent
}

function New-WixPayloadAuthoring {
    param(
        [Parameter(Mandatory=$true)][string]$SourceDir,
        [Parameter(Mandatory=$true)][string]$OutputPath
    )

    $directories = @(Get-ChildItem -LiteralPath $SourceDir -Directory -Recurse | Sort-Object FullName)
    $files = @(Get-ChildItem -LiteralPath $SourceDir -File -Recurse | Sort-Object FullName)

    if ($files.Count -eq 0) {
        throw "No files found in MSI payload source: $SourceDir"
    }

    $dirIds = @{ "" = "INSTALLFOLDER" }
    foreach ($directory in $directories) {
        $relativePath = Get-RelativePath -BasePath $SourceDir -TargetPath $directory.FullName
        $dirIds[$relativePath] = ConvertTo-WixId -Prefix "dir" -Seed $relativePath
    }

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add('<?xml version="1.0" encoding="UTF-8"?>')
    $lines.Add('<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">')
    $lines.Add('  <Fragment>')

    foreach ($directory in $directories) {
        $relativePath = Get-RelativePath -BasePath $SourceDir -TargetPath $directory.FullName
        $parentRelativePath = Get-ParentRelativePath -RelativePath $relativePath
        $parentId = $dirIds[$parentRelativePath]
        $directoryId = $dirIds[$relativePath]
        $directoryName = ConvertTo-XmlValue -Value $directory.Name

        $lines.Add("    <DirectoryRef Id=`"$parentId`">")
        $lines.Add("      <Directory Id=`"$directoryId`" Name=`"$directoryName`" />")
        $lines.Add('    </DirectoryRef>')
    }

    $lines.Add('  </Fragment>')
    $lines.Add('  <Fragment>')
    $lines.Add('    <ComponentGroup Id="AppPayload">')

    foreach ($file in $files) {
        $relativePath = Get-RelativePath -BasePath $SourceDir -TargetPath $file.FullName
        $parentRelativePath = Get-ParentRelativePath -RelativePath $relativePath
        $directoryId = $dirIds[$parentRelativePath]
        $componentId = ConvertTo-WixId -Prefix "cmp" -Seed $relativePath
        $fileId = ConvertTo-WixId -Prefix "fil" -Seed $relativePath
        $componentGuid = ConvertTo-StableGuid -Seed $relativePath
        $sourcePath = ConvertTo-XmlValue -Value $file.FullName

        $lines.Add("      <Component Id=`"$componentId`" Directory=`"$directoryId`" Guid=`"$componentGuid`">")
        $lines.Add("        <File Id=`"$fileId`" Source=`"$sourcePath`" KeyPath=`"yes`" />")
        $lines.Add('      </Component>')
    }

    $lines.Add('    </ComponentGroup>')
    $lines.Add('  </Fragment>')
    $lines.Add('</Wix>')

    $outputDir = Split-Path -Parent $OutputPath
    if (-not (Test-Path -LiteralPath $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir | Out-Null
    }
    Set-Content -LiteralPath $OutputPath -Value $lines -Encoding UTF8
}

function Invoke-WixBuild {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)

    $wixCommand = Get-Command wix -ErrorAction SilentlyContinue
    if ($wixCommand) {
        & $wixCommand.Source @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "WiX build failed with exit code $LASTEXITCODE"
        }
        return
    }

    $wixGlobalTool = Join-Path $env:USERPROFILE ".dotnet\tools\wix.exe"
    if (Test-Path -LiteralPath $wixGlobalTool) {
        & $wixGlobalTool @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "WiX build failed with exit code $LASTEXITCODE"
        }
        return
    }

    throw "WiX Toolset CLI was not found. Install WiX v5+ so 'wix --version' works, then rerun this script."
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).ProviderPath
Set-Location $repoRoot

$metadataPath = Join-Path $repoRoot "packaging\metadata.json"
$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = $metadata.version
}

if ($Version -notmatch '^\d{1,5}\.\d{1,5}\.\d{1,5}$') {
    throw "MSI version must use numeric major.minor.patch format, for example 1.2.3. Received: $Version"
}

if (-not $SkipBuild) {
    & (Join-Path $repoRoot "scripts\build_windows.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "Windows app build failed with exit code $LASTEXITCODE"
    }
}

$appSourceDir = Join-Path $repoRoot "dist\iCloudPhotoSorter"
$appExe = Join-Path $appSourceDir "iCloudPhotoSorter.exe"
if (-not (Test-Path -LiteralPath $appExe)) {
    throw "PyInstaller output not found: $appExe"
}

$wixBuildDir = Join-Path $repoRoot "build\wix"
$payloadWxs = Join-Path $wixBuildDir "payload.wxs"
New-WixPayloadAuthoring -SourceDir $appSourceDir -OutputPath $payloadWxs

$installerDir = Join-Path $repoRoot "dist\installer"
if (-not (Test-Path -LiteralPath $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir | Out-Null
}

$outputName = "{0}-{1}-x64.msi" -f $metadata.outputBaseName, $Version
$outputMsi = Join-Path $installerDir $outputName
if (Test-Path -LiteralPath $outputMsi) {
    Remove-Item -LiteralPath $outputMsi -Force
}

$wixArgs = @(
    "build",
    (Join-Path $repoRoot "packaging\Product.wxs"),
    $payloadWxs,
    "-arch",
    "x64",
    "-out",
    $outputMsi,
    "-d",
    "ProductName=$($metadata.productName)",
    "-d",
    "Manufacturer=$($metadata.manufacturer)",
    "-d",
    "ProductVersion=$Version",
    "-d",
    "UpgradeCode=$($metadata.upgradeCode)"
)

Invoke-WixBuild -Arguments $wixArgs

if (-not (Test-Path -LiteralPath $outputMsi)) {
    throw "MSI build finished without producing expected output: $outputMsi"
}

Write-Host "MSI build complete: $outputMsi" -ForegroundColor Green
