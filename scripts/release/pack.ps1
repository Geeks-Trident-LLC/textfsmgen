param(
    [string]$Output = "dist/package-bundle.zip"
)

Write-Host "Packing project into distributable artifact..." -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent

# Ensure dist exists
if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

# Clean + build
pwsh "$PSScriptRoot/clean.ps1"
pwsh "$PSScriptRoot/build.ps1"

# Create bundle
Write-Host "Creating bundle: $Output" -ForegroundColor Cyan

Compress-Archive `
    -Path @(
        "$root/textfsmgen",
        "$root/scripts",
        "$root/docs",
        "$root/pyproject.toml",
        "$root/README.md"
    ) `
    -DestinationPath $Output `
    -Force

Write-Host "Bundle created at $Output" -ForegroundColor Green
