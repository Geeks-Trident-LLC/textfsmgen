param(
    [string]$Output = "RELEASE_NOTES.md"
)

Write-Host "Generating release notes..." -ForegroundColor Cyan

# Get last tag
$lastTag = git describe --tags --abbrev=0 2>$null

if (-not $lastTag) {
    Write-Host "No tags found. Using full commit history." -ForegroundColor Yellow
    $commits = git log --pretty=format:"- %s"
}
else {
    Write-Host "Last tag: $lastTag" -ForegroundColor Cyan
    $commits = git log $lastTag..HEAD --pretty=format:"- %s"
}

# Write release notes
"## Release Notes (`$(Get-Date -Format yyyy-MM-dd)`)`n" | Out-File $Output
$commits | Out-File $Output -Append

Write-Host "Release notes written to $Output" -ForegroundColor Green
