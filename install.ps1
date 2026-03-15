# ──────────────────────────────────────────────────────────────
# 酒店影像控制系統 — Windows Installer
# Run: powershell -ExecutionPolicy Bypass -File install.ps1
# ──────────────────────────────────────────────────────────────

param(
    [switch]$SkipPython,
    [string]$InstallDir = "$env:LOCALAPPDATA\JiudianVideoControl"
)

$RepoUrl = "https://github.com/ryanalexmartin/jiudian-video-control.git"
$PythonMinVersion = [version]"3.10"
$VenvDir = "$InstallDir\.venv"
$ServerDir = "$InstallDir\server"

Write-Host ""
Write-Host "=== 酒店影像控制系統 — Installer ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. Check / install Python ───────────────────────────────

function Get-PythonPath {
    foreach ($cmd in @("python", "python3", "py")) {
        $p = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($p) {
            # Skip the Microsoft Store stub (WindowsApps)
            if ($p.Source -like "*WindowsApps*") { continue }
            $ver = & $cmd --version 2>&1
            if ($ver -match "(\d+\.\d+\.\d+)") {
                $v = [version]$Matches[1]
                if ($v -ge $PythonMinVersion) {
                    return $p.Source
                }
            }
        }
    }
    return $null
}

$PythonExe = Get-PythonPath

if (-not $PythonExe -and -not $SkipPython) {
    Write-Host "[1/5] Python >= $PythonMinVersion not found. Installing via winget..." -ForegroundColor Yellow
    try {
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $PythonExe = Get-PythonPath
    } catch {
        Write-Host "ERROR: Could not install Python. Please install Python 3.10+ manually from https://python.org" -ForegroundColor Red
        Write-Host "Then re-run this script." -ForegroundColor Red
        exit 1
    }
}

if (-not $PythonExe) {
    Write-Host "ERROR: Python >= $PythonMinVersion required but not found." -ForegroundColor Red
    exit 1
}

Write-Host "[1/5] Python found: $PythonExe" -ForegroundColor Green

# ── 2. Clone or update repo ─────────────────────────────────

$HasGit = Get-Command git -ErrorAction SilentlyContinue

if ($HasGit -and (Test-Path "$InstallDir\.git")) {
    Write-Host "[2/5] Updating existing installation..." -ForegroundColor Cyan
    Push-Location $InstallDir
    $gitOut = git pull --ff-only 2>&1 | Out-String
    Pop-Location
    Write-Host "     Updated" -ForegroundColor Gray
} elseif ($HasGit) {
    Write-Host "[2/5] Cloning repository..." -ForegroundColor Cyan
    if (Test-Path $InstallDir) {
        Remove-Item $InstallDir -Recurse -Force
    }
    $gitOut = git clone $RepoUrl $InstallDir 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Write-Host "     git clone failed, falling back to ZIP download..." -ForegroundColor Yellow
        $HasGit = $null  # Fall through to ZIP
    }
}

if (-not $HasGit) {
    Write-Host "[2/5] Downloading ZIP (git not available)..." -ForegroundColor Cyan
    $ZipUrl = "https://github.com/ryanalexmartin/jiudian-video-control/archive/refs/heads/main.zip"
    $ZipPath = "$env:TEMP\jiudian-video-control.zip"
    $ExtractPath = "$env:TEMP\jiudian-video-control-extract"

    if (Test-Path $InstallDir) {
        Remove-Item $InstallDir -Recurse -Force
    }
    if (Test-Path $ExtractPath) {
        Remove-Item $ExtractPath -Recurse -Force
    }

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
    Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force

    # The ZIP extracts to a subfolder named jiudian-video-control-main
    $Extracted = Get-ChildItem $ExtractPath | Select-Object -First 1
    Move-Item $Extracted.FullName $InstallDir

    Remove-Item $ZipPath -Force
    Remove-Item $ExtractPath -Recurse -Force
    Write-Host "     Downloaded and extracted" -ForegroundColor Gray
}

Write-Host "     Installed to: $InstallDir" -ForegroundColor Gray

