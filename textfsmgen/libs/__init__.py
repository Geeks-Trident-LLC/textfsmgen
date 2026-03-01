"""
textfsmgen.libs
===============

General-purpose functions used across TextFSMGen.
"""

import re
import string
from enum import IntFlag


class ECODE(IntFlag):
    """Standardized process exit codes with success/failure aliases."""
    SUCCESS = 0
    BAD = 1
    PASSED = SUCCESS
    FAILED = BAD


class PATTERN:      # noqa
    """Reusable regex fragments for common character classes."""

    punct=rf"[{re.escape(string.punctuation)}]"
    puncts = rf"{punct}+"