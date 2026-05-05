Write-Host "=== Running full project verification (ALL CHECKS) ===" -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent

# 1. Lint
Write-Host "`n[1/8] Linting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/lint.ps1"

# 2. Format check
Write-Host "`n[2/8] Checking formatting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/format.ps1" -CheckOnly

# 3. Type checking
Write-Host "`n[3/8] Type checking..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/typecheck.ps1"

# 4. Tests
Write-Host "`n[4/8] Running tests..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/test.ps1"

# 5. Coverage
Write-Host "`n[5/8] Running coverage..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/coverage.ps1"

# 6. Docs build
Write-Host "`n[6/8] Building documentation..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/docs.ps1"

# 7. Build package
Write-Host "`n[7/8] Building package..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/build.ps1"

# 8. Release dry-run (TestPyPI + PyPI)
Write-Host "`n[8/8] Release dry-run (TestPyPI + PyPI)..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/release-test.ps1" -DryRun
pwsh "$PSScriptRoot/release.ps1" -DryRun

Write-Host "`nAll verification steps completed successfully." -ForegroundColor Green
