# ============================================================
#  ConTech AI Platform — One-Click Launcher
#  نقرة واحدة: يشغّل المنصة ويفتح المتصفح تلقائياً
# ============================================================

$ErrorActionPreference = "SilentlyContinue"
$ProjectDir = "D:\Alrawaf\PY\Lead Architect _ConTech AI Platform"
$URL = "http://localhost:3000"

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "   ConTech AI Platform - Starting..." -ForegroundColor Cyan
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""

# ---------- 1) Docker Desktop يعمل؟ ----------
function Test-DockerReady {
    docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

if (-not (Test-DockerReady)) {
    Write-Host "  [1/4] Docker Desktop not running - launching it..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "        Waiting for Docker engine (up to 90s)...",
              ""
    $waited = 0
    while (-not (Test-DockerReady) -and $waited -lt 90) {
        Start-Sleep -Seconds 3
        $waited += 3
        Write-Host "        ... $($waited)s" -ForegroundColor DarkGray
    }
    if (-not (Test-DockerReady)) {
        Write-Host "  FAILED: Docker did not start. Open Docker Desktop manually and retry." -ForegroundColor Red
        Read-Host "  Press Enter to close"
        exit 1
    }
    Write-Host "  [OK] Docker is ready." -ForegroundColor Green
}
else {
    Write-Host "  [1/4] Docker already running." -ForegroundColor Green
}

# ---------- 2) تشغيل الحاويات (إن لم تكن تعمل) ----------
Write-Host "  [2/4] Ensuring platform containers are up..."
Push-Location $ProjectDir
docker compose up -d *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED: docker compose up. Check 'docker compose ps' output." -ForegroundColor Red
    Pop-Location
    Read-Host "  Press Enter to close"
    exit 1
}
Pop-Location
Write-Host "  [OK] Containers are up." -ForegroundColor Green

# ---------- 3) انتظار جاهزية الواجهة والخادم فعلياً ----------
Write-Host "  [3/4] Waiting for the app to answer..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$URL/api/v1/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
}

if (-not $ready) {
    Write-Host "  WARNING: App did not answer within 60s - opening browser anyway." -ForegroundColor Yellow
} else {
    Write-Host "  [OK] Platform is answering (backend + frontend healthy)." -ForegroundColor Green
}

# ---------- 4) فتح المتصفح ----------
Write-Host "  [4/4] Opening your browser -> $URL"
Start-Process $URL

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Green
Write-Host "   Platform is ready. Browser opened at:" -ForegroundColor Green
Write-Host "   $URL" -ForegroundColor White
Write-Host ""
Write-Host "   Remember: you only ever use port 3000 in the" -ForegroundColor Gray
Write-Host "   browser - port 8000 is the internal engine." -ForegroundColor Gray
Write-Host "  ============================================" -ForegroundColor Green
Write-Host ""
Read-Host "  Press Enter to close this window"
