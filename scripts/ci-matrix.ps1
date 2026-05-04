param(
    [string[]]$Versions = @("3.10", "3.11", "3.12"),
    [string]$Output = ".github/workflows/ci-matrix.yml"
)

Write-Host "Generating multi-Python CI workflow..." -ForegroundColor Cyan

$yaml = @"
name: CI (Matrix)

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [$(($Versions -join ", "))]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: \${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run CI pipeline
        shell: pwsh
        run: pwsh scripts/ci.ps1
"@

$yaml | Out-File -Encoding utf8 $Output

Write-Host "Matrix CI workflow written to $Output" -ForegroundColor Green
