param(
    [ValidateSet("patch", "minor", "major")]
    [string]$Bump = "patch",

    [switch]$DryRun
)

$root = Split-Path $PSScriptRoot -Parent

Write-Host "=== Python Package Release Tool ===" -ForegroundColor Cyan
Write-Host "Bump type: $Bump"
if ($DryRun) { Write-Host "Dry-run mode enabled." -ForegroundColor Yellow }

# --- Validate tools ---
$required = @("python", "pip", "twine", "bump2version")
foreach ($tool in $required) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Host "Missing required tool: $tool" -ForegroundColor Red
        exit 1
    }
}

# --- Version bump ---
if ($DryRun) {
    Write-Host "[DRY] Would bump version: $Bump"
}
else {
    Write-Host "Bumping version ($Bump)..." -ForegroundColor Cyan
    bump2version $Bump
}

# --- Build package ---
Write-Host "Building package..." -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "[DRY] Would run: python -m build"
}
else {
    python -m build
}

# --- Upload to PyPI ---
Write-Host "Uploading to PyPI..." -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "[DRY] Would run: twine upload dist/*"
}
else {
    twine upload dist/*
}

Write-Host "Release complete." -ForegroundColor Green
