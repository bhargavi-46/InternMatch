# Refreshes the live job database from this PC.
#
# Workday (NVIDIA, Intel, Adobe, PayPal, ...) answers HTTP 429 to GitHub's servers but not to home internet,
# so this run picks up the Workday companies that the daily GitHub Actions refresh has to skip.
# Boards that fail in either run keep their existing jobs, so the two refreshes don't undo each other.
#
# Setup: put one line, DATABASE_URL=<your Neon connection string>, in
#   %USERPROFILE%\.internmatch\neon.env
# (outside the repo and OneDrive, so it is never committed or synced; not under AppData, which packaged apps
# redirect to private copies). Output goes to refresh.log next to it.
#
# Run by hand:  powershell -ExecutionPolicy Bypass -File backend\scripts\refresh-from-pc.ps1

$ErrorActionPreference = 'Stop'
$dataDir = Join-Path $env:USERPROFILE '.internmatch'
$secretFile = Join-Path $dataDir 'neon.env'
$logFile = Join-Path $dataDir 'refresh.log'
$uv = Join-Path $env:USERPROFILE '.local\bin\uv.exe'

$line = Get-Content $secretFile | Where-Object { $_ -match '^\s*DATABASE_URL\s*=\s*\S' } | Select-Object -First 1
if (-not $line) { throw "Add a line DATABASE_URL=<Neon connection string> to $secretFile" }
# Environment variables take priority over backend\.env, which keeps DATABASE_URL=local for development.
$env:DATABASE_URL = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
$env:PYTHONUTF8 = '1'

Set-Location (Split-Path $PSScriptRoot -Parent)  # backend\
Add-Content $logFile "=== $(Get-Date -Format 'yyyy-MM-dd HH:mm') refresh started ==="
# cmd /c keeps Python's stderr (log lines) out of PowerShell's error handling.
cmd /c "`"$uv`" run python -m app.ingest.run >> `"$logFile`" 2>&1"
$code = $LASTEXITCODE
Add-Content $logFile "=== $(Get-Date -Format 'yyyy-MM-dd HH:mm') refresh finished (exit code $code) ==="
exit $code
