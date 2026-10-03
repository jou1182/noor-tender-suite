# Noor Tender Suite - full demo launcher
# Starts: backend :8000 + frontend :3000 + competitor radar :4318 (optional)
# Then opens the browser. Pressing any key at the end stops everything started here.
$ErrorActionPreference = "Continue"
$ProjectDir = $PSScriptRoot

function Say($msg, $color = "White") { Write-Host "  $msg" -ForegroundColor $color }

function Get-PortOwner($port) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $conn) { return $null }
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($conn.OwningProcess)" -ErrorAction SilentlyContinue
    return @{ Pid = $conn.OwningProcess; Cmd = $proc.CommandLine }
}

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

function Stop-ByPort($ports) {
    foreach ($port in $ports) {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($conn) {
            $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
        }
    }
}

Write-Host ""
Say "============================================" Cyan
Say "  Noor Tender Suite - Full Launch" Cyan
Say "  $ProjectDir" DarkGray
Say "============================================" Cyan

# ---------- Pre-flight checks ----------
$py = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Say "ERROR: .venv not found in $ProjectDir" Red
    Say "Create it once: python -m venv .venv ; .venv\Scripts\python.exe -m pip install -r requirements.txt" Yellow
    Read-Host "`n Press Enter to exit"; exit 1
}
$frontend = Join-Path $ProjectDir "frontend"
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Say "ERROR: frontend\node_modules not found - run once: cd frontend ; npm install" Red
    Read-Host "`n Press Enter to exit"; exit 1
}

# ---------- Ports 8000 and 3000: free only with your consent ----------
function Find-DockerCli {
    $candidates = @(
        (Get-Command docker -ErrorAction SilentlyContinue).Source,
        "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\resources\bin\docker.exe"
    )
    return $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
}

function Stop-DockerStack($port) {
    # Killing com.docker.backend.exe would crash Docker Desktop itself -
    # bring the project stack down properly instead.
    $docker = Find-DockerCli
    if (-not $docker) { return $false }
    Push-Location $ProjectDir
    & $docker compose down 2>&1 | Out-Null
    Pop-Location
    Start-Sleep -Seconds 3
    return (-not (Get-PortOwner $port))
}

foreach ($port in 8000, 3000) {
    $owner = Get-PortOwner $port
    if ($owner) {
        Say "Port $port is currently in use by:" Yellow
        Say "  PID $($owner.Pid) :: $($owner.Cmd)" DarkGray
        $isDocker = ($owner.Cmd -match "com\.docker\.backend")
        if ($isDocker) { Say "  This is a Docker container stack - it will be stopped with 'docker compose down'." Yellow }
        $ans = Read-Host "  Type K to stop it and continue with Noor Suite, or any other key to exit"
        if ($ans -ne "K" -and $ans -ne "k") {
            Say "Cancelled - nothing was changed." Red
            Read-Host "`n Press Enter to exit"; exit 0
        }
        $freed = $false
        if ($isDocker) { $freed = Stop-DockerStack $port }
        if (-not $freed) {
            Stop-Process -Id $owner.Pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
        Say "Process on port $port stopped." Green
    }
}

# ---------- Competitor radar (optional) ----------
$radar = Join-Path $ProjectDir "radar"
$startRadar = $false
if ((Test-Path (Join-Path $radar "scripts\etimad-sync-service.mjs")) -and (Test-Path (Join-Path $radar "node_modules"))) {
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $parts = ((node --version 2>$null) -replace '[^0-9.]', '') -split '\.'
        if ($parts.Count -ge 2) {
            $major = [int]$parts[0]; $minor = [int]$parts[1]
            if (($major -gt 22) -or ($major -eq 22 -and $minor -ge 13)) { $startRadar = $true }
        }
    }
}
if (-not (Get-PortOwner 4318)) { $radarPortFree = $true } else { $radarPortFree = $false; $startRadar = $false }

# ---------- Launch ----------
try {
    Say "[1] Starting backend on :8000" Cyan
    Start-Process -FilePath $py -ArgumentList "-m uvicorn app.main:app --port 8000" -WorkingDirectory $ProjectDir -WindowStyle Minimized

    Say "[2] Starting frontend on :3000" Cyan
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory $frontend -WindowStyle Minimized

    if ($startRadar -and $radarPortFree) {
        Say "[3] Starting competitor radar on :4318" Cyan
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run start" -WorkingDirectory $radar -WindowStyle Minimized
    } elseif (-not $startRadar) {
        Say "[3] Radar skipped (requires Node >= 22.13 and npm install inside radar)" Yellow
    }

    Say "[4] Waiting for services to come up..." Cyan
    $backendOk = Wait-Url "http://localhost:8000/api/v1/health" 90
    $frontendOk = Wait-Url "http://localhost:3000" 120
    if ($backendOk -and $frontendOk) {
        Say "Suite is ready. Opening browser..." Green
        Start-Process "http://localhost:3000"
        Say "Frontend: http://localhost:3000" Green
        Say "API docs: http://localhost:8000/docs" Green
        Say "Radar page inside the suite: http://localhost:3000/radar" Green
    } else {
        Say "WARNING: backend=$backendOk frontend=$frontendOk after timeout - open http://localhost:3000 manually in a few moments." Yellow
    }

    Write-Host ""
    Say "Keep this window open while working. Press any key here to stop the whole suite." Yellow
    Read-Host " "
}
finally {
    Say "Stopping Noor Tender Suite..." Cyan
    Stop-ByPort @(8000, 3000, 4318)
    Say "All services stopped. Goodbye." Green
    Start-Sleep -Seconds 2
}
