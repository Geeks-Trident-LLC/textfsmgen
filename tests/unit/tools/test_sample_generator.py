

import pytest
import re
from textfsmgen.tools.samples import SamplesGenerator



@pytest.mark.parametrize(
    "snippet",
    (
        "dot()",                "dots()",

        "space()",              "spaces()",
        "ws()",                 "wss()",
        "whitespace()",         "whitespaces()",

        "digit()",              "digits()",
        "number()",               "mixed_number()",

        "letter()",             "letters()",
        "alnum()",              "alnums()",
        "graph()",              "graphs()",
        "punct()",              "puncts()",

        "word()",               "mixed_word()",
        "non_ws()",             "non_wss()",
        "non_whitespace()",     "non_whitespaces()",
        "anything()",           "something()",
    )
)
def test_core_keywords(snippet):
    node = SamplesGenerator(snippet)
    assert bool(node) is True
    samples = node.generate()
    for sample in samples:
        assert re.fullmatch(node.pattern, sample)
