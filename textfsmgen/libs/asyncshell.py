import os
import shlex
import asyncio
from dataclasses import dataclass


@dataclass
class CommandResult:
    output: str
    exit_code: int

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0


# -------------------------------------------------------------------
# Public async API
# -------------------------------------------------------------------


async def execute_command_async(cmdline: str) -> CommandResult:
    if os.name != "nt":
        return await _run_shell_async(cmdline)

    # Windows: try cmd.exe first
    result = await _run_shell_async(cmdline)
    if result.is_success:
        return result

    # Try direct exec
    result = await _run_direct_async(cmdline)
    if result.is_success:
        return result

    # If user explicitly invoked powershell/pwsh, do NOT wrap again
    if _is_explicit_powershell(cmdline):
        return result

    # Final fallback: wrap in powershell or pwsh
    return await _run_powershell_async(cmdline)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


async def _run_shell_async(cmdline: str) -> CommandResult:
    return await _run_subprocess_async(
        cmdline,
        use_shell=True,
    )


async def _run_direct_async(cmdline: str) -> CommandResult:
    try:
        return await _run_subprocess_async(
            shlex.split(cmdline),
            use_shell=False,
        )
    except Exception:
        return CommandResult("", 1)


async def _run_powershell_async(cmdline: str) -> CommandResult:
    for ps in ("powershell", "pwsh"):
        wrapped = f"{ps} -command {shlex.quote(cmdline)}"
        try:
            return await _run_subprocess_async(
                shlex.split(wrapped),
                use_shell=False,
            )
        except Exception:
            continue
    return CommandResult("", 1)


def _is_explicit_powershell(cmdline: str) -> bool:
    lowered = cmdline.lower().lstrip()
    return lowered.startswith("powershell ") or lowered.startswith("pwsh ")


async def _run_subprocess_async(command, *, use_shell: bool) -> CommandResult:
    proc = await asyncio.create_subprocess_shell(
        command if use_shell else " ".join(command),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=use_shell,
    )

    stdout, stderr = await proc.communicate()
    output = (stdout or b"").decode() + (stderr or b"").decode()

    return CommandResult(output, proc.returncode)
