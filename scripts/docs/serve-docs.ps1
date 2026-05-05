Write-Host "Starting MkDocs live server..." -ForegroundColor Cyan

if (-not (Get-Command mkdocs -ErrorAction SilentlyContinue)) {
    Write-Host "mkdocs is not installed." -ForegroundColor Red
    exit 1
}

mkdocs serve --dev-addr=127.0.0.1:8000
