$ErrorActionPreference = "Stop"

$pidFile = Join-Path $PSScriptRoot ".run\app-pids.json"
if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "Calisan bir SEDA sureci bulunamadi."
    exit 0
}

$processes = Get-Content -Raw -LiteralPath $pidFile | ConvertFrom-Json
foreach ($processId in @($processes.frontend_pid, $processes.backend_pid)) {
    if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
        & taskkill.exe /PID $processId /T /F | Out-Null
    }
}

Remove-Item -LiteralPath $pidFile -Force
Write-Host "SEDA kapatildi; model GPU belleginden cikarildi."
