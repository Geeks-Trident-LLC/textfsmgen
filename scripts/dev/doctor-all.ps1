Write-Host "=== Running full environment diagnostics ===" -ForegroundColor Cyan

# Load doctor module
Import-Module "$PSScriptRoot/doctor.psd1" -Force

Write-Host "`n[1/3] Checking environment tools..." -ForegroundColor Cyan
Test-DevEnvironment

Write-Host "`n[2/3] Syncing project version..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/sync-version.ps1"

Write-Host "`n[3/3] Checking for outdated dependencies..." -ForegroundColor Cyan
pip list --outdated

Write-Host "`nEnvironment diagnostics complete." -ForegroundColor Green
