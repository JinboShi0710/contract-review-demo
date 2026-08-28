$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

foreach ($name in @('backend', 'frontend')) {
    $pidFile = Join-Path $projectDir "$name.pid"
    if (Test-Path -LiteralPath $pidFile) {
        $processId = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue
        if ($processId) {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host 'ContractLens 已停止。'
Start-Sleep -Seconds 2

