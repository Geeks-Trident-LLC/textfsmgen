
import pytest
from pathlib import Path

from tests.integration.golden.utils import (
    iter_testcases,
    ensure_scaffold,
    sync_datetime,
    generate_meta,
    get_inputs_and_results,
    get_expected_snippet_and_templates,
    get_parameters,
    format_diff,
    json_dumps_pretty,
    validate_golden_schema
)


gold_root = Path(__file__).parent


# ---------------------------------------------------------------------------
# CLI OPTIONS
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    """
    Register golden-test CLI options.
    These appear under `pytest --help` as the "golden" group.
    """
    group = parser.getgroup("golden", "Golden test utilities")

    group.addoption(
        "--update-golden",
        action="store_true",
        help=(
            "Rewrite golden files instead of asserting. "
            "Requires --tester=<name> unless 'author' is defined in config.json."
        ),
    )

    group.addoption(
        "--tester",
        action="store",
        default="",
        help="Name of the tester approving golden updates.",
    )

    group.addoption(
        "--list-golden",
        action="store_true",
        help="List all golden test cases and exit.",
    )

    group.addoption(
        "--new-golden",
        action="store",
        default="",
        help="Scaffold a new golden test case: <kind>/<case>",
    )

    group.addoption(
        "--golden-case",
        action="store",
        default="",
        help="Run only a specific golden test case: <kind>/<case>",
    )


# ---------------------------------------------------------------------------
# SESSION START HOOKS
# ---------------------------------------------------------------------------

def pytest_sessionstart(session):
    """
    Handle --list-golden and --new-golden before test collection.
    """
    config = session.config

    # --list-golden
    if config.getoption("--list-golden"):
        print("\nGolden Test Cases:\n")
        for kind, case, _ in iter_testcases():
            print(f"  {kind}/{case}")
        print("\nDone.\n")
        pytest.exit("Listed golden test cases.")

    # --new-golden kind/case
    new_case = config.getoption("--new-golden")
    if new_case:
        try:
            kind, case = new_case.split("/", 1)
        except ValueError:
            pytest.exit("ERROR: --new-golden requires <kind>/<case>")

        case_dir = ensure_scaffold(kind, case)
        print(f"Created new golden test case scaffold at: {case_dir}")
        pytest.exit("New golden case created.")


# ---------------------------------------------------------------------------
# DISCOVERY: provide parameters to tests
# ---------------------------------------------------------------------------

def pytest_generate_tests(metafunc):
    """
    Parametrize tests that accept `golden_case`.
    """
    if "golden_case" in metafunc.fixturenames:
        cases = [(kind, case) for kind, case, _ in iter_testcases()]
        metafunc.parametrize("golden_case", cases)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def update_golden(request):
    return request.config.getoption("--update-golden")


@pytest.fixture
def tester(request):
    return request.config.getoption("--tester").strip()


# ---------------------------------------------------------------------------
# GOLDEN TEST RUNNER
# ---------------------------------------------------------------------------

@pytest.fixture
def run_golden_test(update_golden, tester):
    """
    Execute a golden test case.
    Handles snippet/template generation, verification, and updates.
    """
    def _run(kind, case):
        case_dir = ensure_scaffold(kind, case)
        validate_golden_schema(kind, case)

        parameters = get_parameters(kind, case)

        # precedence: config.json > --tester
        author = parameters.pop("author", None) or tester
        description = parameters.pop("description", "")
        notes = parameters.pop("notes", "")

        # Safety guard: prevent accidental updates
        if update_golden and not author:
            pytest.fail(
                "--update-golden requires --tester=<name> or 'author' in config.json",
                pytrace=False,
            )

        # Load expected snippet/template
        exp_snippet, exp_template, snippet_path, template_path = (
            get_expected_snippet_and_templates(kind, case)
        )

        # Iterate over all input samples
        for basename, sample, exp_result, result_path in get_inputs_and_results(kind, case):
            from textfsmgen import CategoryTemplateBuilder
            from textfsmgen.core.verify import verify_textfsm

            builder = CategoryTemplateBuilder(user_data=sample, **parameters)
            assert bool(builder), f"Failed to build template: {kind}/{case}"

            snippet = builder.snippet
            template = builder.template
            sync_exp_template = sync_datetime(template, exp_template)

            # Update mode
            if update_golden:
                snippet_path.write_text(snippet, encoding="utf-8")
                template_path.write_text(template, encoding="utf-8")
            else:
                # Assertions with colorized diffs
                assert snippet.strip() == exp_snippet.strip(), format_diff(
                    exp_snippet, snippet, f"Snippet mismatch: {kind}/{case}"
                )
                assert sync_exp_template.strip() == template.strip(), format_diff(
                    exp_template, sync_exp_template, f"Template mismatch: {kind}/{case}"
                )

            # Verify TextFSM output
            ok = verify_textfsm(template, sample, expected_result=exp_result)

            if update_golden:
                result_path.write_text(json_dumps_pretty(ok or []), encoding="utf-8")
            else:
                assert bool(ok), ok

        # Write metadata
        if update_golden:
            generate_meta(kind, case, author, description, notes)

    return _run
