param(
    [string]$Output = "dist/release-bundle.zip"
)

Write-Host "Packing release artifact..." -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent

# Ensure dist exists
if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

# Build package
pwsh "$PSScriptRoot/build.ps1"

# Generate release notes
pwsh "$PSScriptRoot/generate-release-notes.ps1"

# Build docs
pwsh "$PSScriptRoot/docs.ps1"

# Generate API docs
pwsh "$PSScriptRoot/generate-api-docs.ps1"

# Create bundle
Write-Host "Creating release bundle: $Output" -ForegroundColor Cyan

Compress-Archive `
    -Path @(
        "$root/dist",
        "$root/docs",
        "$root/RELEASE_NOTES.md",
        "$root/CHANGELOG.md",
        "$root/pyproject.toml",
        "$root/README.md"
    ) `
    -DestinationPath $Output `
    -Force

Write-Host "Release bundle created at $Output" -ForegroundColor Green
