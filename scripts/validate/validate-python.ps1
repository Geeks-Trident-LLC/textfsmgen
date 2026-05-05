Write-Host "=== Validating Python code ===" -ForegroundColor Cyan

# 1. Ruff (imports, unused code, complexity, style)
Write-Host "`n[1/3] Running ruff..." -ForegroundColor Cyan
ruff check .

# 2. mypy (type checking)
Write-Host "`n[2/3] Running mypy..." -ForegroundColor Cyan
mypy textfsmgen

# 3. Optional: pyflakes (extra import checks)
if (Get-Command pyflakes -ErrorAction SilentlyContinue) {
    Write-Host "`n[3/3] Running pyflakes..." -ForegroundColor Cyan
    pyflakes textfsmgen
}
else {
    Write-Host "`n[3/3] pyflakes not installed (skipping)" -ForegroundColor Yellow
}

Write-Host "`nPython validation complete." -ForegroundColor Green
