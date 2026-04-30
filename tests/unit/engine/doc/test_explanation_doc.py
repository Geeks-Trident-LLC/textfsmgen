"""
Unit tests for the `textfsmgen.engine.doc.OperationDoc` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/doc/test_validate_keyword_doc.py
    or
    $ python -m pytest tests/unit/engine/doc/test_validate_keyword_doc.py
"""

import pytest       # noqa

from textfsmgen.engine.doc import ExplanationDoc


@pytest.mark.parametrize(
    "snippet, expected",
    [
        (
            "word()",
            {"semantic": "word", "quantity": "", "unit": ""}
        ),
        (
            "word_group()",
            {"semantic": "word", "quantity": "", "unit": "group"}
        ),
        (
            "word_items()",
            {"semantic": "word", "quantity": "", "unit": "items"}
        ),
        (
            "some_word()",
            {"semantic": "word", "quantity": "some", "unit": ""}
        ),
        (
            "zero_or_one_word()",
            {"semantic": "word", "quantity": "zero_or_one", "unit": ""}
        ),
        (
            "zero_or_more_word()",
            {"semantic": "word", "quantity": "zero_or_more", "unit": ""}
        ),
        (
            "one_or_more_word()",
            {"semantic": "word", "quantity": "one_or_more", "unit": ""}
        ),
        (
            "optional_word()",
            {"semantic": "word", "quantity": "optional", "unit": ""}
        ),
        (
            "optional_word_group()",
            {"semantic": "word", "quantity": "optional", "unit": "group"}
        ),
        (
            "optional_word_items()",
            {"semantic": "word", "quantity": "optional", "unit": "items"}
        ),

    ]
)
def test_parse(snippet, expected):
    doc = ExplanationDoc(snippet)

    assert bool(doc) is True

    for attr, value in expected.items():
        assert getattr(doc, attr) == value
