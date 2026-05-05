param(
    [switch]$Verbose
)

$root = Split-Path $PSScriptRoot -Parent

Write-Host "Running tests..." -ForegroundColor Cyan

$cmd = "pytest --maxfail=1 --disable-warnings --cov=textfsmgen --cov-report=term-missing"

if ($Verbose) {
    $cmd += " -vv"
}

Invoke-Expression $cmd

Write-Host "Tests complete." -ForegroundColor Green
