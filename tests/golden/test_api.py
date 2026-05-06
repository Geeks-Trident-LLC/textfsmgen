
import difflib

from textfsmgen import verify_snippet, verify_textfsm


def unified_diff(a: str, b: str):
    return "\n".join(
        difflib.unified_diff(
            a.splitlines(),
            b.splitlines(),
            fromfile="generated",
            tofile="expected",
            lineterm=""
        )
    )


def test_api(case, golden, request):    # noqa
    """
    Golden test for template generation and parsing using manifest.json.
    """
    # if golden is not enable, just run pytest
    if golden.get("case") is None:
        return

    case = golden["case"]
    manifest = golden["manifest"]
    Builder = golden["Builder"]
    sync_datetime = golden["sync_datetime"]

    canonical_sample, exp_snippet, exp_template, exp_result = golden["canonical"]

    # Build template from canonical sample
    builder = Builder(canonical_sample, **manifest.get("parameters", {}))
    assert builder, f"Builder failed to initialize for case: {case}"

    snippet = builder.snippet
    template = builder.template

    # Normalize date line
    exp_template = sync_datetime(template, exp_template)

    # ------------------------------------------------------------
    # Validate snippet
    # ------------------------------------------------------------
    if snippet.strip() != exp_snippet.strip():
        if request.config.getoption("--diff-golden"):
            print(unified_diff(snippet, exp_snippet))
        assert False, f"[{case}] Canonical snippet mismatch"

    # ------------------------------------------------------------
    # Validate template
    # ------------------------------------------------------------
    if template.strip() != exp_template.strip():
        if request.config.getoption("--diff-golden"):
            print(unified_diff(template, exp_template))
        assert False, f"[{case}] Canonical template mismatch"

    # ------------------------------------------------------------
    # Verify canonical parsing
    # ------------------------------------------------------------
    ok = verify_snippet(
        exp_snippet,
        canonical_sample,
        expected_result=exp_result,
        debug=True,
    )
    assert ok, f"[{case}] Canonical verification failed\n{ok}"

    # ------------------------------------------------------------
    # Verify all user-provided samples
    # ------------------------------------------------------------
    for input_data, expected in golden["inputs"]:
        ok = verify_textfsm(
            template,
            input_data,
            expected_result=expected,
            debug=True,
        )
        assert ok, f"[{case}] Input verification failed\n{ok}"
