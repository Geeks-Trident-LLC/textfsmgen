param(
    [switch]$CheckOnly
)

$root = Split-Path $PSScriptRoot -Parent

Write-Host "Formatting Python code..." -ForegroundColor Cyan

if ($CheckOnly) {
    ruff check $root
    black --check $root
}
else {
    ruff check $root --fix
    black $root
}

Write-Host "Formatting complete." -ForegroundColor Green
