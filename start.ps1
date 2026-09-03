$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot "venv\Scripts\python.exe"
$nextCli = Join-Path $projectRoot "frontend\node_modules\next\dist\bin\next"
$runDirectory = Join-Path $projectRoot ".run"
$pidFile = Join-Path $runDirectory "app-pids.json"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python sanal ortami bulunamadi. README dosyasindaki kurulum adimlarini uygulayin."
}

if (-not (Test-Path -LiteralPath $nextCli)) {
    throw "Frontend paketleri bulunamadi. Frontend klasorunde 'pnpm install' calistirin."
}

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCommand) {
    $nodePath = $nodeCommand.Source
} else {
    $codexNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
    if (-not (Test-Path -LiteralPath $codexNode)) {
        throw "Node.js bulunamadi. Node.js 20 veya daha yeni bir surum kurun."
    }
    $nodePath = $codexNode
}

if (Test-Path -LiteralPath $pidFile) {
    $savedProcesses = Get-Content -Raw -LiteralPath $pidFile | ConvertFrom-Json
    $runningProcess = @($savedProcesses.frontend_pid, $savedProcesses.backend_pid) |
        Where-Object { $_ -and (Get-Process -Id $_ -ErrorAction SilentlyContinue) } |
        Select-Object -First 1

    if ($runningProcess) {
        Write-Host "SEDA zaten calisiyor."
        Write-Host "Arayuz: http://127.0.0.1:3000"
        Start-Process "http://127.0.0.1:3000"
        exit 0
    }

    # Bilgisayar beklenmeden kapandiysa eski PID dosyasi kalabilir.
    Remove-Item -LiteralPath $pidFile -Force
}

New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null

$backend = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $runDirectory "backend.log") `
    -RedirectStandardError (Join-Path $runDirectory "backend-error.log") `
    -PassThru

try {
    $frontend = Start-Process `
        -FilePath $nodePath `
        -ArgumentList @($nextCli, "dev", "--hostname", "127.0.0.1", "--port", "3000") `
        -WorkingDirectory (Join-Path $projectRoot "frontend") `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $runDirectory "frontend.log") `
        -RedirectStandardError (Join-Path $runDirectory "frontend-error.log") `
        -PassThru
} catch {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    throw
}

@{
    backend_pid = $backend.Id
    frontend_pid = $frontend.Id
} | ConvertTo-Json | Set-Content -LiteralPath $pidFile -Encoding UTF8

Start-Sleep -Seconds 2
Write-Host "SEDA baslatildi."
Write-Host "Arayuz: http://127.0.0.1:3000"
Write-Host "API:     http://127.0.0.1:8000/docs"
Write-Host "Kapatmak icin: .\kapat.cmd"
Start-Process "http://127.0.0.1:3000"
