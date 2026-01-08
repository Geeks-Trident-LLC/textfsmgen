"""
Unit tests for the `textfsmgen.gpdiff.NDiffChangedText` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gpdiff/test_ndiff_common_text_class.py
    or
    $ python -m pytest tests/unit/gpdiff/test_ndiff_common_text_class.py
"""

import pytest

from textfsmgen.gpdiff import NDiffChangedText


class TestNDiffChangedText:
    """
    Test suite for NDiffChangedText.

    Covers initialization, detection of empty changes,
    regex pattern generation, and snippet generation.
    """
    @pytest.mark.parametrize(
        "input_text, expected_name, expected_is_changed, expected_lst, expected_lst_other",
        [
            ("", "", False, [], []),
            ("-this is not a ndiff changed removed text format", "", False, [], []),
            ("+this is not a ndiff changed added text format", "", False, [], []),

            ("- removed", "ndiff_changed_text", True, ["removed"], []),
            ("+ added", "ndiff_changed_text", True, [], ["added"]),
        ],
    )
    def test_init(
        self,
        input_text,
        expected_name,
        expected_is_changed,
        expected_lst,
        expected_lst_other,
    ):
        """Test initialization and basic properties of NDiffChangedText."""
        node = NDiffChangedText(input_text)
        assert node.name == expected_name
        assert node.is_changed == expected_is_changed
        assert node.lst == expected_lst
        assert node.lst_other == expected_lst_other

    @pytest.mark.parametrize(
        "input_text, other_texts, expected_empty_changed",
        [
            ("- removed_a", [], True),
            ("- removed_a", ["+ added_a"], False),

            ("+ added_a", [], True),
            ("+ added_a", ["- removed_a"], False),
        ],
    )
    def test_is_containing_empty_changed(
        self, input_text, other_texts, expected_empty_changed
    ):
        """Test detection of empty changes when only one side of diff is present."""
        node = NDiffChangedText(input_text)
        for other in other_texts:
            node.extend(NDiffChangedText(other))
        assert node.is_containing_empty_changed == expected_empty_changed

    @pytest.mark.parametrize(
        "input_text, other_texts, kwargs, expected_pattern",
        [
            (
                "- a1",
                [],
                dict(var="v1"),
                "(?P<v1>([a-zA-Z][a-zA-Z0-9]*)|)"
            ),
            (
                "- a1",
                ["+ b2"],
                dict(var="v1"),
                "(?P<v1>[a-zA-Z][a-zA-Z0-9]*)"
            ),
            (
                "- a1",
                ["+ b2"],
                dict(var="v1", label="c"),
                "(?P<vc1>[a-zA-Z][a-zA-Z0-9]*)"
            ),

            (
                "- a1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=False),
                "(?P<v1>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)*)"
            ),
            (
                "- a1 b1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=True),
                "(?P<v1>[a-zA-Z][a-zA-Z0-9]*( +[a-zA-Z][a-zA-Z0-9]*)*)"
            ),
            (
                "- a1 b1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=False),
                "(?P<v1>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+)"
            ),
            (
                "- a1 b1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=True, is_root=True),
                r"(?P<v1>\S+( +\S+)*)"
            ),
            (
                "- a1 b1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=False, is_root=True),
                r"(?P<v1>\S+( +\S+)*)"
            ),
        ],
    )
    def test_get_pattern(self, input_text, other_texts, kwargs, expected_pattern):
        """Test regex pattern generation with different options."""
        node = NDiffChangedText(input_text)
        for other in other_texts:
            node.extend(NDiffChangedText(other))
        assert node.get_pattern(**kwargs) == expected_pattern


    @pytest.mark.parametrize(
        "input_text, other_texts, kwargs, expected_snippet",
        [
            (
                "- a1",
                [],
                dict(var="v1"),
                "word(var_v1, or_empty)"
            ),
            (
                "- a1",
                ["+ b2"],
                dict(var="v1"),
                "word(var_v1)"
            ),
            (
                "- a1",
                ["+ b2"],
                dict(var="v1", label="c"),
                "word(var_vc1)"
            ),

            (
                "- a1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=False),
                "words(var_v1)"
            ),
            (
                "- a1 b1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=True),
                "word_or_group(var_v1)"
            ),
            (
                "- a1 b1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=False),
                "phrase(var_v1)"
            ),
            (
                "- a1 b1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=True, is_root=True),
                "non_whitespaces_or_group(var_v1)"
            ),
            (
                "- a1 b1",
                ["+ c1 d1"],
                dict(var="v1", is_lessen=False, is_root=True),
                "non_whitespaces_or_group(var_v1)"
            ),
        ],
    )
    def test_get_snippet(self, input_text, other_texts, kwargs, expected_snippet):
        """Test snippet generation with different options."""
        node = NDiffChangedText(input_text)
        for other in other_texts:
            node.extend(NDiffChangedText(other))
        assert node.get_snippet(**kwargs) == expected_snippet