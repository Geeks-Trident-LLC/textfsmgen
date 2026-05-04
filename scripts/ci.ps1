Write-Host "=== CI Pipeline Start ===" -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent

# Lint
Write-Host "Running lint..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/lint.ps1"

# Format check
Write-Host "Checking formatting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/format.ps1" -CheckOnly

# Tests
Write-Host "Running tests..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/test.ps1"

# Build
Write-Host "Building package..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/build.ps1"

# Docs (optional)
if (Test-Path "$root/mkdocs.yml" -or Test-Path "$root/docs/conf.py") {
    Write-Host "Building documentation..." -ForegroundColor Cyan
    pwsh "$PSScriptRoot/docs.ps1"
}

Write-Host "=== CI Pipeline Complete ===" -ForegroundColor Green
