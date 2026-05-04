$root = Split-Path $PSScriptRoot -Parent

Write-Host "Building documentation..." -ForegroundColor Cyan

if (Test-Path "$root/mkdocs.yml") {
    if (-not (Get-Command mkdocs -ErrorAction SilentlyContinue)) {
        Write-Host "mkdocs not installed." -ForegroundColor Red
        exit 1
    }
    mkdocs build
}
elseif (Test-Path "$root/docs/conf.py") {
    if (-not (Get-Command sphinx-build -ErrorAction SilentlyContinue)) {
        Write-Host "sphinx-build not installed." -ForegroundColor Red
        exit 1
    }
    sphinx-build docs docs/_build
}
else {
    Write-Host "No documentation configuration found." -ForegroundColor Yellow
    exit 0
}

Write-Host "Documentation build complete." -ForegroundColor Green
