$ErrorActionPreference = "Stop"

$pidFile = Join-Path $PSScriptRoot ".run\app-pids.json"
if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "Çalışan bir SEDA süreci kaydı bulunamadı."
    exit 0
}

$processes = Get-Content -Raw -LiteralPath $pidFile | ConvertFrom-Json
foreach ($processId in @($processes.frontend_pid, $processes.backend_pid)) {
    if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
        & taskkill.exe /PID $processId /T /F | Out-Null
    }
}

Remove-Item -LiteralPath $pidFile -Force
Write-Host "SEDA kapatıldı; model GPU belleğinden çıkarıldı."
