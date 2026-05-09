import os

from pathlib import Path

from textfsmgen import verify_textfsm
from textfsmgen.core.data_loader import DataLoader, is_identical_templates, \
    is_identical_snippet

gold_root = Path(__file__).parent


def get_testcases(parent_path):
    for file_path in parent_path.glob("*"):
        name = file_path.name
        if (
            file_path.is_dir() and
            (not name.startswith("_") or not name.endswith("_")) and
            name[0].isalpha()
        ):
            yield str(file_path)


def run_main_case(data_info: DataLoader) -> None:
    """
    Execute a main golden test case.

    Behavior:
    - If GOLDEN_REGEN=1: regenerate canonical + expected_results and exit early.
    - Otherwise: run normal comparisons.
    """

    # -----------------------------------
    # Regeneration mode
    # -----------------------------------
    if os.getenv("GOLDEN_REGEN"):
        data_info.generate_meta()
        data_info.regenerate()
        return  # Do NOT run comparisons during regeneration

    # -----------------------------------
    # Normal test mode
    # -----------------------------------
    Builder = data_info.get_builder()
    builder = Builder(user_data=data_info.canonical_sample, **data_info.parameters)

    error = (
        f"Failed to use canonical {data_info.kind}-format sample to create TextFSM template\n"
        "====================\n"
        f"{data_info.canonical_sample}\n"
    )
    assert bool(builder), error

    # Compare snippet
    assert is_identical_snippet(
        builder.snippet,
        data_info.canonical_snippet
    ), "Canonical snippet mismatch"

    # Compare template
    assert is_identical_templates(
        builder.template, data_info.canonical_template
    ), "Canonical template mismatch"

    # Parse canonical sample
    status = verify_textfsm(
        builder.template,
        data_info.canonical_sample,
        expected_result=data_info.canonical_result
    )
    assert bool(status), status

    # Parse each input sample
    for input_sample_info, exp_result_info in data_info.get_input_and_expected_result():
        input_sample = input_sample_info["data"]
        exp_result = exp_result_info["data"]
        status = verify_textfsm(
            data_info.canonical_template,
            input_sample,
            expected_result=exp_result
        )
        assert bool(status), status

    breakpoint()
    # write meta.json
    data_info.generate_meta()

    # check drift
    data_info.check_drift()


def run_integration_case(data_info: DataLoader) -> None:
    """
    Execute an integration golden test case.

    Behavior:
    - If GOLDEN_REGEN=1: regenerate expected + expected_results and exit early.
    - Otherwise: run normal comparisons.
    """
    # -----------------------------------
    # Regeneration mode
    # -----------------------------------
    if os.getenv("GOLDEN_REGEN"):
        data_info.generate_meta()
        data_info.regenerate()
        return  # Do NOT run comparisons during regeneration

    # -----------------------------------
    # Normal test mode
    # -----------------------------------
    Builder = data_info.get_builder()

    # Use first input sample to build expected snippet/template
    first_input_info, _ = next(data_info.get_input_and_expected_result())
    first_input = first_input_info["data"]

    builder = Builder(
        user_data=first_input,
        **data_info.parameters
    )

    # Compare snippet
    assert is_identical_snippet(
        builder.snippet,
        data_info.expected_snippet
    ), "Expected snippet mismatch"

    # Compare template
    assert is_identical_templates(
        builder.template,
        data_info.expected_template
    ), "Expected template mismatch"

    for input_sample_info, exp_result_info in data_info.get_input_and_expected_result():
        input_sample = input_sample_info["data"]
        exp_result = exp_result_info["data"]
        builder = Builder(
            user_data=input_sample,
            **data_info.parameters
        )
        status = verify_textfsm(
            data_info.expected_template,
            input_sample,
            expected_result=exp_result
        )
        assert bool(status), status

    # check drift
    data_info.check_drift()


