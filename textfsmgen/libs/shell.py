# textfsmgen/libs/shell.py

import platform

import os
import shlex
import subprocess
import asyncio
from dataclasses import dataclass


@dataclass
class CommandResult:
    output: str
    exit_code: int

    @property
    def is_success(self):
        return self.exit_code == 0


async def execute_command_async(cmdline: str) -> CommandResult:
    proc = await asyncio.create_subprocess_shell(
        cmdline,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()
    output = (stdout or b"").decode() + (stderr or b"").decode()

    return CommandResult(output, proc.returncode)


def execute_command(cmdline: str) -> CommandResult:
    if os.name != "nt":
        return _run_shell(cmdline)

    # Windows: try cmd.exe first
    result = _run_shell(cmdline)
    if result.is_success:
        return result

    # Try direct exec (no shell)
    result = _run_direct(cmdline)
    if result.is_success:
        return result

    # If user already invoked PowerShell/pwsh, do not wrap again
    if _is_explicit_powershell(cmdline):
        return result  # propagate failure

    # Final fallback: wrap in PowerShell or pwsh
    return _run_powershell(cmdline)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _run_shell(cmdline: str) -> CommandResult:
    proc = subprocess.run(
        cmdline,
        shell=True,
        capture_output=True,
        text=True,
    )
    return CommandResult(proc.stdout + proc.stderr, proc.returncode)


def _run_direct(cmdline: str) -> CommandResult:
    try:
        proc = subprocess.run(
            shlex.split(cmdline),
            shell=False,
            capture_output=True,
            text=True,
        )
        return CommandResult(proc.stdout + proc.stderr, proc.returncode)
    except Exception:   # noqa
        return CommandResult("", 1)


def _is_explicit_powershell(cmdline: str) -> bool:
    lowered = cmdline.lower().lstrip()
    return lowered.startswith("powershell ") or lowered.startswith("pwsh ")


def _run_powershell(cmdline: str) -> CommandResult:
    for ps in ("powershell", "pwsh"):
        try:
            wrapped = f"{ps} -command {shlex.quote(cmdline)}"
            proc = subprocess.run(
                shlex.split(wrapped),
                shell=False,
                capture_output=True,
                text=True,
            )
            return CommandResult(proc.stdout + proc.stderr, proc.returncode)
        except Exception:   # noqa
            continue
    return CommandResult("", 1)


def is_macos_dark_mode() -> bool:
    """Return True if macOS is currently using Dark Mode."""
    if platform.system() != "Darwin":
        return False

    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() == "Dark"
    except Exception:  # noqa
        return False  # key doesn't exist → Light Mode
