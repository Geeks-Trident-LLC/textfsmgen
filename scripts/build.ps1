Write-Host "Building Python package..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found." -ForegroundColor Red
    exit 1
}

python -m build

Write-Host "Build complete." -ForegroundColor Green
