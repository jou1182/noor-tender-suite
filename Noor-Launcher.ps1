# Noor AI Platform - One-Click Launcher
# 1) Docker mode if Docker Desktop can start; 2) otherwise local mode (venv + npm run dev).
# No hard-coded project path: everything is relative to this script's folder.

$ErrorActionPreference = "Continue"
$ProjectDir = $PSScriptRoot
$FrontendUrl = "http://localhost:3000"
$BackendHealth = "http://localhost:8000/api/v1/health"

function Say($msg, $color = "White") { Write-Host "  $msg" -ForegroundColor $color }

function Test-Url($url) {
    try { return ((Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200) } catch { return $false }
}

function Wait-Url($url, $seconds) {
    $end = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $end) {
        if (Test-Url $url) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Test-DockerReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { return $false }
    docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

function Find-DockerDesktop {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\DockerDesktop\Docker Desktop.exe",
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    )
    return $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

Write-Host ""
Say "============================================" Cyan
Say " Noor AI Platform - Starting..." Cyan
Say " Project: $ProjectDir" DarkGray
Say "============================================" Cyan

if (-not (Test-Path (Join-Path $ProjectDir "app\main.py"))) {
    Say "ERROR: app\main.py not found next to this launcher ($ProjectDir)." Red
    Read-Host "  Press Enter to close"; exit 1
}

# Already running? just open it.
if ((Test-Url $BackendHealth) -and (Test-Url $FrontendUrl)) {
    Say "Platform already running." Green
    Start-Process $FrontendUrl
    exit 0
}

# ---------------- Docker mode ----------------
$mode = "local"
if (-not (Test-DockerReady)) {
    $exe = Find-DockerDesktop
    if ($exe) {
        Say "[1] Docker Desktop is not running - starting it (up to 90s)..." Yellow
        Start-Process $exe
        $waited = 0
        while (-not (Test-DockerReady) -and $waited -lt 90) { Start-Sleep -Seconds 3; $waited += 3 }
    }
}
if (Test-DockerReady) {
    Say "[1] Docker is ready. Starting containers..." Green
    Push-Location $ProjectDir
    docker compose up -d
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -eq 0) { $mode = "docker" } else { Say "docker compose failed - falling back to local mode." Yellow }
} else {
    Say "[1] Docker unavailable - using local mode." Yellow
}

# ---------------- Local mode ----------------
if ($mode -eq "local") {
    $py = Join-Path $ProjectDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) {
        Say "ERROR: .venv not found. Create it once:" Red
        Say "  python -m venv .venv ; .venv\Scripts\python.exe -m pip install -r requirements.txt" Gray
        Read-Host "  Press Enter to close"; exit 1
    }
    $frontend = Join-Path $ProjectDir "frontend"
    if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
        Say "ERROR: frontend\node_modules missing. Run once:  cd frontend ; npm install" Red
        Read-Host "  Press Enter to close"; exit 1
    }
    if (-not (Test-Url $BackendHealth)) {
        Say "[2] Starting backend on :8000 (new window)..." Cyan
        Start-Process -FilePath $py -ArgumentList "-m uvicorn app.main:app --port 8000" -WorkingDirectory $ProjectDir
    }
    if (-not (Test-Url $FrontendUrl)) {
        Say "[3] Starting frontend on :3000 (new window)..." Cyan
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory $frontend
    }
}

# ---------------- Wait & open ----------------
Say "[4] Waiting for backend and frontend..."
$backendOk = Wait-Url $BackendHealth 120
$frontendOk = Wait-Url $FrontendUrl 120
if ($backendOk -and $frontendOk) { Say "Platform is up ($mode mode)." Green }
else {
    Say "WARNING: backend=$backendOk frontend=$frontendOk after 120s - opening anyway." Yellow
}
Start-Process $FrontendUrl
Say "Open: $FrontendUrl   (API: http://localhost:8000)" Green
Write-Host ""
Read-Host "  Press Enter to close this window"
