param(
    [switch]$DryRun
)

Write-Host "=== CI Release Pipeline ===" -ForegroundColor Cyan

# Build package
Write-Host "Building package..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/build.ps1"

# Release to TestPyPI
Write-Host "Releasing to TestPyPI..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/release-test.ps1" -DryRun:$DryRun

# Release to PyPI
Write-Host "Releasing to PyPI..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/release.ps1" -DryRun:$DryRun

Write-Host "CI release pipeline complete." -ForegroundColor Green
