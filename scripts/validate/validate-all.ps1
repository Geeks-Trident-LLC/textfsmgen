Write-Host "=== Running full validation suite ===" -ForegroundColor Cyan

# 1. Lint
Write-Host "`n[1/8] Linting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/lint.ps1"

# 2. Format check
Write-Host "`n[2/8] Checking formatting..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/format.ps1" -CheckOnly

# 3. Type checking
Write-Host "`n[3/8] Type checking..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/typecheck.ps1"

# 4. Template validation (all .textfsm files)
Write-Host "`n[4/8] Validating TextFSM templates..." -ForegroundColor Cyan
Get-ChildItem -Recurse -Filter *.textfsm | ForEach-Object {
    pwsh "$PSScriptRoot/validate-template.ps1" -Template $_.FullName
}

# 5. Tests
Write-Host "`n[5/8] Running tests..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/test.ps1"

# 6. Coverage
Write-Host "`n[6/8] Running coverage..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/coverage.ps1"

# 7. Docs build
Write-Host "`n[7/8] Building documentation..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/docs.ps1"

# 8. Packaging
Write-Host "`n[8/8] Building package..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/build.ps1"

Write-Host "`nFull validation suite completed successfully." -ForegroundColor Green
