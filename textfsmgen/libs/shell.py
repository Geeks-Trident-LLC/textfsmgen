"""
textfsmgen.libs.shell
=====================

General-purpose shell (CLI interaction) functions used across TextFSMGen.
"""  # noqa

from typing import Optional

import subprocess
import re
import platform
import shlex


from . import ECODE
from .generic import DotObject


class PackageInfo:
    """Retrieve and store package info using pip."""

    def __init__(self, name: str):
        self.pkg = name.lower()
        self._installed: bool = False
        self._version: str = ""
        self._name: str = ""
        self._pip_freeze_result: Optional[DotObject] = None
        self._pip_show_result: Optional[DotObject] = None
        self._process()

    @property
    def is_installed(self) -> bool:
        """Return True if the package is installed."""
        return self._installed

    @property
    def version(self) -> str:
        """Return the detected package version."""
        return self._version

    @property
    def name(self) -> str:
        """Return the package name."""
        return self._name

    @property
    def freeze_out(self) -> str:
        """Return raw output from `pip freeze`."""
        if isinstance(self._pip_freeze_result, DotObject):
            return self._pip_freeze_result.output
        return ""

    @property
    def show_out(self) -> str:
        """Return raw output from `pip show`."""
        if isinstance(self._pip_show_result, DotObject):
            return self._pip_show_result.output
        return ""

    def _process(self) -> None:
        """Populate package info using `pip freeze` and `pip show`."""
        self._pip_freeze_result = execute_command("pip freeze")

        pat_freeze = rf"(?i)(?P<name>{self.pkg}) *(?P<sep>==|@) *(?P<version>.+)\s*$"
        for line in self.freeze_out.splitlines():
            m = re.match(pat_freeze, line)
            if m:
                self._name = m.group("name")
                self._installed = True
                self._version = m.group("version") if m.group("sep") == "==" else ""
                break

        if self.is_installed and not self._version:
            self._pip_show_result = execute_command(f"pip show {self.pkg}")
            pat_show = r"(?i)^version:\s+(?P<version>.+)\s*$"
            m = re.search(pat_show, self.show_out, flags=re.M)
            if m:
                self._version = m.group("version")


def execute_command(cmdline: str) -> DotObject:
    """
    Run a shell command in the most natural way possible.
    Automatically detects PowerShell pipelines and reruns them safely.
    """

    is_windows = platform.system() == "Windows"

    # ------------------------------------------------------------
    # 1. Try running normally (cmd.exe or bash/zsh)
    # ------------------------------------------------------------
    proc = subprocess.run(cmdline, shell=True, capture_output=True, text=True)

    if proc.returncode == ECODE.SUCCESS or not is_windows:
        return DotObject(
            output=(proc.stdout or "") + (proc.stderr or ""),
            exit_code=proc.returncode,
            is_success=proc.returncode == ECODE.SUCCESS,
        )

    # ------------------------------------------------------------
    # 2. If on Windows and command looks like PowerShell syntax,
    #    run it through PowerShell safely.
    # ------------------------------------------------------------
    if _looks_like_powershell(cmdline):
        return _run_powershell_block(cmdline)

    # ------------------------------------------------------------
    # 3. If user explicitly typed "powershell ..." or "pwsh ...",
    #    run it directly with shell=False.
    # ------------------------------------------------------------
    if cmdline.strip().lower().startswith(("powershell ", "pwsh ")):
        return _run_explicit_powershell(cmdline)

    # ------------------------------------------------------------
    # 4. Fallback: return the failed result
    # ------------------------------------------------------------
    return DotObject(
        output=(proc.stdout or "") + (proc.stderr or ""),
        exit_code=proc.returncode,
        is_success=False,
    )


def _looks_like_powershell(cmd: str) -> bool:
    """Heuristics to detect PowerShell pipelines."""
    ps_keywords = [
        "|",
        "select-object",
        "where-object",
        "format-",
        "get-",
        "set-",
        "new-",
        "remove-",
        "& {",
        ";",
    ]
    cmd_lower = cmd.lower()
    return any(k in cmd_lower for k in ps_keywords)


def _run_powershell_block(command: str) -> DotObject:
    """Run a PowerShell pipeline using a script block."""
    ps_command = f"& {{ {command} }}"
    for ps in ("powershell", "pwsh"):
        proc = subprocess.run(
            [ps, "-command", ps_command], shell=False, capture_output=True, text=True
        )
        if proc.returncode == ECODE.SUCCESS:
            return DotObject(
                output=(proc.stdout or "") + (proc.stderr or ""),
                exit_code=proc.returncode,
                is_success=True,
            )
    return DotObject(
        output=(proc.stdout or "") + (proc.stderr or ""),
        exit_code=proc.returncode,
        is_success=False,
    )


def _run_explicit_powershell(cmdline: str) -> DotObject:
    """Run commands that already start with powershell/pwsh."""
    parts = shlex.split(cmdline)
    proc = subprocess.run(parts, shell=False, capture_output=True, text=True)
    return DotObject(
        output=(proc.stdout or "") + (proc.stderr or ""),
        exit_code=proc.returncode,
        is_success=proc.returncode == ECODE.SUCCESS,
    )


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
