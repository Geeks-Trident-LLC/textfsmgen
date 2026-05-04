Write-Host "=== CI Docs Pipeline ===" -ForegroundColor Cyan

# Validate mkdocs config
Write-Host "Validating mkdocs configuration..." -ForegroundColor Cyan
mkdocs build --strict

# Generate API docs
Write-Host "Generating API docs..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/generate-api-docs.ps1"

# Build docs
Write-Host "Building documentation..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/docs.ps1"

Write-Host "Docs CI pipeline complete." -ForegroundColor Green
