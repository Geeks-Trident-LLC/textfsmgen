"""
Unit tests for the `textfsmgen.engine.doc.TokenDoc` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/doc/test_validate_keyword_doc.py
    or
    $ python -m pytest tests/unit/engine/doc/test_validate_keyword_doc.py
"""
import pytest   # noqa

from textfsmgen.engine.doc import TokenDoc

from tests.unit.engine.doc import get_keywords


@pytest.mark.parametrize(
    "category, func",
    [
        ("singular",        TokenDoc.singular_placeholder),
        ("plural",          TokenDoc.plural_placeholder),
        ("semantic",        TokenDoc.semantic_placeholder),
        ("plural_semantic", TokenDoc.plural_semantic_placeholder),
        ("group",           TokenDoc.grouped_placeholder),
    ]
)
def test_validate_placeholder_formats(category, func):
    for key in get_keywords(category=category):
        template = func(key)
        try:
            result = template % "dummy"
        except Exception as exc:
            pytest.fail(f"Invalid format for key '{key}': {template}\nException: {exc}")

        assert result, f"Empty result for key '{key}'"


@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "zero or one"),
        ("plural",          True,   "zero or more"),
        ("semantic",        True,   "zero or one"),
        ("plural_semantic", True,   "zero or more"),
        ("group",           True,   "zero or more"),

        ("singular",        False,  "one"),
        ("plural",          False,  "one or more"),
        ("semantic",        False,  "one"),
        ("plural_semantic", False,  "one or more"),
        ("group",           False,  "two or more"),
    ]
)
def test_core_keyword_doc(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(key, or_empty=or_empty)
        keyword_doc = node.describe_core()
        assert expected in keyword_doc


@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "zero or one"),
        ("plural",          True,   "zero or more"),
        ("semantic",        True,   "zero or one"),
        ("plural_semantic", True,   "zero or more"),
        ("group",           True,   "zero or more"),

        ("singular",        False,  "zero or one"),
        ("plural",          False,  "zero or more"),
        ("semantic",        False,  "zero or one"),
        ("plural_semantic", False,  "one or more"),
        ("group",           False,  "one or more"),
    ]
)
def test_prefix_optional_keyword_doc(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"optional_{key}", or_empty=or_empty)
        keyword_doc = node.describe_optional()
        assert expected in keyword_doc
