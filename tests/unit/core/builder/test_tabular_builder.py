import pytest
from textfsmgen.core.builder import TabularBuilder


SAMPLE_TABLE = """
Interface    Status    Speed
------------ --------- ------
Gi0/1        up        1000
Gi0/2        down      100
"""


def test_set_sample_resets_state():
    b = TabularBuilder()
    b.set_sample(SAMPLE_TABLE)
    b.build()
    assert b.template

    b.set_sample("Header1 Header2")
    assert not b.template


def test_set_sample_file(tmp_path):
    p = tmp_path / "table.txt"
    p.write_text(SAMPLE_TABLE)

    b = TabularBuilder()
    b.set_sample_file(str(p))
    b.build()

    assert "Value" in b.template


def test_build_generates_snippet():
    b = TabularBuilder()
    b.set_sample(SAMPLE_TABLE)
    b.build()

    assert b.snippet
    assert "start() mixed_word(var_interface)" in b.snippet


def test_build_generates_template():
    b = TabularBuilder()
    b.set_sample(SAMPLE_TABLE)
    b.build()

    assert "Start" in b.template


def test_truthiness():
    b = TabularBuilder()
    assert not b

    b.set_sample(SAMPLE_TABLE)
    b.build()
    assert b


def test_raises_on_parse_failure():
    b = TabularBuilder()
    b.set_sample("bad table")
    with pytest.raises(Exception):
        b.build()
