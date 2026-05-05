param(
    [Parameter(Mandatory=$true)]
    [string]$Module,

    [string]$Output = "profile.stats"
)

Write-Host "Profiling Python module: $Module" -ForegroundColor Cyan

python -m cProfile -o $Output $Module

Write-Host "Profile written to $Output" -ForegroundColor Green
Write-Host "To view results:" -ForegroundColor Yellow
Write-Host "    python -m pstats $Output"
