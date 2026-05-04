Write-Host "Serving API documentation with live reload..." -ForegroundColor Cyan

if (-not (Get-Command mkdocs -ErrorAction SilentlyContinue)) {
    Write-Host "mkdocs is not installed." -ForegroundColor Red
    exit 1
}

# Ensure API docs exist
if (-not (Test-Path "docs/api")) {
    Write-Host "API docs not found. Generating..." -ForegroundColor Yellow
    pwsh "$PSScriptRoot/generate-api-docs.ps1"
}

mkdocs serve --dev-addr=127.0.0.1:8001
