"""
Unit tests for the `textfsmgen.engine.translate` module.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate
    or
    $ python -m pytest tests/unit/translate
"""


class TranslatedDummyPattern:
    """
    A lightweight dummy implementation of `PatternTranslator` used for unit testing.
    """


def to_list(arg):
    return arg if isinstance(arg, (list, tuple)) else (arg,)
