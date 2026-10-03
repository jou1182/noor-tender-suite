# منظومة النور — مشغّل العرض الكامل
# يشغّل: الخادم الخلفي :8000 + الواجهة :3000 + رادار المنافسات :4318 (اختياري)
# ثم يفتح المتصفح. أي مفتاح عند الإنهاء يوقف كل ما شُغّل من هنا.
$ErrorActionPreference = "Continue"
$ProjectDir = $PSScriptRoot
chcp 65001 | Out-Null

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
Say " منظومة النور — التشغيل الكامل" Cyan
Say " $ProjectDir" DarkGray
Say "============================================" Cyan

# ---------- فحوصات ما قبل التشغيل ----------
$py = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Say "خطأ: بيئة .venv غير موجودة في $ProjectDir" Red
    Say "أنشئها مرة واحدة: python -m venv .venv ; .venv\Scripts\python.exe -m pip install -r requirements.txt" Yellow
    Read-Host "`n اضغط Enter للخروج"; exit 1
}
$frontend = Join-Path $ProjectDir "frontend"
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Say "خطأ: frontend\node_modules غير موجود — نفّذ مرة واحدة: cd frontend ; npm install" Red
    Read-Host "`n اضغط Enter للخروج"; exit 1
}

# ---------- المنفذان 8000 و3000: إخلاء بموافقتك ----------
foreach ($port in 8000, 3000) {
    $owner = Get-PortOwner $port
    if ($owner) {
        Say "المنفذ $port مشغول حالياً بالعملية التالية:" Yellow
        Say "  PID $($owner.Pid) :: $($owner.Cmd)" DarkGray
        $ans = Read-Host "  اكتب K لإيقافها ومتابعة تشغيل منظومة النور، أو أي مفتاح آخر للخروج"
        if ($ans -ne "K" -and $ans -ne "k") {
            Say "تم الإلغاء — لم يتغير أي شيء." Red
            Read-Host "`n اضغط Enter للخروج"; exit 0
        }
        Stop-Process -Id $owner.Pid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        Say "أُوقفت العملية على المنفذ $port." Green
    }
}

# ---------- رادار المنافسات (اختياري) ----------
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

# ---------- التشغيل ----------
try {
    Say "[1] تشغيل الخادم الخلفي على :8000" Cyan
    Start-Process -FilePath $py -ArgumentList "-m uvicorn app.main:app --port 8000" -WorkingDirectory $ProjectDir -WindowStyle Minimized

    Say "[2] تشغيل الواجهة على :3000" Cyan
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory $frontend -WindowStyle Minimized

    if ($startRadar -and $radarPortFree) {
        Say "[3] تشغيل رادار المنافسات على :4318" Cyan
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run start" -WorkingDirectory $radar -WindowStyle Minimized
    } elseif (-not $startRadar) {
        Say "[3] رادار المنافسات مُتجاهَل (يتطلب Node >= 22.13 وnpm install داخل radar)" Yellow
    }

    Say "[4] الانتظار حتى تجهز الخدمات…" Cyan
    $backendOk = Wait-Url "http://localhost:8000/api/v1/health" 90
    $frontendOk = Wait-Url "http://localhost:3000" 120
    if ($backendOk -and $frontendOk) {
        Say "المنظومة جاهزة. يُفتح المتصفح الآن…" Green
        Start-Process "http://localhost:3000"
        Say "الواجهة:      http://localhost:3000" Green
        Say "واجهة البرمجة: http://localhost:8000/docs" Green
        Say "صفحة الرادار داخل المنظومة: http://localhost:3000/radar" Green
    } else {
        Say "تنبيه: الخادم=$backendOk الواجهة=$frontendOk بعد المهلة — افتح http://localhost:3000 يدوياً بعد لحظات." Yellow
    }

    Write-Host ""
    Say "اترك هذه النافذة مفتوحة أثناء العمل. اضغط أي مفتاح هنا لإيقاف المنظومة بالكامل." Yellow
    Read-Host " "
}
finally {
    Say "إيقاف منظومة النور…" Cyan
    Stop-ByPort @(8000, 3000, 4318)
    Say "توقفت كل الخدمات. إلى اللقاء." Green
    Start-Sleep -Seconds 2
}
