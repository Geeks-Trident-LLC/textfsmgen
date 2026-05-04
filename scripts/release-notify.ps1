param(
    [string]$Tag,
    [string]$Message = "A new release is available.",
    [string]$SlackWebhook,
    [string]$TeamsWebhook
)

Write-Host "Sending release notification..." -ForegroundColor Cyan

# Determine tag if not provided
if (-not $Tag) {
    $Tag = git describe --tags --abbrev=0 2>$null
    if (-not $Tag) {
        Write-Host "No tag found. Provide one with -Tag." -ForegroundColor Red
        exit 1
    }
}

$payload = @{
    text = "$Message`nRelease: $Tag"
} | ConvertTo-Json

# Slack
if ($SlackWebhook) {
    Write-Host "Posting to Slack..." -ForegroundColor Cyan
    Invoke-RestMethod -Uri $SlackWebhook -Method Post -Body $payload -ContentType "application/json"
}

# Teams
if ($TeamsWebhook) {
    Write-Host "Posting to Teams..." -ForegroundColor Cyan
    Invoke-RestMethod -Uri $TeamsWebhook -Method Post -Body $payload -ContentType "application/json"
}

Write-Host "Release notification sent." -ForegroundColor Green
