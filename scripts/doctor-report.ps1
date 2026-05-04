Write-Host "Generating environment diagnostic report..." -ForegroundColor Cyan

$report = [ordered]@{}

# Tools to check
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

$toolStatus = @{}
foreach ($tool in $tools) {
    $toolStatus[$tool] = [ordered]@{
        installed = [bool](Get-Command $tool -ErrorAction SilentlyContinue)
    }
}
$report.tools = $toolStatus

# Python version
$report.python_version = python --version 2>$null

# Pip version
$report.pip_version = pip --version 2>$null

# Outdated dependencies
$outdated = pip list --outdated --format=json 2>$null
$report.outdated_packages = if ($outdated) { $outdated | ConvertFrom-Json } else { @() }

# Version sync check
$pyproject = "pyproject.toml"
if (Test-Path $pyproject) {
    $version = Select-String -Path $pyproject -Pattern '^version\s*=\s*"(.*)"' |
        ForEach-Object { $_.Matches[0].Groups[1].Value }
    $report.project_version = $version
}

# Output JSON
$json = $report | ConvertTo-Json -Depth 5
$json | Out-File -Encoding utf8 "doctor-report.json"

Write-Host "Diagnostic report written to doctor-report.json" -ForegroundColor Green
