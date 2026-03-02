"""
textfsmgen.libs
===============

General-purpose functions used across TextFSMGen.
"""

from enum import IntFlag

from .pat import PATTERN


class ECODE(IntFlag):
    """Standardized process exit codes with success/failure aliases."""
    SUCCESS = 0
    BAD = 1
    PASSED = SUCCESS
    FAILED = BAD


__all__ = [
    'ECODE',
    'PATTERN',
]