from textfsmgen.core.builder import BuilderBase


def test_build_result(fake_builder):
    result = fake_builder().to_result()
    assert hasattr(result, "snippet")
    assert hasattr(result, "template")
    assert hasattr(result, "result")
    assert hasattr(result, "warning")


def test_builder_base():
    base_builder = BuilderBase()
    assert hasattr(base_builder, "sample")
    assert hasattr(base_builder, "snippet")
    assert hasattr(base_builder, "template")
    assert hasattr(base_builder, "result")
    assert hasattr(base_builder, "warning")