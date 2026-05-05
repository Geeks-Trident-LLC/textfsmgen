Write-Host "Generating API documentation..." -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent
$apiDir = "$root/docs/api"

if (-not (Get-Command mkdocs -ErrorAction SilentlyContinue)) {
    Write-Host "mkdocs is not installed." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command mkdocs-gen-api -ErrorAction SilentlyContinue)) {
    Write-Host "mkdocs-gen-api is not installed." -ForegroundColor Red
    Write-Host "Install with: pip install mkdocs-gen-api" -ForegroundColor Yellow
    exit 1
}

# Clean old API docs
if (Test-Path $apiDir) {
    Remove-Item $apiDir -Recurse -Force
}

# Generate new API docs
mkdocs-gen-api textfsmgen --output-dir docs/api

Write-Host "API documentation generated in docs/api/" -ForegroundColor Green
