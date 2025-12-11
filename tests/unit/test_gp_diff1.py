import pytest           # noqa

from textfsmgenerator.gpdiff import DiffLinePattern


def test_generated_snippet1():
    lines = [
        '12345 | ttys000  |  0:00.55 | /bin/zsh --login -i',
        ' 3344 | ttys001  |  0:01.23 | -zsh'
    ]
    expected_snippet = 'start(space) digits(var_v0) | word(var_v1)  |  mixed_number(var_v2) | mixed_words(var_v3) end()'
    node = DiffLinePattern(*lines)
    snippet = node.snippet
    assert snippet == expected_snippet


def test_generated_snippet2():
    lines = [
        'this \t is a pen',
        'this is the yellow pen',
    ]
    expected_snippet = 'start() this\t is words(var_v0) pen end()'
    node = DiffLinePattern(*lines)
    snippet = node.snippet
    assert snippet == expected_snippet


def test_generated_snippet3():
    lines = [
        'ipv6_addr: a::b % 16',
        'ipv6_addr: a::c % 32',
    ]
    expected_snippet = 'start() ipv6_addr: mixed_word(var_v0) % digits(var_v1) end()'
    node = DiffLinePattern(*lines)
    snippet = node.snippet
    assert snippet == expected_snippet


def test_generated_snippet4():
    lines = [
        'ipv6_addr: 1::2 % 32',
        'ipv6_addr: 1::3 / 33',
    ]
    expected_snippet = 'start() ipv6_addr: non_whitespaces_phrase(var_v0) end()'
    node = DiffLinePattern(*lines)
    snippet = node.snippet
    assert snippet == expected_snippet


def test_generated_snippet5():
    lines = [
        'this is yellow half \t pencil',
        'this is red half pencil',
        'this is green half pencil',
        'this is half pencil',
    ]
    expected_snippet = 'start() this is letters(var_v0, or_empty) half\t pencil end()'
    node = DiffLinePattern(*lines)
    snippet = node.snippet
    assert snippet == expected_snippet


def test_generated_pattern1():
    lines = [
        'this \t is a pen',
        'this is the yellow pen',
    ]
    expected_pattern = 'this\\s+is (?P<v0>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)*) pen'
    node = DiffLinePattern(*lines)
    pattern = node.pattern
    assert pattern == expected_pattern
