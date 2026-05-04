"""
textfsmgen.libs
===============

General-purpose functions used across TextFSMGen.
"""  # noqa

import platform
from enum import IntFlag

from .pattern import PATTERN

_system = platform.system()
is_macos = _system == "Darwin"
is_linux = _system == "Linux"
is_windows = _system == "Windows"


class ECODE(IntFlag):
    """Standardized process exit codes with success/failure aliases."""

    SUCCESS = 0
    BAD = 1
    PASSED = SUCCESS
    FAILED = BAD


__all__ = [
    "ECODE",
    "PATTERN",
    "is_macos",
    "is_linux",
    "is_windows",
]
