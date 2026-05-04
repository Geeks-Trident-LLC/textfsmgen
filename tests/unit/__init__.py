"""
Unit tests for the `textfsmgen` packages.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest
    $ pytest tests/unit
    or
    $ python -m pytest
    $ python -m pytest tests/unit
"""

import re


def replace_dates_with_placeholder(text: str, placeholder: str = "YYYY-mm-dd") -> str:
    """
    Replace actual dates in the format YYYY-MM-DD with a placeholder.

    Parameters
    ----------
    text : str
        Input text that may contain dates.
    placeholder : str, optional
        The placeholder string to substitute for dates.
        Defaults to "YYYY-mm-dd".

    Returns
    -------
    str
        Text with dates replaced by the placeholder.
    """
    pattern = r"^# Created date: \d{4}-\d{2}-\d{2}"
    replacement = f"# Created date: {placeholder}"
    return re.sub(pattern, replacement, text, flags=re.MULTILINE)


class DummyClass:
    """Simple class used to test object-based exception naming."""
