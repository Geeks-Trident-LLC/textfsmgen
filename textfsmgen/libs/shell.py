"""
textfsmgen.libs.shell
=====================

General-purpose shell (CLI interaction) functions used across TextFSMGen.
"""     # noqa

from typing import Optional

import subprocess
import re

from . import ECODE
from .generic import DotObject
from .decorators import try_and_catch


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


@try_and_catch()
def execute_command(cmdline: str) -> DotObject:
    """
    Run a shell command and return its result.

    Parameters
    ----------
    cmdline : str
        Command line string to execute.

    Returns
    -------
    DotObject
        Object with:
        - output (str): Captured stdout/stderr.
        - exit_code (int): The exit status code returned by the shell.
        - is_success (bool): True if exit_code == ECODE.SUCCESS.
    """
    exit_code, output = subprocess.getstatusoutput(cmdline)
    return DotObject(
        output=output,
        exit_code=exit_code,
        is_success=exit_code == ECODE.SUCCESS,
    )
