Write-Host "Running coverage..." -ForegroundColor Cyan

$cmd = "pytest --cov=textfsmgen --cov-report=term-missing --cov-report=html"

Invoke-Expression $cmd

Write-Host "Coverage complete." -ForegroundColor Green
Write-Host "HTML report available at: htmlcov/index.html" -ForegroundColor Yellow
