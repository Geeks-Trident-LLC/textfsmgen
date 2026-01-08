"""
Unit tests for the `textfsmgen.gpdiff.NDiffCommonText` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gpdiff/test_ndiff_common_text_class.py
    or
    $ python -m pytest tests/unit/gpdiff/test_ndiff_common_text_class.py
"""

import pytest

from textfsmgen.gpdiff import NDiffCommonText


class TestNDiffCommonText:
    """
    Unit tests for the NDiffCommonText class.

    Covers initialization, pattern generation, and snippet generation.
    """

    @pytest.mark.parametrize(
        "input_txt, exp_name, exp_is_common, exp_lst, exp_lst_other",
        [
            ("", "", False, [], []),
            ("this is not NDiffCommonText", "", False, [], []),
            ("  unchanged_item", "ndiff_common_text", True, ["unchanged_item"], []),
        ],
    )
    def test_init(
        self, input_txt, exp_name, exp_is_common, exp_lst, exp_lst_other
    ):
        """Test initialization and basic properties."""
        node = NDiffCommonText(input_txt)
        assert node.name == exp_name
        assert node.is_common == exp_is_common
        assert node.lst == exp_lst
        assert node.lst_other == exp_lst_other

    @pytest.mark.parametrize(
        "input_txt, whitespace, exp_pattern",
        [
            ("  regular space", " ", "regular space"),
            ("  regular    space", " ", "regular +space"),
            ("  using whitespace", r"\s", r"using\swhitespace"),
            ("  using    whitespace", r"\s", r"using\s+whitespace"),
            ("  escape ** this", " ", r"escape \*{2,} this"),
            ("  escape ++   this", " ", r"escape \+{2,} +this"),
            ("  ^(?i)escape this", " ", r"\^\(\?i\)escape this"),
        ],
    )
    def test_get_pattern(self, input_txt, whitespace, exp_pattern):
        """Test regex pattern generation with different whitespace options."""
        node = NDiffCommonText(input_txt)
        assert node.get_pattern(whitespace=whitespace) == exp_pattern

    @pytest.mark.parametrize(
        "input_txt, whitespace, exp_snippet",
        [
            ("  regular space", " ", "regular space"),
            ("  regular    space", " ", "regular    space"),
            ("  using whitespace", r"\s", "using whitespace"),
            ("  using    whitespace", r"\s", "using    whitespace"),
        ],
    )
    def test_get_snippet(self, input_txt, whitespace, exp_snippet):
        """Test snippet generation with different whitespace options."""
        node = NDiffCommonText(input_txt)
        assert node.get_snippet(whitespace=whitespace) == exp_snippet
