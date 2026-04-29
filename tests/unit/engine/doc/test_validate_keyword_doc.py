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
        ("singular",        True,   "match zero or one"),
        ("plural",          True,   "match zero or more"),
        ("semantic",        True,   "match zero or one"),
        ("plural_semantic", True,   "match zero or more"),

        ("singular",        False,  "match one"),
        ("plural",          False,  "match one or more"),
        ("semantic",        False,  "match one"),
        ("plural_semantic", False,  "match one or more"),
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
        ("singular",        True,   "match zero or one"),
        ("plural",          True,   "match zero or more"),
        ("semantic",        True,   "match zero or one"),
        ("plural_semantic", True,   "match zero or more"),

        ("singular",        False,  "match zero or one"),
        ("plural",          False,  "match zero or more"),
        ("semantic",        False,  "match zero or one"),
        ("plural_semantic", False,  "match zero or more"),
    ]
)
def test_prefix_optional(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"optional_{key}", or_empty=or_empty)
        keyword_doc = node.describe_optional()
        failure = f"(optional_{key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure

@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "match zero or more"),
        ("plural",          True,   "match zero or more"),
        ("semantic",        True,   "match zero or more"),
        ("plural_semantic", True,   "match zero or more"),

        ("singular",        False,  "match one or more"),
        ("plural",          False,  "match one or more"),
        ("semantic",        False,  "match one or more"),
        ("plural_semantic", False,  "match one or more"),
    ]
)
def test_prefix_some(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"some_{key}", or_empty=or_empty)
        keyword_doc = node.describe_some()
        failure = f"(some_{key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure

@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "match zero or one"),
        ("plural",          True,   "match zero or more"),
        ("semantic",        True,   "match zero or one"),
        ("plural_semantic", True,   "match zero or more"),

        ("singular",        False,  "match zero or one"),
        ("plural",          False,  "match zero or more"),
        ("semantic",        False,  "match zero or one"),
        ("plural_semantic", False,  "match zero or more"),
    ]
)
def test_prefix_zero_or_one(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"zero_or_one_{key}", or_empty=or_empty)
        keyword_doc = node.describe_zero_or_one()
        failure = f"(zero_or_one_{key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure


@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "match zero or more"),
        ("plural",          True,   "match zero or more"),
        ("semantic",        True,   "match zero or more"),
        ("plural_semantic", True,   "match zero or more"),

        ("singular",        False,  "match zero or more"),
        ("plural",          False,  "match zero or more"),
        ("semantic",        False,  "match zero or more"),
        ("plural_semantic", False,  "match zero or more"),
    ]
)
def test_prefix_zero_or_more(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"zero_or_more_{key}", or_empty=or_empty)
        keyword_doc = node.describe_zero_or_more()
        failure = f"(zero_or_more_{key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure


