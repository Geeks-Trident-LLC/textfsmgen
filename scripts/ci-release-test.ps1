param(
    [switch]$DryRun
)

Write-Host "=== CI TestPyPI Release Pipeline ===" -ForegroundColor Cyan

# Build package
Write-Host "Building package..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/build.ps1"

# Release to TestPyPI
Write-Host "Releasing to TestPyPI..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/release-test.ps1" -DryRun:$DryRun

Write-Host "TestPyPI release pipeline complete." -ForegroundColor Green
