Write-Host "=== Setting up development environment ===" -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent
$venv = "$root/.venv"

# Create venv
if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $venv
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
$activate = "$venv/Scripts/Activate.ps1"
. $activate

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
    Write-Host "Installing pre-commit hooks..." -ForegroundColor Cyan
    pre-commit install
}

Write-Host "Development environment ready." -ForegroundColor Green
Write-Host "To activate the environment later:" -ForegroundColor Yellow
Write-Host "    . .venv/Scripts/Activate.ps1"