@pytest.mark.parametrize(
    "category, or_empty, expected",
    [
        ("singular",        True,   "match zero or more"),
        ("plural",          True,   "match zero or more"),
        ("semantic",        True,   "match zero or more"),
        ("plural_semantic", True,   "match zero or more"),

        ("singular",        False,  "match one or more"),
        ("plural",          False,  "match one or more"),
        ("semantic",        False,  "match one or more"),
        ("plural_semantic", False,  "match one or more"),
    ]
)
def test_prefix_one_or_more(category, or_empty, expected):
    for key in get_keywords(category=category):
        node = TokenDoc(f"one_or_more_{key}", or_empty=or_empty)
        keyword_doc = node.describe_one_or_more()
        failure = f"(one_or_more_{key}|{category}|{or_empty}|{expected}) => {keyword_doc}"
        assert expected in keyword_doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("dot_group",               "match zero or more"),
        ("space_group",             "match zero or more"),
        ("ws_group",                "match zero or more"),
        ("whitespace_group",        "match zero or more"),

        # semantic case
        ("digit_group",             "match zero or more"),
        ("letter_group",            "match zero or more"),
        ("alnum_group",             "match zero or more"),
        ("punct_group",             "match zero or more"),
        ("punctuation_group",       "match zero or more"),
        ("graph_group",             "match zero or more"),
        ("non_ws_group",            "match zero or more"),
        ("non_whitespace_group",    "match zero or more"),
        ("space_or_punct_group",    "match zero or more"),
        ("punct_or_space_group",    "match zero or more"),
        ("sop_group",               "match zero or more"),
        ("letter_or_punct_group",   "match zero or more"),
        ("punct_or_letter_group",   "match zero or more"),
        ("lop_group",               "match zero or more"),

        # special case - plural
        ("dots_group",              "match zero or more"),
        ("spaces_group",            "match zero or more"),
        ("wss_group",               "match zero or more"),
        ("whitespaces_group",       "match zero or more"),

        # semantic case - plural
        ("digits_group",            "match zero or more"),
        ("letters_group",           "match zero or more"),
        ("alnums_group",            "match zero or more"),
        ("puncts_group",            "match zero or more"),
        ("punctuations_group",      "match zero or more"),
        ("graphs_group",            "match zero or more"),
        ("non_wss_group",           "match zero or more"),
        ("non_whitespaces_group",   "match zero or more"),

        ("spaces_or_puncts_group",  "match zero or more"),
        ("puncts_or_spaces_group",  "match zero or more"),
        ("sops_group",              "match zero or more"),

        ("letters_or_puncts_group", "match zero or more"),
        ("puncts_or_letters_group", "match zero or more"),
        ("lops_group",              "match zero or more"),
    ]
)
def test_suffix_group_with_empty_flag(keyword, expected):
    node = TokenDoc(keyword, or_empty=True)
    doc = node.describe_group()
    failure = f"({keyword}|or_empty=True|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("dot_group",               "match one or more"),
        ("space_group",             "match one or more"),
        ("ws_group",                "match one or more"),
        ("whitespace_group",        "match one or more"),

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
        ("dots_group",              "match one or more"),
        ("spaces_group",            "match one or more"),
        ("wss_group",               "match one or more"),
        ("whitespaces_group",       "match one or more"),

        # semantic case - plural
        ("digits_group",            "match two or more"),
        ("letters_group",           "match two or more"),
        ("alnums_group",            "match two or more"),
        ("puncts_group",            "match two or more"),
        ("punctuations_group",      "match two or more"),
        ("graphs_group",            "match two or more"),
        ("non_wss_group",           "match two or more"),
        ("non_whitespaces_group",   "match two or more"),

        ("spaces_or_puncts_group",  "match two or more"),
        ("puncts_or_spaces_group",  "match two or more"),
        ("sops_group",              "match two or more"),

        ("letters_or_puncts_group", "match two or more"),
        ("puncts_or_letters_group", "match two or more"),
        ("lops_group",              "match two or more"),
    ]
)
def test_suffix_group(keyword, expected):
    node = TokenDoc(keyword)
    doc = node.describe_group()
    failure = f"({keyword}|{expected}) => {doc}"
    assert expected in doc, failure

