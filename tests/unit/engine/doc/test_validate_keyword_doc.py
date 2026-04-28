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
    "category, or_empty, expected",
    [
        ("singular",        True,   "zero or one"),
        ("plural",          True,   "zero or more"),
        ("semantic",        True,   "zero or one"),
        ("plural_semantic", True,   "zero or more"),

        ("singular",        False,  "one"),
        ("plural",          False,  "one or more"),
        ("semantic",        False,  "one"),
        ("plural_semantic", False,  "one or more"),
    ]
)
def test_core_keyword_doc(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(key, or_empty=or_empty)
        keyword_doc = node.describe_core()
        failure = f"({key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure

@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "zero or one"),
        ("plural",          True,   "zero or more"),
        ("semantic",        True,   "zero or one"),
        ("plural_semantic", True,   "zero or more"),

        ("singular",        False,  "zero or one"),
        ("plural",          False,  "zero or more"),
        ("semantic",        False,  "zero or one"),
        ("plural_semantic", False,  "one or more"),
    ]
)
def test_prefix_optional_keyword_doc(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"optional_{key}", or_empty=or_empty)
        keyword_doc = node.describe_optional()
        failure = f"({key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure

@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "zero or more"),
        ("plural",          True,   "zero or more"),
        ("semantic",        True,   "zero or more"),
        ("plural_semantic", True,   "zero or more"),

        ("singular",        False,  "one or more"),
        ("plural",          False,  "one or more"),
        ("semantic",        False,  "one or more"),
        ("plural_semantic", False,  "one or more"),
    ]
)
def test_prefix_some_keyword_doc(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"some_{key}", or_empty=or_empty)
        keyword_doc = node.describe_some()
        failure = f"({key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure

@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "zero or one"),
        ("plural",          True,   "zero or more"),
        ("semantic",        True,   "zero or one"),
        ("plural_semantic", True,   "zero or more"),

        ("singular",        False,  "zero or one"),
        ("plural",          False,  "zero or more"),
        ("semantic",        False,  "zero or one"),
        ("plural_semantic", False,  "zero or more"),
    ]
)
def test_prefix_zero_or_one_keyword_doc(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"zero_or_one_{key}", or_empty=or_empty)
        keyword_doc = node.describe_zero_or_one()
        failure = f"({key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure


@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "zero or more"),
        ("plural",          True,   "zero or more"),
        ("semantic",        True,   "zero or more"),
        ("plural_semantic", True,   "zero or more"),

        ("singular",        False,  "zero or more"),
        ("plural",          False,  "zero or more"),
        ("semantic",        False,  "zero or more"),
        ("plural_semantic", False,  "zero or more"),
    ]
)
def test_prefix_zero_or_more_keyword_doc(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"zero_or_more_{key}", or_empty=or_empty)
        keyword_doc = node.describe_zero_or_more()
        failure = f"({key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure


@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "zero or more"),
        ("plural",          True,   "zero or more"),
        ("semantic",        True,   "zero or more"),
        ("plural_semantic", True,   "zero or more"),

        ("singular",        False,  "one or more"),
        ("plural",          False,  "one or more"),
        ("semantic",        False,  "one or more"),
        ("plural_semantic", False,  "one or more"),
    ]
)
def test_prefix_one_or_more_keyword_doc(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"one_or_more_{key}", or_empty=or_empty)
        keyword_doc = node.describe_one_or_more()
        failure = f"({key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure
        
        
