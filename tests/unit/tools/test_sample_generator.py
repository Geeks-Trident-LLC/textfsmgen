"""
Unit tests for the `textfsmgen.tools.samples.SamplesGenerator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/tools/test_sample_generator.py
    or
    $ python -m pytest tests/unit/tools/test_sample_generator.py
"""

import pytest
import re
from textfsmgen.tools.samples import SamplesGenerator

from textfsmgen.libs.decorators import catch_debug_break


@pytest.mark.parametrize(
    "snippet",
    (
        "numbers()",
        "mixed_numbers()",
        "words()",
        "mixed_words()",
    ),
)
def test_plural_semantic(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "dot()",
        "dots()",
        "space()",
        "spaces()",
        "ws()",
        "wss()",
        "whitespace()",
        "whitespaces()",
        "digit()",
        "digits()",
        "number()",
        "mixed_number()",
        "letter()",
        "letters()",
        "alnum()",
        "alnums()",
        "graph()",
        "graphs()",
        "punct()",
        "puncts()",
        "word()",
        "mixed_word()",
        "non_ws()",
        "non_wss()",
        "non_whitespace()",
        "non_whitespaces()",
        "anything()",
        "something()",
    ),
)
def test_core_keywords(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "dot(or_empty)",
        "dots(or_empty)",
        "space(or_empty)",
        "spaces(or_empty)",
        "ws(or_empty)",
        "wss(or_empty)",
        "whitespace(or_empty)",
        "whitespaces(or_empty)",
        "digit(or_empty)",
        "digits(or_empty)",
        "number(or_empty)",
        "mixed_number(or_empty)",
        "letter(or_empty)",
        "letters(or_empty)",
        "alnum(or_empty)",
        "alnums(or_empty)",
        "graph(or_empty)",
        "graphs(or_empty)",
        "punct(or_empty)",
        "puncts(or_empty)",
        "word(or_empty)",
        "mixed_word(or_empty)",
        "non_ws(or_empty)",
        "non_wss(or_empty)",
        "non_whitespace(or_empty)",
        "non_whitespaces(or_empty)",
        "anything(or_empty)",
        "something(or_empty)",
    ),
)
def test_with_or_empty_flag(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "some_dot()",
        "some_dots()",
        "some_space()",
        "some_spaces()",
        "some_ws()",
        "some_wss()",
        "some_whitespace()",
        "some_whitespaces()",
        "some_digit()",
        "some_digits()",
        "some_number()",
        "some_mixed_number()",
        "some_letter()",
        "some_letters()",
        "some_alnum()",
        "some_alnums()",
        "some_graph()",
        "some_graphs()",
        "some_punct()",
        "some_puncts()",
        "some_word()",
        "some_mixed_word()",
        "some_non_ws()",
        "some_non_wss()",
        "some_non_whitespace()",
        "some_non_whitespaces()",
    ),
)
def test_prefix_some(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "optional_dot()",
        "optional_dots()",
        "optional_space()",
        "optional_spaces()",
        "optional_ws()",
        "optional_wss()",
        "optional_whitespace()",
        "optional_whitespaces()",
        "optional_digit()",
        "optional_digits()",
        "optional_number()",
        "optional_mixed_number()",
        "optional_letter()",
        "optional_letters()",
        "optional_alnum()",
        "optional_alnums()",
        "optional_graph()",
        "optional_graphs()",
        "optional_punct()",
        "optional_puncts()",
        "optional_word()",
        "optional_mixed_word()",
        "optional_non_ws()",
        "optional_non_wss()",
        "optional_non_whitespace()",
        "optional_non_whitespaces()",
    ),
)
def test_prefix_optional(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "zero_or_one_dot()",
        "zero_or_one_dots()",
        "zero_or_one_space()",
        "zero_or_one_spaces()",
        "zero_or_one_ws()",
        "zero_or_one_wss()",
        "zero_or_one_whitespace()",
        "zero_or_one_whitespaces()",
        "zero_or_one_digit()",
        "zero_or_one_digits()",
        "zero_or_one_number()",
        "zero_or_one_mixed_number()",
        "zero_or_one_letter()",
        "zero_or_one_letters()",
        "zero_or_one_alnum()",
        "zero_or_one_alnums()",
        "zero_or_one_graph()",
        "zero_or_one_graphs()",
        "zero_or_one_punct()",
        "zero_or_one_puncts()",
        "zero_or_one_word()",
        "zero_or_one_mixed_word()",
        "zero_or_one_non_ws()",
        "zero_or_one_non_wss()",
        "zero_or_one_non_whitespace()",
        "zero_or_one_non_whitespaces()",
    ),
)
def test_prefix_zero_or_one(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "zero_or_more_dot()",
        "zero_or_more_dots()",
        "zero_or_more_space()",
        "zero_or_more_spaces()",
        "zero_or_more_ws()",
        "zero_or_more_wss()",
        "zero_or_more_whitespace()",
        "zero_or_more_whitespaces()",
        "zero_or_more_digit()",
        "zero_or_more_digits()",
        "zero_or_more_number()",
        "zero_or_more_mixed_number()",
        "zero_or_more_letter()",
        "zero_or_more_letters()",
        "zero_or_more_alnum()",
        "zero_or_more_alnums()",
        "zero_or_more_graph()",
        "zero_or_more_graphs()",
        "zero_or_more_punct()",
        "zero_or_more_puncts()",
        "zero_or_more_word()",
        "zero_or_more_mixed_word()",
        "zero_or_more_non_ws()",
        "zero_or_more_non_wss()",
        "zero_or_more_non_whitespace()",
        "zero_or_more_non_whitespaces()",
    ),
)
def test_prefix_zero_or_more(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "one_or_more_dot()",
        "one_or_more_dots()",
        "one_or_more_space()",
        "one_or_more_spaces()",
        "one_or_more_ws()",
        "one_or_more_wss()",
        "one_or_more_whitespace()",
        "one_or_more_whitespaces()",
        "one_or_more_digit()",
        "one_or_more_digits()",
        "one_or_more_number()",
        "one_or_more_mixed_number()",
        "one_or_more_letter()",
        "one_or_more_letters()",
        "one_or_more_alnum()",
        "one_or_more_alnums()",
        "one_or_more_graph()",
        "one_or_more_graphs()",
        "one_or_more_punct()",
        "one_or_more_puncts()",
        "one_or_more_word()",
        "one_or_more_mixed_word()",
        "one_or_more_non_ws()",
        "one_or_more_non_wss()",
        "one_or_more_non_whitespace()",
        "one_or_more_non_whitespaces()",
    ),
)
def test_prefix_one_or_more(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "dot_group()",
        "dots_group()",
        "space_group()",
        "spaces_group()",
        "ws_group()",
        "wss_group()",
        "whitespace_group()",
        "whitespaces_group()",
        "digit_group()",
        "digits_group()",
        "number_group()",
        "mixed_number_group()",
        "letter_group()",
        "letters_group()",
        "alnum_group()",
        "alnums_group()",
        "graph_group()",
        "graphs_group()",
        "punct_group()",
        "puncts_group()",
        "word_group()",
        "mixed_word_group()",
        "non_ws_group()",
        "non_wss_group()",
        "non_whitespace_group()",
        "non_whitespaces_group()",
    ),
)
def test_suffix_group(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        # "optional_dot_group()",            "optional_dots_group()",
        # "optional_space_group()",          "optional_spaces_group()",
        # "optional_ws_group()",             "optional_wss_group()",
        # "optional_whitespace_group()",     "optional_whitespaces_group()",
        "optional_digit_group()",
        "optional_digits_group()",
        "optional_number_group()",
        "optional_mixed_number_group()",
        "optional_letter_group()",
        "optional_letters_group()",
        "optional_alnum_group()",
        "optional_alnums_group()",
        "optional_graph_group()",
        "optional_graphs_group()",
        "optional_punct_group()",
        "optional_puncts_group()",
        "optional_word_group()",
        "optional_mixed_word_group()",
        "optional_non_ws_group()",
        "optional_non_wss_group()",
        "optional_non_whitespace_group()",
        "optional_whitespaces_group()",
    ),
)
@catch_debug_break(False)
def test_optional_group(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "3dot()",
        "3dots()",
        "3space()",
        "3spaces()",
        "3ws()",
        "3wss()",
        "3whitespace()",
        "3whitespaces()",
        "3_digit()",
        "3_digits()",
        "3_number()",
        "3_mixed_number()",
        "3_letter()",
        "3_letters()",
        "3_alnum()",
        "3_alnums()",
        "three_graph()",
        "three_graphs()",
        "three_punct()",
        "three_puncts()",
        "three_word()",
        "three_mixed_word()",
        "three_non_ws()",
        "three_non_wss()",
        "three_non_whitespace()",
        "three_non_whitespaces()",
    ),
)
def test_exact_quantity(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)


@pytest.mark.parametrize(
    "snippet",
    (
        "2_to_5_dot()",
        "2_to_5_dots()",
        "2_to_5_space()",
        "2_to_5_spaces()",
        "three_to_five_ws()",
        "three_to_five_wss()",
        "three_to_five_whitespace()",
        "three_to_five_whitespaces()",
        "3_5_digit()",
        "3_5_digits()",
        "3_5_number()",
        "3_5_mixed_number()",
        "3_5_letter()",
        "3_5_letters()",
        "3_to_n_alnum()",
        "3_to_n_alnums()",
        "_to_3_graph()",
        "_to_3_graphs()",
        "_to_3_punct()",
        "_to_3_puncts()",
        "zero_to_three_word()",
        "zero_to_three_mixed_word()",
        "zero_to_three_non_ws()",
        "zero_to_three_non_wss()",
        "zero_to_three_non_whitespace()",
        "zero_to_three_non_whitespaces()",
    ),
)
def test_quantity_range(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    checks = [bool(re.fullmatch(node.pattern, sample)) for sample in samples]
    assert checks and all(checks)
