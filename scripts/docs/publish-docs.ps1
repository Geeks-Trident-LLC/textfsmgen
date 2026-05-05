Write-Host "Publishing documentation to GitHub Pages..." -ForegroundColor Cyan

if (-not (Get-Command mkdocs -ErrorAction SilentlyContinue)) {
    Write-Host "mkdocs is not installed." -ForegroundColor Red
    exit 1
}

mkdocs gh-deploy --clean

Write-Host "Documentation published." -ForegroundColor Green
