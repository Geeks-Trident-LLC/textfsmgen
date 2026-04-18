"""
Unit tests for the `textfsmgen.libs.text.wrap_text_block` function.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/text/wrap_text_block.py
    or
    $ python -m pytest tests/unit/libs/text/wrap_text_block.py
"""

import pytest       # noqa

from textwrap import dedent
from textfsmgen.libs.text import wrap_text_block


def sample_text() -> str:
    """Return a fixed multi‑sentence block used for wrapping tests."""
    return (
        "ABC XYZ LLC is a San Jose based company offering unique "
        "solutions and a variety of services. Our business is "
        "setting the industry standards, positioning us as "
        "category leaders worldwide."
    )


@pytest.mark.parametrize(
    "block, subject, limit, expected",
    [
        (
            sample_text(),
            "Explanation:",
            68,
            """
            Explanation: ABC XYZ LLC is a San Jose based company offering unique
                         solutions and a variety of services. Our business is
                         setting the industry standards, positioning us as
                         category leaders worldwide.
            """,
        ),
        (
            sample_text(),
            "This is very long subject line:",
            68,
            """
            This is very long subject line:
                ABC XYZ LLC is a San Jose based company offering unique
                solutions and a variety of services. Our business is setting the
                industry standards, positioning us as category leaders
                worldwide.
            """,
        ),
    ],
)
def test_wrap_text(block, subject, limit, expected):
    result = wrap_text_block(block, subject=subject, limit=limit)
    assert result == dedent(expected).strip()
