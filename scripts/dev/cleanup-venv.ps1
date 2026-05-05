Write-Host "Cleaning up virtual environment..." -ForegroundColor Cyan

$venv = ".venv"

if (Test-Path $venv) {
    Remove-Item $venv -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Virtual environment removed." -ForegroundColor Green
}
else {
    Write-Host "No virtual environment found." -ForegroundColor Yellow
}
