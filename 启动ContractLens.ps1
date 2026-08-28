$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectDir 'backend'
$frontendDir = Join-Path $projectDir 'frontend'
$pythonExe = Join-Path $backendDir '.venv\Scripts\python.exe'
$npmCmd = 'C:\Program Files\nodejs\npm.cmd'

if (-not (Test-Path -LiteralPath $pythonExe)) {
    Write-Host '后端虚拟环境不存在，请先安装后端依赖。' -ForegroundColor Red
    Read-Host '按回车退出'
    exit 1
}

if (-not (Test-Path -LiteralPath (Join-Path $frontendDir 'node_modules'))) {
    Write-Host '前端依赖不存在，请先运行 npm.cmd install。' -ForegroundColor Red
    Read-Host '按回车退出'
    exit 1
}

if (-not (Get-NetTCPConnection -LocalPort 8006 -State Listen -ErrorAction SilentlyContinue)) {
    $backend = Start-Process -FilePath $pythonExe `
        -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8006') `
        -WorkingDirectory $backendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $projectDir 'backend.out.log') `
        -RedirectStandardError (Join-Path $projectDir 'backend.err.log') `
        -PassThru
    Set-Content -LiteralPath (Join-Path $projectDir 'backend.pid') -Value $backend.Id
}

if (-not (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue)) {
    $frontend = Start-Process -FilePath $npmCmd `
        -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1') `
        -WorkingDirectory $frontendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $projectDir 'frontend.out.log') `
        -RedirectStandardError (Join-Path $projectDir 'frontend.err.log') `
        -PassThru
    Set-Content -LiteralPath (Join-Path $projectDir 'frontend.pid') -Value $frontend.Id
}

Start-Sleep -Seconds 4
Start-Process 'http://127.0.0.1:3000'

