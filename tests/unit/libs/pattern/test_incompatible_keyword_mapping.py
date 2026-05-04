"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_incompatible_keyword_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_incompatible_keyword_mapping.py
"""

import pytest

from textfsmgen.libs.pattern import ParsedKeywordMappingName


def get_failure_message(keyword):
    fmt = "Undefined %r keyword.  Request technical support for feature extension."
    return fmt % keyword


@pytest.mark.parametrize(
    "incompatible_keyword_name",
    [
        # Note: The <optional> prefix is a standalone modifier.
        #   Combining it with any other prefix (some, zero_or_one, zero_or_more, one_or_more)
        #   or attaching a quantity makes the keyword invalid.
        "3_optional_word",
        "three_optional_word",
        "one_to_three_optional_word",
        "some_optional_word",
        "zero_or_one_optional_word",
        "zero_or_more_optional_word",
        "one_or_more_optional_word",
    ],
)
def test_optional_prefix(incompatible_keyword_name):
    """Reject invalid combinations involving the <optional> prefix."""
    parser = ParsedKeywordMappingName(incompatible_keyword_name)

    failure_msg = get_failure_message(incompatible_keyword_name)

    assert bool(parser) is False
    assert bool(parser.status) is False
    assert parser.status == failure_msg


@pytest.mark.parametrize(
    "incompatible_keyword_name",
    [
        # Note: The <some> prefix is a standalone modifier.
        #   Combining it with any other prefix (optional, zero_or_one, zero_or_more, one_or_more)
        #   or attaching a quantity makes the keyword invalid.
        "3_some_words",
        "three_some_words",
        "one_to_three_some_words",
        "optional_some_words",
        "zero_or_one_some_words",
        "zero_or_more_some_words",
        "one_or_more_some_words",
    ],
)
def test_some_prefix(incompatible_keyword_name):
    """Reject invalid combinations involving the <some> prefix."""
    parser = ParsedKeywordMappingName(incompatible_keyword_name)

    failure_msg = get_failure_message(incompatible_keyword_name)

    assert bool(parser) is False
    assert bool(parser.status) is False
    assert parser.status == failure_msg


@pytest.mark.parametrize(
    "incompatible_keyword_name",
    [
        # Note: The <zero_or_one> prefix is a standalone modifier.
        #   Combining it with any other prefix (optional, some, zero_or_more, one_or_more)
        #   or attaching a quantity makes the keyword invalid.
        "optional_zero_or_one_word",
        "zero_or_one_optional_word",
    ],
)
def test_zero_or_one_prefix(incompatible_keyword_name):
    """Reject invalid combinations involving the <zero-or-one> prefix."""
    parser = ParsedKeywordMappingName(incompatible_keyword_name)

    failure_msg = get_failure_message(incompatible_keyword_name)

    assert bool(parser) is False
    assert bool(parser.status) is False
    assert parser.status == failure_msg


@pytest.mark.parametrize(
    "incompatible_keyword_name",
    [
        # Note: The <zero_or_more> prefix is a standalone modifier.
        #   Combining it with any other prefix (optional, some, zero_or_one, one_or_more)
        #   or attaching a quantity makes the keyword invalid.
        "optional_zero_or_more_words",
        "zero_or_more_optional_words",
    ],
)
def test_zero_or_more_prefix(incompatible_keyword_name):
    """Reject invalid combinations involving the <zero-or-more> prefix."""
    parser = ParsedKeywordMappingName(incompatible_keyword_name)

    failure_msg = get_failure_message(incompatible_keyword_name)

    assert bool(parser) is False
    assert bool(parser.status) is False
    assert parser.status == failure_msg


@pytest.mark.parametrize(
    "incompatible_keyword_name",
    [
        # Note: The <one_or_more> prefix is a standalone modifier.
        #   Combining it with any other prefix (optional, some, zero_or_one, zero_or_more)
        #   or attaching a quantity makes the keyword invalid.
        "optional_one_or_more_words",
        "one_or_more_optional_words",
    ],
)
def test_one_or_more_prefix(incompatible_keyword_name):
    """Reject invalid combinations involving the <one-or-more> prefix."""
    parser = ParsedKeywordMappingName(incompatible_keyword_name)

    failure_msg = get_failure_message(incompatible_keyword_name)

    assert bool(parser) is False
    assert bool(parser.status) is False
    assert parser.status == failure_msg


@pytest.mark.parametrize(
    "incompatible_keyword_name",
    [
        # Note: The <exact-quantity> prefix is a standalone modifier.
        #   Combining it with any other prefix (optional, some, zero_or_one, zero_or_more)
        #   makes the keyword invalid.
        "optional_two_words",
        "optional_2_words",
        "optional_2words",
        "two_optional_words",
        "some_two_words",
    ],
)
def test_exact_quantity_prefix(incompatible_keyword_name):
    """Reject invalid combinations involving the <exact-quantity> prefix."""
    parser = ParsedKeywordMappingName(incompatible_keyword_name)

    failure_msg = get_failure_message(incompatible_keyword_name)

    assert bool(parser) is False
    assert bool(parser.status) is False
    assert parser.status == failure_msg


@pytest.mark.parametrize(
    "incompatible_keyword_name",
    [
        # Note: The <range-quantity> prefix is a standalone modifier.
        #   Combining it with any other prefix (optional, some, zero_or_one, zero_or_more)
        #   makes the keyword invalid.
        "optional_one_to_five_words",
        "optional_one_to_n_words",
        "some_2_to_n_words",
        "some_2_n_words",
    ],
)
def test_range_quantity_prefix(incompatible_keyword_name):
    """Reject invalid combinations involving the <exact-quantity> prefix."""
    parser = ParsedKeywordMappingName(incompatible_keyword_name)

    failure_msg = get_failure_message(incompatible_keyword_name)

    assert bool(parser) is False
    assert bool(parser.status) is False
    assert parser.status == failure_msg


@pytest.mark.parametrize(
    "incompatible_keyword_name",
    [
        # Note: The <group> suffix is a standalone modifier.
        #   Combining it with any other (optional, some, zero_or_one, zero_or_more)
        #   makes the keyword invalid.
        "word_optional_group",
        "word_one_to_five_group",
        "word_some_group",
        "word_one_or_more_group",
    ],
)
def test_group_suffix(incompatible_keyword_name):
    """Reject invalid combinations involving the <range-quantity> suffix."""
    parser = ParsedKeywordMappingName(incompatible_keyword_name)

    failure_msg = get_failure_message(incompatible_keyword_name)

    assert bool(parser) is False
    assert bool(parser.status) is False
    assert parser.status == failure_msg
