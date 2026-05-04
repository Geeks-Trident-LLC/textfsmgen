param(
    [Parameter(Mandatory=$true)]
    [string]$Template
)

if (-not (Test-Path $Template)) {
    Write-Host "Template not found: $Template" -ForegroundColor Red
    exit 1
}

Write-Host "Validating TextFSM template: $Template" -ForegroundColor Cyan

$cmd = @"
import sys
from textfsm import TextFSM

try:
    with open("$Template") as f:
        TextFSM(f)
    print("VALID")
except Exception as e:
    print("INVALID:", e)
    sys.exit(1)
"@

python - <<EOF
$cmd
EOF
