param(
    [switch]$Fix
)

$root = Split-Path $PSScriptRoot -Parent

Write-Host "Linting Python code..." -ForegroundColor Cyan

if ($Fix) {
    ruff check $root --fix
}
else {
    ruff check $root
}

# Optional: mypy if installed
if (Get-Command mypy -ErrorAction SilentlyContinue) {
    Write-Host "Running mypy..." -ForegroundColor Cyan
    mypy $root
}

Write-Host "Linting complete." -ForegroundColor Green
