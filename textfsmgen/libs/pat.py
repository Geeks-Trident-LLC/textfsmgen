"""
textfsmgen.libs.common
======================

General-purpose Patter class and functions used across TextFSMGen.
"""


import re
import string


class PATTERN:      # noqa
    """Reusable regex fragments for common character classes."""

    punct=rf"[{re.escape(string.punctuation)}]"
    puncts = rf"{punct}+"
