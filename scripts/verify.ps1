Write-Host "=== Running full project verification ===" -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent

Write-Host "`n[1/5] Linting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/lint.ps1"

Write-Host "`n[2/5] Checking formatting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/format.ps1" -CheckOnly

Write-Host "`n[3/5] Type checking..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/typecheck.ps1"

Write-Host "`n[4/5] Running tests..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/test.ps1"

Write-Host "`n[5/5] Running coverage..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/coverage.ps1"

Write-Host "`nAll checks passed." -ForegroundColor Green
