"""
Unit tests for the `textfsmgen.core.patterns.ElementPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/core/element_pattern/test_dot_and_graph.py
    or
    $ python -m pytest tests/unit/core/element_pattern/test_dot_and_graph.py
"""

import pytest   # noqa

from textfsmgen.core.patterns import ElementPattern


from tests.unit.libs.pattern import (
    space, spaces, ws, wss,                     # noqa
    dot, letter, letters,                       # noqa
    digit, digits, alnum, graph,                # noqa
    non_ws, non_wss, punct, puncts,             # noqa
    number, mixed_number, word, mixed_word,     # noqa
    space_or_punct, letter_or_punct,            # noqa
    alnum, alnums,                              # noqa

    sep
)

non_whitespace = non_ws
non_whitespaces = non_wss
punctuation = punct
punctuations = puncts
graphs = f"{graph}+"
dots = dot


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("dot()",       f"{dot}"),
        ("dots()",      f"{dot}+"),
        ("graph()",     f"{graph}"),
        ("graphs()",    f"{graph}+"),
    ]
)
def test(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("optional_dot()",      f"{dot}?"),
        ("optional_dots()",     f"{dot}*"),
        ("optional_graph()",    f"{graph}?"),
        ("optional_graphs()",   f"{graph}*"),
    ]
)
def test_optional(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_one_dot()",       f"{dot}?"),
        ("zero_or_one_dots()",      f"{dot}*"),
        ("zero_or_one_graph()",     f"{graph}?"),
        ("zero_or_one_graphs()",    f"{graph}*"),
    ]
)
def test_zero_or_one(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_more_dot()",      f"{dot}*"),
        ("zero_or_more_dots()",     f"{dot}*"),
        ("zero_or_more_graph()",    f"{graph}*"),
        ("zero_or_more_graphs()",   f"{graph}*"),
    ]
)
def test_zero_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("one_or_more_dot()",       f"{dot}+"),
        ("one_or_more_dots()",      f"{dot}+"),
        ("one_or_more_graph()",     f"{graph}+"),
        ("one_or_more_graphs()",    f"{graph}+"),
    ]
)
def test_one_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("dot_group()",             f"{dot}+"),
        ("dots_group()",            f"{dot}+"),
        ("graph_group()",           f"{graphs}({sep}{graphs})+"),
        ("graphs_group()",          f"{graphs}({sep}{graphs})+"),

        ("optional_dot_group()",    f"{dot}*"),
        ("optional_dots_group()",   f"{dot}*"),
        ("optional_graph_group()",  f"({graphs}({sep}{graphs})+)?"),
        ("optional_graphs_group()", f"({graphs}({sep}{graphs})+)?"),

        ("dot_items()",             f"{dot}+"),
        ("dots_items()",            f"{dot}+"),
        ("graph_items()",           f"{graphs}({sep}{graphs})*"),
        ("graphs_items()",          f"{graphs}({sep}{graphs})*"),

        ("optional_dot_items()",    f"{dot}*"),
        ("optional_dots_items()",   f"{dot}*"),
        ("optional_graph_items()",  f"({graphs}({sep}{graphs})*)?"),
        ("optional_graphs_items()", f"({graphs}({sep}{graphs})*)?"),
    ]
)
def test_group(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("three_dot()",         f"{dot}{{3}}"),
        ("three_dots()",        f"{dot}{{3}}"),
        ("three_graph()",       f"{graph}{{3}}"),
        ("three_graphs()",      f"{graph}{{3}}"),
    ]
)
def test_exact_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected

@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("two_to_five_dot()",       f"{dot}{{{2},{5}}}"),
        ("two_to_five_dots()",      f"{dot}{{{2},{5}}}"),
        ("two_to_five_graph()",     f"{graph}{{{2},{5}}}"),
        ("two_to_five_graphs()",    f"{graph}{{{2},{5}}}"),
    ]
)
def test_range_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected