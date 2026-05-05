Write-Host "Syncing version across project..." -ForegroundColor Cyan

$pyproject = "pyproject.toml"

if (-not (Test-Path $pyproject)) {
    Write-Host "pyproject.toml not found." -ForegroundColor Red
    exit 1
}

# Extract version
$version = Select-String -Path $pyproject -Pattern '^version\s*=\s*"(.*)"' |
    ForEach-Object { $_.Matches[0].Groups[1].Value }

if (-not $version) {
    Write-Host "Version not found in pyproject.toml" -ForegroundColor Red
    exit 1
}

Write-Host "Detected version: $version" -ForegroundColor Green

# Update docs
$docs = @(
    "docs/index.md",
    "docs/usage.md",
    "docs/development.md"
)

foreach ($file in $docs) {
    if (Test-Path $file) {
        (Get-Content $file) `
            -replace 'Version:.*', "Version: $version" |
            Set-Content $file
        Write-Host "Updated $file" -ForegroundColor Cyan
    }
}

Write-Host "Version sync complete." -ForegroundColor Green
