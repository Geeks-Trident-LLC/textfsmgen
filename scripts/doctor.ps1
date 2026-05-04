Write-Host "=== Environment Diagnostics (doctor) ===" -ForegroundColor Cyan

$tools = @(
    "python",
    "pip",
    "ruff",
    "black",
    "mypy",
    "pytest",
    "mkdocs",
    "sphinx-build",
    "twine",
    "build",
    "git"
)

foreach ($tool in $tools) {
    if (Get-Command $tool -ErrorAction SilentlyContinue) {
        Write-Host "[OK]   $tool" -ForegroundColor Green
    }
    else {
        Write-Host "[MISS] $tool" -ForegroundColor Red
    }
}

Write-Host "`nPowerShell version:" -ForegroundColor Cyan
$PSVersionTable.PSVersion

Write-Host "`nPython version:" -ForegroundColor Cyan
python --version

Write-Host "`nPip version:" -ForegroundColor Cyan
pip --version

Write-Host "`nDoctor check complete." -ForegroundColor Green
