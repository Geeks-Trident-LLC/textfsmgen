Write-Host "=== Bootstrapping full development environment ===" -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent
$venv = "$root/.venv"

# 1. Create venv
if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $venv
}

# 2. Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
. "$venv/Scripts/Activate.ps1"

# 3. Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks
if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
    Write-Host "Installing pre-commit hooks..." -ForegroundColor Cyan
    pre-commit install
}

# 5. Build docs
Write-Host "Building documentation..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/docs.ps1"

# 6. Generate API docs
Write-Host "Generating API documentation..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/generate-api-docs.ps1"

# 7. Run full verification suite
Write-Host "Running full verification suite..." -ForegroundColor Cyan
pwsh "$PSScriptRoot/verify-all.ps1"

Write-Host "`nBootstrap complete. Development environment is fully ready." -ForegroundColor Green
Write-Host "To activate the environment later:" -ForegroundColor Yellow
Write-Host "    . .venv/Scripts/Activate.ps1"
