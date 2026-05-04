
# 🧪 Tests Overview

This directory contains tests for textfsmgen.

We use **pytest** for running tests and **PowerShell scripts** to orchestrate common workflows.

---

## ▶ Running Tests

From the project root:

```powershell
pwsh scripts/test.ps1
```

Or directly with pytest:

```bash
pytest
```

---

## 📁 Structure

- `tests/unit/` — Unit tests for small, focused pieces of logic
- `tests/integration/` — End-to-end and workflow tests
- `tests/data/` — Sample inputs, outputs, and templates used by tests

(If these folders don’t exist yet, they are recommended.)

---

## 🧩 Adding New Tests

1. Place unit tests in `tests/unit/` with names like `test_<module>.py`.
2. Place integration tests in `tests/integration/` with names like `test_<feature>_integration.py`.
3. Use `tests/data/` for fixtures (CLI output, templates, JSON expectations).
4. Run:

```powershell
pwsh scripts/test.ps1
```

before opening a PR.

---

## ✅ Conventions

- Use **pytest** style tests (functions, fixtures).
- Prefer **small, focused tests** over large, brittle ones.
- For new features, add:
  - at least one unit test
  - at least one integration test (if applicable)


---

### pwsh/powershell auto-detect script — `scripts/run-tool.ps1`

```powershell
<#
.SYNOPSIS
  Run a project script using pwsh if available, otherwise powershell.

.EXAMPLE
  ./scripts/run-tool.ps1 scripts/test.ps1
#>

param(
    [Parameter(Mandatory = $true)]
    [string] $ScriptPath,

    [string[]] $Arguments
)

function Get-PowerShellCommand {
    if (Get-Command pwsh -ErrorAction SilentlyContinue) {
        return "pwsh"
    }

    if (Get-Command powershell -ErrorAction SilentlyContinue) {
        return "powershell"
    }

    throw "Neither 'pwsh' nor 'powershell' is available on PATH."
}

$psCmd = Get-PowerShellCommand

& $psCmd $ScriptPath @Arguments
$exitCode = $LASTEXITCODE

exit $exitCode
```

Usage:

```powershell
./scripts/run-tool.ps1 scripts/test.ps1
```

---

### Integration test templates

`tests/integration/test_cli_integration.py`:

```python
import subprocess
import sys
from pathlib import Path


def run_cli(*args: str) -> subprocess.CompletedProcess:
    root = Path(__file__).resolve().parents[2]
    cmd = [sys.executable, "-m", "textfsmgen", *args]
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True)


def test_cli_help_succeeds() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert "Usage" in result.stdout or "usage" in result.stdout


def test_cli_parses_sample_file(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    sample_input = root / "tests" / "data" / "sample.txt"
    template = root / "tests" / "data" / "sample.textfsm"

    result = run_cli("parse", "--template", str(template), "--input", str(sample_input))
    assert result.returncode == 0
    assert result.stdout.strip() != ""
```

`tests/integration/test_api_integration.py`:


---