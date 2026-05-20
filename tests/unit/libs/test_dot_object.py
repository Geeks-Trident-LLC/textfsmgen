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


def test_basic_dot_access():
    """DotObject should expose top-level keys as attributes."""
    data = {"a": 1, "b": "second", "c": 3.3}
    obj = DotDict(**data)

    assert obj.a == 1
    assert obj.b == "second"
    assert obj.c == 3.3


def test_nested_dot_access():
    """Nested dictionaries should be wrapped and accessible via dot notation."""
    data = {"a": 1, "b": {"c": 3.3}}
    obj = DotDict(**data)

    assert obj.a == 1
    assert obj.b == {"c": 3.3}
    assert obj.b.c == 3.3


def test_shadowed_dict_method_with_trailing_underscore():
    """Keys that shadow dict methods should be accessible via a trailing underscore."""
    data = {"update": "value from dict, not the method"}
    obj = DotDict(**data)

    assert obj.update_ == "value from dict, not the method"


def test_space_key_normalization():
    """Keys with spaces should normalize to underscore-based attribute access."""
    data = {"a b c": "a b c"}
    obj = DotDict(**data)

    assert obj.a_b_c == "a b c"


def test_dot_key_normalization():
    """Keys with dots should normalize to underscore-based attribute access."""
    data = {"a.b.c": "a.b.c"}
    obj = DotDict(**data)

    assert obj.a_b_c == "a.b.c"


def test_dash_key_normalization():
    """Keys with dashes should normalize to underscore-based attribute access."""
    data = {"a-b-c": "a-b-c"}
    obj = DotDict(**data)

    assert obj.a_b_c == "a-b-c"


def test_setattr_basic_key():
    """Setting an existing simple key via attribute should update the value."""
    data = {"a": 1}
    obj = DotDict(**data)

    assert obj.a == 1

    obj.a = 2
    assert obj.a == 2
    assert obj.get("a") == 2


def test_setattr_shadowed_method_key():
    """Keys shadowing dict methods should be settable via trailing underscore."""
    data = {"update": "value from dict, not the method"}
    obj = DotDict(**data)

    assert obj.update_ == "value from dict, not the method"

    obj.update_ = "new value for update key"
    assert obj.update_ == "new value for update key"
    assert obj.get("update") == "new value for update key"


def test_setattr_space_normalized_key():
    """Keys with spaces should be settable via underscore-normalized attributes."""
    data = {"a b c": "a b c"}
    obj = DotDict(**data)

    assert obj.a_b_c == "a b c"

    obj.a_b_c = "new value a b c"
    assert obj.a_b_c == "new value a b c"
    assert obj.get("a b c") == "new value a b c"


def test_setattr_dot_normalized_key():
    """Keys with dots should be settable via underscore-normalized attributes."""
    data = {"a.b.c": "a.b.c"}
    obj = DotDict(**data)

    assert obj.a_b_c == "a.b.c"

    obj.a_b_c = "new value a.b.c"
    assert obj.a_b_c == "new value a.b.c"
    assert obj.get("a.b.c") == "new value a.b.c"


def test_setattr_dash_normalized_key():
    """Keys with dashes should be settable via underscore-normalized attributes."""
    data = {"a-b-c": "a-b-c"}
    obj = DotDict(**data)

    assert obj.a_b_c == "a-b-c"

    obj.a_b_c = "new value a-b-c"
    assert obj.a_b_c == "new value a-b-c"
    assert obj.get("a-b-c") == "new value a-b-c"


@pytest.mark.parametrize(
    "attr",
    [
        "clear",
        "copy",
        "fromkeys",
        "get",
        "items",
        "keys",
        "pop",
        "popitem",
        "setdefault",
        "update",
        "values",
        "_valid_key",
        "_dict_members",
        "_wrap",
        "__getattr__",
        "__setattr__",
        "__delattr__",
    ],
)
def tet_raise_exception_by_overwrite_dot_object_attribute(attr):
    obj = DotDict()
    with pytest.raises(AttributeError):
        setattr(obj, attr, "Cannot overwrite DotObject attribute")
