import os
import pytest
from unittest.mock import patch, MagicMock

from textfsmgen.libs.shell import execute_command, CommandResult


def make_proc(stdout="", stderr="", returncode=0):
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


# -------------------------------------------------------------------
# Non‑Windows behavior
# -------------------------------------------------------------------

@patch("os.name", "posix")
@patch("subprocess.run")
def test_non_windows_shell(mock_run):
    mock_run.return_value = make_proc("ok", "", 0)

    result = execute_command("echo hi")

    assert result.is_success
    assert result.output == "ok"
    mock_run.assert_called_once()


# -------------------------------------------------------------------
# Windows: cmd.exe success
# -------------------------------------------------------------------

@patch("os.name", "nt")
@patch("subprocess.run")
def test_windows_cmd_success(mock_run):
    mock_run.return_value = make_proc("cmd-ok", "", 0)

    result = execute_command("dir")

    assert result.is_success
    assert result.output == "cmd-ok"


# -------------------------------------------------------------------
# Windows: cmd.exe fails, direct exec succeeds
# -------------------------------------------------------------------

@patch("os.name", "nt")
def test_windows_direct_exec_success():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            make_proc("", "err", 1),  # shell=True fails
            make_proc("direct-ok", "", 0),  # direct exec succeeds
        ]

        result = execute_command("tool --version")

        assert result.is_success
        assert result.output == "direct-ok"


# -------------------------------------------------------------------
# Windows: PowerShell fallback
# -------------------------------------------------------------------

@patch("os.name", "nt")
def test_windows_powershell_fallback():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            make_proc("", "err", 1),  # shell=True fails
            make_proc("", "err", 1),  # direct exec fails
            make_proc("ps-ok", "", 0),  # powershell succeeds
        ]

        result = execute_command("echo hi")

        assert result.is_success
        assert result.output == "ps-ok"


# -------------------------------------------------------------------
# Windows: explicit powershell should NOT be wrapped again
# -------------------------------------------------------------------

@patch("os.name", "nt")
def test_explicit_powershell_not_wrapped():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            make_proc("", "err", 1),  # shell=True fails
            make_proc("", "err", 1),  # direct exec fails
        ]

        result = execute_command("powershell echo hi")

        assert not result.is_success
        assert mock_run.call_count == 2  # no fallback wrap
