param(
    [string]$Output = "CHANGELOG.md"
)

Write-Host "Generating changelog..." -ForegroundColor Cyan

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

# Write changelog
"## Changelog (`$(Get-Date -Format yyyy-MM-dd)`)`n" | Out-File $Output
$commits | Out-File $Output -Append

Write-Host "Changelog written to $Output" -ForegroundColor Green
