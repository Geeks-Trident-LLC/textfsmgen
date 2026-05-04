import pytest
from textfsmgen.core.patterns import VarCls


@pytest.mark.parametrize(
    "name, pattern, option, valid, exp_statement, exp_var_name",
    [
        ("", "", "", False, "", ""),
        ("digits", r"\d+", r"", True, r"Value digits (\d+)", "${digits}"),
    ],
)
def test(name, pattern, option, valid, exp_statement, exp_var_name):
    node = VarCls(name=name, pattern=pattern, option=option)
    assert bool(node) is valid
    assert node.value == exp_statement
    assert node.var_name == exp_var_name