# ── 3. Create venv and install deps ─────────────────────────

if (-not (Test-Path "$VenvDir\Scripts\python.exe")) {
    Write-Host "[3/5] Creating virtual environment..." -ForegroundColor Cyan
    & $PythonExe -m venv $VenvDir
} else {
    Write-Host "[3/5] Virtual environment exists" -ForegroundColor Green
}

$VenvPython = "$VenvDir\Scripts\python.exe"

Write-Host "     Installing dependencies (this may take a minute)..." -ForegroundColor Gray
& $VenvPython -m ensurepip --upgrade 2>&1 | Out-String | Out-Null
& $VenvPython -m pip install --upgrade pip --quiet 2>&1 | Out-String | Out-Null
& $VenvPython -m pip install -r "$ServerDir\requirements.txt" 2>&1 | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "     Dependencies installed." -ForegroundColor Green

# ── 4. Create launcher script ───────────────────────────────

Write-Host "[4/5] Creating launcher..." -ForegroundColor Cyan

$LauncherPath = "$InstallDir\JiudianVideoControl.bat"
$LauncherContent = @"
@echo off
title 酒店影像控制系統
cd /d "$InstallDir"
set PYTHONPATH=$ServerDir\src
"$VenvPython" -m jiudian_server --no-dev %*
"@

Set-Content -Path $LauncherPath -Value $LauncherContent -Encoding UTF8

# Dev mode launcher
$DevLauncherPath = "$InstallDir\JiudianVideoControl_Dev.bat"
$DevLauncherContent = @"
@echo off
title 酒店影像控制系統 (Dev)
cd /d "$InstallDir"
set PYTHONPATH=$ServerDir\src
"$VenvPython" -m jiudian_server --dev %*
"@

Set-Content -Path $DevLauncherPath -Value $DevLauncherContent -Encoding UTF8

# Also set PYTHONPATH so the module resolves
$RunnerPath = "$InstallDir\run.ps1"
$RunnerContent = @"
`$env:PYTHONPATH = "$ServerDir\src"
& "$VenvPython" -m jiudian_server @args
"@
Set-Content -Path $RunnerPath -Value $RunnerContent -Encoding UTF8

# ── 5. Create shortcuts ────────────────────────────────────

Write-Host "[5/5] Creating shortcuts..." -ForegroundColor Cyan

$WshShell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$DesktopLink = "$env:USERPROFILE\Desktop\酒店影像控制系統.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopLink)
$Shortcut.TargetPath = $LauncherPath
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "酒店影像控制系統 Video Control System"
$Shortcut.WindowStyle = 7  # Minimized (hides console)
$Shortcut.Save()
Write-Host "     Desktop shortcut created" -ForegroundColor Gray

# Start Menu shortcut
$StartMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\酒店影像控制系統"
if (-not (Test-Path $StartMenuDir)) {
    New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
}

$StartLink = "$StartMenuDir\酒店影像控制系統.lnk"
$Shortcut2 = $WshShell.CreateShortcut($StartLink)
$Shortcut2.TargetPath = $LauncherPath
$Shortcut2.WorkingDirectory = $InstallDir
$Shortcut2.Description = "酒店影像控制系統 Video Control System"
$Shortcut2.WindowStyle = 7
$Shortcut2.Save()
Write-Host "     Start Menu shortcut created" -ForegroundColor Gray

# ── Done ────────────────────────────────────────────────────

Write-Host ""
Write-Host "=== Installation complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "  Installed to:  $InstallDir" -ForegroundColor White
Write-Host "  Desktop shortcut: 酒店影像控制系統" -ForegroundColor White
Write-Host ""
Write-Host "  To run manually:" -ForegroundColor Gray
Write-Host "    Production:  $LauncherPath" -ForegroundColor Gray
Write-Host "    Dev mode:    $DevLauncherPath" -ForegroundColor Gray
Write-Host ""
Write-Host "  To update later, re-run this script." -ForegroundColor Gray
Write-Host ""
