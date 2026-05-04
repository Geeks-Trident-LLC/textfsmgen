param(
    [Parameter(Mandatory=$true)]
    [string]$Target,

    [switch]$Command
)

if ($Command) {
    Write-Host "Monitoring command output: $Target" -ForegroundColor Cyan
    while ($true) {
        Invoke-Expression $Target
        Start-Sleep -Seconds 1
        Clear-Host
    }
}
else {
    if (-not (Test-Path $Target)) {
        Write-Host "File not found: $Target" -ForegroundColor Red
        exit 1
    }

    Write-Host "Monitoring file: $Target" -ForegroundColor Cyan
    Get-Content $Target -Wait
}
