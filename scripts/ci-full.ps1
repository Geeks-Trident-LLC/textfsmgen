Write-Host "=== Full CI Pipeline ===" -ForegroundColor Cyan

# Lint
Write-Host "`n[1/9] Linting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/lint.ps1"

# Format check
Write-Host "`n[2/9] Checking formatting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/format.ps1" -CheckOnly

# Type checking
Write-Host "`n[3/9] Type checking..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/typecheck.ps1"

# Tests
Write-Host "`n[4/9] Running tests..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/test.ps1"

# Coverage
Write-Host "`n[5/9] Running coverage..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/coverage.ps1"

# Docs
Write-Host "`n[6/9] Building documentation..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/docs.ps1"

# API docs
Write-Host "`n[7/9] Generating API docs..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/generate-api-docs.ps1"

# Packaging
Write-Host "`n[8/9] Building package..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/build.ps1"

# Release dry-run
Write-Host "`n[9/9] Release dry-run..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/release-test.ps1" -DryRun
pwsh "$PSScriptRoot/release.ps1" -DryRun

Write-Host "`nFull CI pipeline complete." -ForegroundColor Green
