from __future__ import annotations

from pathlib import Path
import json
import difflib
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors, validate_case_path
from ..cli_decorator import timed_command
from .shared import log, short_path


@click.command(
    name="promote-verify",
    help="Verify that a MAIN golden test case is still valid. No writes, no sandbox.",
)
@timed_command
@click.option(
    "--json", "json_output", is_flag=True, help="Output machine-readable JSON summary."
)
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("case", type=click.Path())
def cmd_promote_verify(
    json_output,
    quiet,
    verbose,
    debug,
    compact,
    case,
):
    return cmd_promote_verify_(
        Path(case).resolve(),
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )


@catch_path_errors
def cmd_promote_verify_(
    case_path: Path,
    *,
    json_output=False,
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
) -> int:

    json_events = []

    def record_fail(message: str, diff_lines: list[str] | None = None):  # noqa
        json_events.append(
            {
                "status": "fail",
                "message": message,
                "diff": diff_lines if diff_lines is not None else [],
            }
        )

    # ------------------------------------------------------------
    # 0. Validate main case
    # ------------------------------------------------------------
    ok = validate_case_path(case_path)
    if not ok:
        record_fail(str(ok))
        if json_output:
            print(json.dumps({"events": json_events}, indent=2))
        return 1

    case = GoldenCase.from_path(case_path)
    if not case.is_main():
        record_fail("not a main case")
        if json_output:
            print(json.dumps({"events": json_events}, indent=2))
        return 1

    if not json_output:
        log(
            f"{short_path(case_path)} — main case",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

    # ------------------------------------------------------------
    # 1. Load canonical template + snippet
    # ------------------------------------------------------------
    canonical = case.data.load_canonical()
    template_text = canonical.template.content

    # ------------------------------------------------------------
    # 2. Load inputs + expected_results
    # ------------------------------------------------------------
    inputs = case.data.load_inputs()
    expected_results = case.data.load_expected_results()

    # Build mapping: expected_result filename → JSON content
    expected_map = {Path(er.fullname).name: er.content for er in expected_results}

    # ------------------------------------------------------------
    # 3. Verify each input
    # ------------------------------------------------------------
    mismatches = []
    missing = []

    for inp in inputs:
        base = Path(inp.fullname).stem
        exp_name = f"{base}_result.json"
        text = inp.content

        # Check expected_result exists
        if exp_name not in expected_map:
            missing.append(exp_name)
            record_fail(f"missing expected_result: {exp_name}", diff_lines=[])
            if not json_output:
                log(
                    f"missing expected_result: {exp_name}",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )
            continue

        expected_json = json.dumps(expected_map[exp_name], indent=2)

        # Parse using canonical template
        parsed = parse_textfsm_to_dicts(template_text, text)
        parsed_json = json.dumps(parsed, indent=2)

        if parsed_json != expected_json:
            mismatches.append(exp_name)
            diff_lines = list(
                difflib.unified_diff(
                    expected_json.splitlines(),
                    parsed_json.splitlines(),
                    fromfile=f"main/expected_results/{exp_name}",
                    tofile=f"main/parsed/{exp_name}",
                    lineterm="",
                )
            )
            record_fail(f"result mismatch: {exp_name}", diff_lines)

            if not json_output:
                log(
                    f"result mismatch: {exp_name}",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )
                for line in diff_lines:
                    print(line)

    # ------------------------------------------------------------
    # 4. Build summary
    # ------------------------------------------------------------
    total_diffs = len(missing) + len(mismatches)

    json_summary = {
        "missing": missing,
        "mismatches": mismatches,
        "total_diffs": total_diffs,
    }

    # ------------------------------------------------------------
    # 5. JSON output
    # ------------------------------------------------------------
    if json_output:
        output = {
            "case": str(case_path),
            "events": json_events,
            "summary": json_summary,
        }
        print(json.dumps(output, indent=2))
        return 0 if total_diffs == 0 else 1

    # ------------------------------------------------------------
    # 6. Compact summary
    # ------------------------------------------------------------
    if compact:
        print(f"[PROMOTE-VERIFY] {short_path(case_path)} diffs={total_diffs}")
        return 0 if total_diffs == 0 else 1

    # ------------------------------------------------------------
    # 7. Human summary
    # ------------------------------------------------------------
    print("[PROMOTE-VERIFY]")
    print(f"  case:        {short_path(case_path)}")
    print(f"  missing:     {len(missing)}")
    print(f"  mismatches:  {len(mismatches)}")
    print(f"  total diffs: {total_diffs}")

    return 0 if total_diffs == 0 else 1