@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("optional_dot_group",               "match zero or more"),
        ("optional_space_group",             "match zero or more"),
        ("optional_ws_group",                "match zero or more"),
        ("optional_whitespace_group",        "match zero or more"),

        # semantic case
        ("optional_digit_group",             "match zero or more"),
        ("optional_letter_group",            "match zero or more"),
        ("optional_alnum_group",             "match zero or more"),
        ("optional_punct_group",             "match zero or more"),
        ("optional_punctuation_group",       "match zero or more"),
        ("optional_graph_group",             "match zero or more"),
        ("optional_non_ws_group",            "match zero or more"),
        ("optional_non_whitespace_group",    "match zero or more"),
        ("optional_space_or_punct_group",    "match zero or more"),
        ("optional_punct_or_space_group",    "match zero or more"),
        ("optional_sop_group",               "match zero or more"),
        ("optional_letter_or_punct_group",   "match zero or more"),
        ("optional_punct_or_letter_group",   "match zero or more"),
        ("optional_lop_group",               "match zero or more"),

        # special case - plural
        ("optional_dots_group",              "match zero or more"),
        ("optional_spaces_group",            "match zero or more"),
        ("optional_wss_group",               "match zero or more"),
        ("optional_whitespaces_group",       "match zero or more"),

        # semantic case - plural
        ("optional_digits_group",            "match zero or more"),
        ("optional_letters_group",           "match zero or more"),
        ("optional_alnums_group",            "match zero or more"),
        ("optional_puncts_group",            "match zero or more"),
        ("optional_punctuations_group",      "match zero or more"),
        ("optional_graphs_group",            "match zero or more"),
        ("optional_non_wss_group",           "match zero or more"),
        ("optional_non_whitespaces_group",   "match zero or more"),

        ("optional_spaces_or_puncts_group",  "match zero or more"),
        ("optional_puncts_or_spaces_group",  "match zero or more"),
        ("optional_sops_group",              "match zero or more"),

        ("optional_letters_or_puncts_group", "match zero or more"),
        ("optional_puncts_or_letters_group", "match zero or more"),
        ("optional_lops_group",              "match zero or more"),
    ]
)
def test_optional_group_with_empty_flag(keyword, expected):
    node = TokenDoc(keyword, or_empty=True)
    doc = node.describe_group()
    failure = f"({keyword}|or_empty=True|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("optional_dot_group",               "match zero or more"),
        ("optional_space_group",             "match zero or more"),
        ("optional_ws_group",                "match zero or more"),
        ("optional_whitespace_group",        "match zero or more"),

         # semantic case
        ("optional_digit_group",             "match zero or more"),
        ("optional_letter_group",            "match zero or more"),
        ("optional_alnum_group",             "match zero or more"),
        ("optional_punct_group",             "match zero or more"),
        ("optional_punctuation_group",       "match zero or more"),
        ("optional_graph_group",             "match zero or more"),
        ("optional_non_ws_group",            "match zero or more"),
        ("optional_non_whitespace_group",    "match zero or more"),
        ("optional_space_or_punct_group",    "match zero or more"),
        ("optional_punct_or_space_group",    "match zero or more"),
        ("optional_sop_group",               "match zero or more"),
        ("optional_letter_or_punct_group",   "match zero or more"),
        ("optional_punct_or_letter_group",   "match zero or more"),
        ("optional_lop_group",               "match zero or more"),

        # special case - plural
        ("optional_dots_group",              "match zero or more"),
        ("optional_spaces_group",            "match zero or more"),
        ("optional_wss_group",               "match zero or more"),
        ("optional_whitespaces_group",       "match zero or more"),

        # semantic case - plural
        ("optional_digits_group",            "match zero or more"),
        ("optional_letters_group",           "match zero or more"),
        ("optional_alnums_group",            "match zero or more"),
        ("optional_puncts_group",            "match zero or more"),
        ("optional_punctuations_group",      "match zero or more"),
        ("optional_graphs_group",            "match zero or more"),
        ("optional_non_wss_group",           "match zero or more"),
        ("optional_non_whitespaces_group",   "match zero or more"),

        ("optional_spaces_or_puncts_group",  "match zero or more"),
        ("optional_puncts_or_spaces_group",  "match zero or more"),
        ("optional_sops_group",              "match zero or more"),

        ("optional_letters_or_puncts_group", "match zero or more"),
        ("optional_puncts_or_letters_group", "match zero or more"),
        ("optional_lops_group",              "match zero or more"),
    ]
)
def test_optional_group(keyword, expected):
    node = TokenDoc(keyword)
    doc = node.describe_group()
    failure = f"({keyword}|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("dot_items",               "match zero or more"),
        ("space_items",             "match zero or more"),
        ("ws_items",                "match zero or more"),
        ("whitespace_items",        "match zero or more"),

        # semantic case
        ("digit_items",             "match zero or more"),
        ("letter_items",            "match zero or more"),
        ("alnum_items",             "match zero or more"),
        ("punct_items",             "match zero or more"),
        ("punctuation_items",       "match zero or more"),
        ("graph_items",             "match zero or more"),
        ("non_ws_items",            "match zero or more"),
        ("non_whitespace_items",    "match zero or more"),
        ("space_or_punct_items",    "match zero or more"),
        ("punct_or_space_items",    "match zero or more"),
        ("sop_items",               "match zero or more"),
        ("letter_or_punct_items",   "match zero or more"),
        ("punct_or_letter_items",   "match zero or more"),
        ("lop_items",               "match zero or more"),

        # special case - plural
        ("dots_items",              "match zero or more"),
        ("spaces_items",            "match zero or more"),
        ("wss_items",               "match zero or more"),
        ("whitespaces_items",       "match zero or more"),

        # semantic case - plural
        ("digits_items",            "match zero or more"),
        ("letters_items",           "match zero or more"),
        ("alnums_items",            "match zero or more"),
        ("puncts_items",            "match zero or more"),
        ("punctuations_items",      "match zero or more"),
        ("graphs_items",            "match zero or more"),
        ("non_wss_items",           "match zero or more"),
        ("non_whitespaces_items",   "match zero or more"),

        ("spaces_or_puncts_items",  "match zero or more"),
        ("puncts_or_spaces_items",  "match zero or more"),
        ("sops_items",              "match zero or more"),

        ("letters_or_puncts_items", "match zero or more"),
        ("puncts_or_letters_items", "match zero or more"),
        ("lops_items",              "match zero or more"),
    ]
)
def test_suffix_items_with_empty_flag(keyword, expected):
    node = TokenDoc(keyword, or_empty=True)
    doc = node.describe_items()
    failure = f"({keyword}|or_empty=True|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("dot_items",               "match one or more"),
        ("space_items",             "match one or more"),
        ("ws_items",                "match one or more"),
        ("whitespace_items",        "match one or more"),

         # semantic case
        ("digit_items",             "match one or more"),
        ("letter_items",            "match one or more"),
        ("alnum_items",             "match one or more"),
        ("punct_items",             "match one or more"),
        ("punctuation_items",       "match one or more"),
        ("graph_items",             "match one or more"),
        ("non_ws_items",            "match one or more"),
        ("non_whitespace_items",    "match one or more"),
        ("space_or_punct_items",    "match one or more"),
        ("punct_or_space_items",    "match one or more"),
        ("sop_items",               "match one or more"),
        ("letter_or_punct_items",   "match one or more"),
        ("punct_or_letter_items",   "match one or more"),
        ("lop_items",               "match one or more"),

        # special case - plural
        ("dots_items",              "match one or more"),
        ("spaces_items",            "match one or more"),
        ("wss_items",               "match one or more"),
        ("whitespaces_items",       "match one or more"),

        # semantic case - plural
        ("digits_items",            "match one or more"),
        ("letters_items",           "match one or more"),
        ("alnums_items",            "match one or more"),
        ("puncts_items",            "match one or more"),
        ("punctuations_items",      "match one or more"),
        ("graphs_items",            "match one or more"),
        ("non_wss_items",           "match one or more"),
        ("non_whitespaces_items",   "match one or more"),

        ("spaces_or_puncts_items",  "match one or more"),
        ("puncts_or_spaces_items",  "match one or more"),
        ("sops_items",              "match one or more"),

        ("letters_or_puncts_items", "match one or more"),
        ("puncts_or_letters_items", "match one or more"),
        ("lops_items",              "match one or more"),
    ]
)
def test_items(keyword, expected):
    node = TokenDoc(keyword)
    doc = node.describe_items()
    failure = f"({keyword}|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("optional_dot_items",               "match zero or more"),
        ("optional_space_items",             "match zero or more"),
        ("optional_ws_items",                "match zero or more"),
        ("optional_whitespace_items",        "match zero or more"),

        # semantic case
        ("optional_digit_items",             "match zero or more"),
        ("optional_letter_items",            "match zero or more"),
        ("optional_alnum_items",             "match zero or more"),
        ("optional_punct_items",             "match zero or more"),
        ("optional_punctuation_items",       "match zero or more"),
        ("optional_graph_items",             "match zero or more"),
        ("optional_non_ws_items",            "match zero or more"),
        ("optional_non_whitespace_items",    "match zero or more"),
        ("optional_space_or_punct_items",    "match zero or more"),
        ("optional_punct_or_space_items",    "match zero or more"),
        ("optional_sop_items",               "match zero or more"),
        ("optional_letter_or_punct_items",   "match zero or more"),
        ("optional_punct_or_letter_items",   "match zero or more"),
        ("optional_lop_items",               "match zero or more"),

        # special case - plural
        ("optional_dots_items",              "match zero or more"),
        ("optional_spaces_items",            "match zero or more"),
        ("optional_wss_items",               "match zero or more"),
        ("optional_whitespaces_items",       "match zero or more"),

        # semantic case - plural
        ("optional_digits_items",            "match zero or more"),
        ("optional_letters_items",           "match zero or more"),
        ("optional_alnums_items",            "match zero or more"),
        ("optional_puncts_items",            "match zero or more"),
        ("optional_punctuations_items",      "match zero or more"),
        ("optional_graphs_items",            "match zero or more"),
        ("optional_non_wss_items",           "match zero or more"),
        ("optional_non_whitespaces_items",   "match zero or more"),

        ("optional_spaces_or_puncts_items",  "match zero or more"),
        ("optional_puncts_or_spaces_items",  "match zero or more"),
        ("optional_sops_items",              "match zero or more"),

        ("optional_letters_or_puncts_items", "match zero or more"),
        ("optional_puncts_or_letters_items", "match zero or more"),
        ("optional_lops_items",              "match zero or more"),
    ]
)
def test_optional_items_with_empty_flag(keyword, expected):
    node = TokenDoc(keyword, or_empty=True)
    doc = node.describe_items()
    failure = f"({keyword}|or_empty=True|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, expected",
    [
        # special case
        ("optional_dot_items",               "match zero or more"),
        ("optional_space_items",             "match zero or more"),
        ("optional_ws_items",                "match zero or more"),
        ("optional_whitespace_items",        "match zero or more"),

         # semantic case
        ("optional_digit_items",             "match zero or more"),
        ("optional_letter_items",            "match zero or more"),
        ("optional_alnum_items",             "match zero or more"),
        ("optional_punct_items",             "match zero or more"),
        ("optional_punctuation_items",       "match zero or more"),
        ("optional_graph_items",             "match zero or more"),
        ("optional_non_ws_items",            "match zero or more"),
        ("optional_non_whitespace_items",    "match zero or more"),
        ("optional_space_or_punct_items",    "match zero or more"),
        ("optional_punct_or_space_items",    "match zero or more"),
        ("optional_sop_items",               "match zero or more"),
        ("optional_letter_or_punct_items",   "match zero or more"),
        ("optional_punct_or_letter_items",   "match zero or more"),
        ("optional_lop_items",               "match zero or more"),

        # special case - plural
        ("optional_dots_items",              "match zero or more"),
        ("optional_spaces_items",            "match zero or more"),
        ("optional_wss_items",               "match zero or more"),
        ("optional_whitespaces_items",       "match zero or more"),

        # semantic case - plural
        ("optional_digits_items",            "match zero or more"),
        ("optional_letters_items",           "match zero or more"),
        ("optional_alnums_items",            "match zero or more"),
        ("optional_puncts_items",            "match zero or more"),
        ("optional_punctuations_items",      "match zero or more"),
        ("optional_graphs_items",            "match zero or more"),
        ("optional_non_wss_items",           "match zero or more"),
        ("optional_non_whitespaces_items",   "match zero or more"),

        ("optional_spaces_or_puncts_items",  "match zero or more"),
        ("optional_puncts_or_spaces_items",  "match zero or more"),
        ("optional_sops_items",              "match zero or more"),

        ("optional_letters_or_puncts_items", "match zero or more"),
        ("optional_puncts_or_letters_items", "match zero or more"),
        ("optional_lops_items",              "match zero or more"),
    ]
)
def test_optional_items(keyword, expected):
    node = TokenDoc(keyword)
    doc = node.describe_items()
    failure = f"({keyword}|{expected}) => {doc}"
    assert expected in doc, failure