@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("dot_group",               "zero or more"),
        ("space_group",             "zero or more"),
        ("ws_group",                "zero or more"),
        ("whitespace_group",        "zero or more"),

        # semantic case
        ("digit_group",             "zero or more"),
        ("letter_group",            "zero or more"),
        ("alnum_group",             "zero or more"),
        ("punct_group",             "zero or more"),
        ("punctuation_group",       "zero or more"),
        ("graph_group",             "zero or more"),
        ("non_ws_group",            "zero or more"),
        ("non_whitespace_group",    "zero or more"),
        ("space_or_punct_group",    "zero or more"),
        ("punct_or_space_group",    "zero or more"),
        ("sop_group",               "zero or more"),
        ("letter_or_punct_group",   "zero or more"),
        ("punct_or_letter_group",   "zero or more"),
        ("lop_group",               "zero or more"),

        # special case - plural
        ("dots_group",              "zero or more"),
        ("spaces_group",            "zero or more"),
        ("wss_group",               "zero or more"),
        ("whitespaces_group",       "zero or more"),

        # semantic case - plural
        ("digits_group",            "zero or more"),
        ("letters_group",           "zero or more"),
        ("alnums_group",            "zero or more"),
        ("puncts_group",            "zero or more"),
        ("punctuations_group",      "zero or more"),
        ("graphs_group",            "zero or more"),
        ("non_wss_group",           "zero or more"),
        ("non_whitespaces_group",   "zero or more"),

        ("spaces_or_puncts_group",  "zero or more"),
        ("puncts_or_spaces_group",  "zero or more"),
        ("sops_group",              "zero or more"),

        ("letters_or_puncts_group", "zero or more"),
        ("puncts_or_letters_group", "zero or more"),
        ("lops_group",              "zero or more"),
    ]
)
def test_group_keyword_doc_with_or_empty(keyword, expected):
    node = TokenDoc(keyword, or_empty=True)
    doc = node.describe_group()
    failure = f"({keyword}|or_empty=True|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("dot_group",               "one or more"),
        ("space_group",             "one or more"),
        ("ws_group",                "one or more"),
        ("whitespace_group",        "one or more"),

        # semantic case
        ("digit_group",             "two or more"),
        ("letter_group",            "two or more"),
        ("alnum_group",             "two or more"),
        ("punct_group",             "two or more"),
        ("punctuation_group",       "two or more"),
        ("graph_group",             "two or more"),
        ("non_ws_group",            "two or more"),
        ("non_whitespace_group",    "two or more"),
        ("space_or_punct_group",    "two or more"),
        ("punct_or_space_group",    "two or more"),
        ("sop_group",               "two or more"),
        ("letter_or_punct_group",   "two or more"),
        ("punct_or_letter_group",   "two or more"),
        ("lop_group",               "two or more"),

        # special case - plural
        ("dots_group",              "one or more"),
        ("spaces_group",            "one or more"),
        ("wss_group",               "one or more"),
        ("whitespaces_group",       "one or more"),

        # semantic case - plural
        ("digits_group",            "two or more"),
        ("letters_group",           "two or more"),
        ("alnums_group",            "two or more"),
        ("puncts_group",            "two or more"),
        ("punctuations_group",      "two or more"),
        ("graphs_group",            "two or more"),
        ("non_wss_group",           "two or more"),
        ("non_whitespaces_group",   "two or more"),

        ("spaces_or_puncts_group",  "two or more"),
        ("puncts_or_spaces_group",  "two or more"),
        ("sops_group",              "two or more"),

        ("letters_or_puncts_group", "two or more"),
        ("puncts_or_letters_group", "two or more"),
        ("lops_group",              "two or more"),
    ]
)
def test_group_keyword_doc(keyword, expected):
    node = TokenDoc(keyword)
    doc = node.describe_group()
    failure = f"({keyword}|{expected}) => {doc}"
    assert expected in doc, failure

