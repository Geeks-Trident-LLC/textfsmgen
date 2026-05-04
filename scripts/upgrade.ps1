param(
    [switch]$Freeze
)

Write-Host "=== Upgrading dependencies ===" -ForegroundColor Cyan

# Upgrade pip first
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Upgrade all installed packages
Write-Host "Upgrading installed packages..." -ForegroundColor Cyan
pip list --outdated --format=freeze | ForEach-Object {
    $pkg = $_.Split('==')[0]
    Write-Host "Upgrading $pkg..." -ForegroundColor Yellow
    pip install --upgrade $pkg
}

# Reinstall dev dependencies
if (Test-Path "requirements-dev.txt") {
    Write-Host "Reinstalling dev dependencies..." -ForegroundColor Cyan
    pip install -r requirements-dev.txt
}

# Optionally freeze updated requirements
if ($Freeze) {
    Write-Host "Freezing updated requirements..." -ForegroundColor Cyan
    pip freeze | Out-File -Encoding utf8 requirements.txt
}

Write-Host "Dependency upgrade complete." -ForegroundColor Green