@pytest.mark.parametrize(
    "keyword, exp1, exp2",
    [
        # special case
        # (
        #     "3word",
        #     "match exactly three words ",
        #     "separated by one or more whitespace characters."
        # ),
        # (
        #     "3_word",
        #     "match exactly three words ",
        #     "separated by one or more whitespace characters."
        # ),
        (
            "three_word",
            "match exactly three words ",
            "separated by one or more whitespace characters."
        ),
        # (
        #     "3words",
        #     "match exactly three words ",
        #     "separated by one or more whitespace characters."
        # ),
        # (
        #     "3_words",
        #     "match exactly three words ",
        #     "separated by one or more whitespace characters."
        # ),
        (
            "three_words",
            "match exactly three words ",
            "separated by one or more whitespace characters."
        ),

    ]
)
def test_exact_match(keyword, exp1, exp2):
    node = TokenDoc(keyword)
    doc = node.describe_exact_match()
    failure = f"({keyword}|{exp1}|{exp2}) => {doc}"
    assert exp1 in doc, failure
    assert exp2 in doc, failure


@pytest.mark.parametrize(
    "keyword, exp1, exp2",
    [
        # special case
        (
            "2_to_4_words",
            "match two to four words ",
            "separated by one or more whitespace characters."
        ),
        (
            "two_to_four_words",
            "match two to four words ",
            "separated by one or more whitespace characters."
        ),

        (
            "2_to_n_words",
            "match two or more words ",
            "separated by one or more whitespace characters."
        ),
        (
            "two_to_n_words",
            "match two or more words ",
            "separated by one or more whitespace characters."
        ),

        (
            "2_to_2_words",
            "match exactly two words ",
            "separated by one or more whitespace characters."
        ),
        (
            "two_to_two_words",
            "match exactly two words ",
            "separated by one or more whitespace characters."
        ),

    ]
)
def test_range_match(keyword, exp1, exp2):
    node = TokenDoc(keyword)
    doc = node.describe_range_match()
    failure = f"({keyword}|{exp1}|{exp2}) => {doc}"
    assert exp1 in doc, failure
    assert exp2 in doc, failure