@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("optional_dot_group",               "zero or more"),
        ("optional_space_group",             "zero or more"),
        ("optional_ws_group",                "zero or more"),
        ("optional_whitespace_group",        "zero or more"),

        # semantic case
        ("optional_digit_group",             "zero or more"),
        ("optional_letter_group",            "zero or more"),
        ("optional_alnum_group",             "zero or more"),
        ("optional_punct_group",             "zero or more"),
        ("optional_punctuation_group",       "zero or more"),
        ("optional_graph_group",             "zero or more"),
        ("optional_non_ws_group",            "zero or more"),
        ("optional_non_whitespace_group",    "zero or more"),
        ("optional_space_or_punct_group",    "zero or more"),
        ("optional_punct_or_space_group",    "zero or more"),
        ("optional_sop_group",               "zero or more"),
        ("optional_letter_or_punct_group",   "zero or more"),
        ("optional_punct_or_letter_group",   "zero or more"),
        ("optional_lop_group",               "zero or more"),

        # special case - plural
        ("optional_dots_group",              "zero or more"),
        ("optional_spaces_group",            "zero or more"),
        ("optional_wss_group",               "zero or more"),
        ("optional_whitespaces_group",       "zero or more"),

        # semantic case - plural
        ("optional_digits_group",            "zero or more"),
        ("optional_letters_group",           "zero or more"),
        ("optional_alnums_group",            "zero or more"),
        ("optional_puncts_group",            "zero or more"),
        ("optional_punctuations_group",      "zero or more"),
        ("optional_graphs_group",            "zero or more"),
        ("optional_non_wss_group",           "zero or more"),
        ("optional_non_whitespaces_group",   "zero or more"),

        ("optional_spaces_or_puncts_group",  "zero or more"),
        ("optional_puncts_or_spaces_group",  "zero or more"),
        ("optional_sops_group",              "zero or more"),

        ("optional_letters_or_puncts_group", "zero or more"),
        ("optional_puncts_or_letters_group", "zero or more"),
        ("optional_lops_group",              "zero or more"),
    ]
)
def test_optional_group_keyword_doc_with_or_empty(keyword, expected):
    node = TokenDoc(keyword, or_empty=True)
    doc = node.describe_group()
    failure = f"({keyword}|or_empty=True|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("optional_dot_group",               "zero or more"),
        ("optional_space_group",             "zero or more"),
        ("optional_ws_group",                "zero or more"),
        ("optional_whitespace_group",        "zero or more"),

        # semantic case
        ("optional_digit_group",             "one or more"),
        ("optional_letter_group",            "one or more"),
        ("optional_alnum_group",             "one or more"),
        ("optional_punct_group",             "one or more"),
        ("optional_punctuation_group",       "one or more"),
        ("optional_graph_group",             "one or more"),
        ("optional_non_ws_group",            "one or more"),
        ("optional_non_whitespace_group",    "one or more"),
        ("optional_space_or_punct_group",    "one or more"),
        ("optional_punct_or_space_group",    "one or more"),
        ("optional_sop_group",               "one or more"),
        ("optional_letter_or_punct_group",   "one or more"),
        ("optional_punct_or_letter_group",   "one or more"),
        ("optional_lop_group",               "one or more"),

        # special case - plural
        ("optional_dots_group",              "zero or more"),
        ("optional_spaces_group",            "zero or more"),
        ("optional_wss_group",               "zero or more"),
        ("optional_whitespaces_group",       "zero or more"),

        # semantic case - plural
        ("optional_digits_group",            "one or more"),
        ("optional_letters_group",           "one or more"),
        ("optional_alnums_group",            "one or more"),
        ("optional_puncts_group",            "one or more"),
        ("optional_punctuations_group",      "one or more"),
        ("optional_graphs_group",            "one or more"),
        ("optional_non_wss_group",           "one or more"),
        ("optional_non_whitespaces_group",   "one or more"),

        ("optional_spaces_or_puncts_group",  "one or more"),
        ("optional_puncts_or_spaces_group",  "one or more"),
        ("optional_sops_group",              "one or more"),

        ("optional_letters_or_puncts_group", "one or more"),
        ("optional_puncts_or_letters_group", "one or more"),
        ("optional_lops_group",              "one or more"),
    ]
)
def test_optional_group_keyword_doc(keyword, expected):
    node = TokenDoc(keyword)
    doc = node.describe_group()
    failure = f"({keyword}|{expected}) => {doc}"
    assert expected in doc, failure