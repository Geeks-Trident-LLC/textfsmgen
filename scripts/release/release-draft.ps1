param(
    [string]$Tag,
    [string]$NotesFile = "RELEASE_NOTES.md"
)

Write-Host "Creating GitHub Release draft..." -ForegroundColor Cyan

# Ensure GitHub CLI exists
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI (gh) is not installed." -ForegroundColor Red
    exit 1
}

# Determine tag if not provided
if (-not $Tag) {
    $Tag = git describe --tags --abbrev=0 2>$null
    if (-not $Tag) {
        Write-Host "No tag found. Provide one with -Tag." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Using tag: $Tag" -ForegroundColor Green

# Generate release notes
pwsh "$PSScriptRoot/generate-release-notes.ps1" -Output $NotesFile

# Create draft release
gh release create $Tag `
    --draft `
    --notes-file $NotesFile `
    --title "Release $Tag"

Write-Host "Draft release created for tag $Tag" -ForegroundColor Green
