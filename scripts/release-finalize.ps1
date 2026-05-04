param(
    [Parameter(Mandatory=$true)]
    [string]$Tag,

    [string[]]$Artifacts
)

Write-Host "Finalizing GitHub Release..." -ForegroundColor Cyan

# Ensure GitHub CLI exists
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI (gh) is not installed." -ForegroundColor Red
    exit 1
}

Write-Host "Publishing release for tag: $Tag" -ForegroundColor Green

# Publish the draft release
gh release edit $Tag --draft=false

# Upload artifacts if provided
if ($Artifacts) {
    foreach ($artifact in $Artifacts) {
        if (Test-Path $artifact) {
            Write-Host "Uploading artifact: $artifact" -ForegroundColor Cyan
            gh release upload $Tag $artifact --clobber
        }
        else {
            Write-Host "Artifact not found: $artifact" -ForegroundColor Yellow
        }
    }
}

Write-Host "Release finalized and published." -ForegroundColor Green
