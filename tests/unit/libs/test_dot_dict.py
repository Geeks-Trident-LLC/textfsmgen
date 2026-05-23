"""
Unit tests for the `textfsmgen.libs.generic.DotObject` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/test_dot_object.py
    or
    $ python -m pytest tests/unit/libs/test_dot_object.py
"""

import pytest
from textfsmgen.libs.generic import DotDict


# ------------------------------------------------------------
# Basic attribute access
# ------------------------------------------------------------
def test_basic_attribute_access():
    d = DotDict({"a": 1, "b": 2})
    assert d.a == 1
    assert d.b == 2
    assert d["a"] == 1
    assert d["b"] == 2


# ------------------------------------------------------------
# Nested dict wrapping
# ------------------------------------------------------------
def test_nested_dict_wrapping():
    d = DotDict({"config": {"paths": {"input": "file.txt"}}})
    assert d.config.paths.input == "file.txt"


# ------------------------------------------------------------
# Assignment after initialization
# ------------------------------------------------------------
def test_assignment_after_init():
    d = DotDict()
    d.config = {"paths": {"input": "file.txt"}}
    assert d.config.paths.input == "file.txt"


# ------------------------------------------------------------
# update() should wrap nested dicts
# ------------------------------------------------------------
def test_update_wraps_nested_dicts():
    d = DotDict()
    d.update({"config": {"paths": {"output": "result.json"}}})
    assert d.config.paths.output == "result.json"


# ------------------------------------------------------------
# List of dicts should be wrapped
# ------------------------------------------------------------
def test_list_of_dicts_wrapping():
    d = DotDict({"abc": [{"x": 1}, {"y": 2}]})

    assert d.abc[0].x == 1
    assert d.abc[1].y == 2


# ------------------------------------------------------------
# Deep nesting
# ------------------------------------------------------------
def test_deep_nesting():
    d = DotDict({
        "a": {
            "b": {
                "c": {
                    "d": 123
                }
            }
        }
    })
    assert d.a.b.c.d == 123


# ------------------------------------------------------------
# Invalid attribute names must NOT be accessible via dot notation
# ------------------------------------------------------------
def test_invalid_attribute_names():
    d = DotDict({"1": 1, "foo-bar": 2, "some value": 3})

    # Must use key access
    assert d["1"] == 1
    assert d["foo-bar"] == 2
    assert d["some value"] == 3
    # Dot access should fail
    with pytest.raises(AttributeError):
        _ = d.__getattr__("1")

    with pytest.raises(AttributeError):
        _ = d.__getattr__("foo-bar")

    with pytest.raises(AttributeError):
        _ = d.__getattr__("some value")


# ------------------------------------------------------------
# Overwriting values should preserve wrapping
# ------------------------------------------------------------
def test_overwrite_value():
    d = DotDict({"config": {"a": 1}})
    d.config = {"b": {"c": 2}}
    assert d.config.b.c == 2


# ------------------------------------------------------------
# List assignment after init should wrap
# ------------------------------------------------------------
def test_list_assignment_after_init():
    d = DotDict()
    d.items_abc = [{"a": 1}, {"b": 2}]
    assert d.items_abc[0].a == 1
    assert d.items_abc[1].b == 2
