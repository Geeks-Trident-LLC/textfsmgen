Write-Host "Running mypy type checking..." -ForegroundColor Cyan

if (-not (Get-Command mypy -ErrorAction SilentlyContinue)) {
    Write-Host "mypy is not installed." -ForegroundColor Red
    exit 1
}

mypy textfsmgen

Write-Host "Type checking complete." -ForegroundColor Green
