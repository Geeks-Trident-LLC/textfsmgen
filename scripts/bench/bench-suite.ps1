param(
    [Parameter(Mandatory=$true)]
    [string[]]$Targets,

    [int]$Repeat = 5
)

Write-Host "=== Benchmark Suite ===" -ForegroundColor Cyan

foreach ($target in $Targets) {
    Write-Host "`nBenchmarking: $target" -ForegroundColor Yellow

$cmd = @"
import timeit
print(timeit.timeit("$target", number=$Repeat))
"@

    python - <<EOF
$cmd
EOF
}

Write-Host "`nBenchmark suite complete." -ForegroundColor Green
