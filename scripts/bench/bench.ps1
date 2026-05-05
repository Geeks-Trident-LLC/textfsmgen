param(
    [Parameter(Mandatory=$true)]
    [string]$Target,

    [int]$Repeat = 5
)

Write-Host "Benchmarking: $Target" -ForegroundColor Cyan

$cmd = @"
import timeit
print(timeit.timeit("$Target", number=$Repeat))
"@

python - <<EOF
$cmd
EOF

Write-Host "Benchmark complete." -ForegroundColor Green
