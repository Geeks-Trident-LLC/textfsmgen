from textfsmgen.core.builder import FreeFormBuilder


SIMPLE_SNIPPET = """
Interface: mixed_word(var_INTERFACE)
Status: mixed_word(var_STATUS)
"""

SAMPLE = """
Interface: Gi0/1
Status: On
"""

NO_VARIABLE_SNIPPET = """
Interface: Gi0/1
"""


def test_set_snippet_resets_state():
    b = FreeFormBuilder()
    b.set_snippet(SIMPLE_SNIPPET)
    b.build()
    assert b.variables

    b.set_snippet("Value X (.*)")
    assert not b.variables
    assert not b.template


def test_set_snippet_file(tmp_path):
    p = tmp_path / "snippet.txt"
    p.write_text(SIMPLE_SNIPPET)

    b = FreeFormBuilder()
    b.set_snippet_file(str(p))
    b.build()

    assert "INTERFACE" in b.template


def test_build_extracts_variables():
    b = FreeFormBuilder()
    b.set_snippet(SIMPLE_SNIPPET)
    b.build()

    names = [v.name for v in b.variables]
    assert "INTERFACE" in names
    assert "STATUS" in names


def test_build_generates_template():
    b = FreeFormBuilder()
    b.set_snippet(SIMPLE_SNIPPET)
    b.build()

    assert "Start" in b.template
    assert "Value INTERFACE" in b.template


def test_build_validates_template():
    b = FreeFormBuilder()
    b.set_snippet(SIMPLE_SNIPPET)
    b.set_sample(SAMPLE)
    b.build()
    assert bool(b.result)


def test_build_raises_without_variables():
    b = FreeFormBuilder()
    b.set_snippet(NO_VARIABLE_SNIPPET)
    b.build()
    assert "Snippet does not contain any variable definitions" in b.warning


def test_truthiness():
    b = FreeFormBuilder()
    assert not b

    b.set_snippet(SIMPLE_SNIPPET)
    b.build()
    assert b


def test_parsing_failure_warning():
    b = FreeFormBuilder()
    b.set_snippet("Value {{ key }}")
    b.set_sample("this will not match")
    b.build()
    assert "Snippet does not contain any variable definitions" in b.warning
