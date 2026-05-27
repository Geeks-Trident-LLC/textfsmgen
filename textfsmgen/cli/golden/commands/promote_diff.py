from __future__ import annotations

from pathlib import Path
import json
import shutil
import difflib
import click


from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors, validate_case_path
from ..cli_decorator import timed_command, validate_sandbox_flags
from .shared import log, short_path


@click.command(
    name="promote-diff",
    help="Compare an integration case with its promoted main case. Shows unified diffs.",
)
@timed_command
@validate_sandbox_flags
@click.option(
    "--sandbox", is_flag=True, help="Run inside <case>.temp and delete on success."
)
@click.option(
    "--sandbox-keep", is_flag=True, help="Run inside <case>.temp and preserve it."
)
@click.option("--dry-run", is_flag=True, help="Simulate promote-diff itself.")
@click.option("--template", "diff_template", is_flag=True, help="Diff template only.")
@click.option("--snippet", "diff_snippet", is_flag=True, help="Diff snippet only.")
@click.option(
    "--results", "diff_results", is_flag=True, help="Diff expected_results only."
)
@click.option("--inputs", "diff_inputs", is_flag=True, help="Diff inputs only.")
@click.option(
    "--manifest", "diff_manifest", is_flag=True, help="Diff manifest.json only."
)
@click.option(
    "--json", "json_output", is_flag=True, help="Output machine-readable JSON summary."
)
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("case", type=click.Path())
def cmd_promote_diff(
    sandbox,
    sandbox_keep,
    dry_run,
    diff_template,
    diff_snippet,
    diff_results,
    diff_inputs,
    diff_manifest,
    json_output,
    quiet,
    verbose,
    debug,
    compact,
    case,
):
    diff_all = not (
        diff_template or diff_snippet or diff_results or diff_inputs or diff_manifest
    )

    return cmd_promote_diff_(
        Path(case).resolve(),
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        diff_template=diff_template,
        diff_snippet=diff_snippet,
        diff_results=diff_results,
        diff_inputs=diff_inputs,
        diff_manifest=diff_manifest,
        diff_all=diff_all,
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )


@catch_path_errors
def cmd_promote_diff_(
    case_path: Path,
    *,
    sandbox=False,
    sandbox_keep=False,
    dry_run=False,
    diff_template=False,
    diff_snippet=False,
    diff_results=False,
    diff_inputs=False,
    diff_manifest=False,
    diff_all=False,
    json_output=False,
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
) -> int:

    json_events = []
    json_summary = {}

    def record_fail(message: str, diff_lines: list[str] | None = None):
        json_events.append(
            {
                "status": "fail",
                "message": message,
                "diff": diff_lines if diff_lines is not None else [],
            }
        )

    # ------------------------------------------------------------
    # 0. Validate integration case
    # ------------------------------------------------------------
    ok = validate_case_path(case_path)
    if not ok:
        record_fail(str(ok))
        if json_output:
            print(json.dumps({"events": json_events}, indent=2))
        return 1

    case = GoldenCase.from_path(case_path)
    if not case.is_integration():
        record_fail("not an integration case")
        if json_output:
            print(json.dumps({"events": json_events}, indent=2))
        return 1

    if not json_output:
        log(
            f"{short_path(case_path)} — integration case",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

    # ------------------------------------------------------------
    # 1. Determine main case path
    # ------------------------------------------------------------
    parts = list(case_path.parts)
    idx = parts.index("integration")
    parts[idx] = "main"
    main_path = Path(*parts)

    if not main_path.exists():
        record_fail(f"main case does not exist: {main_path}")
        if json_output:
            print(json.dumps({"events": json_events}, indent=2))
        return 1

    if not json_output:
        log(
            f"main case: {short_path(main_path)}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

    # ------------------------------------------------------------
    # 2. Sandbox setup
    # ------------------------------------------------------------
    real_case_path = case_path
    case_temp = None
    sandbox_info = {"enabled": False, "path": None, "kept": False}

    if sandbox or sandbox_keep:
        sandbox_info["enabled"] = True
        case_temp = real_case_path.with_name(real_case_path.name + ".temp")
        sandbox_info["path"] = str(case_temp)

        if not json_output:
            log(
                f"[sandbox] copying integration case to {short_path(case_temp)}",
                level="sandbox",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

        if case_temp.exists():
            shutil.rmtree(case_temp)

        shutil.copytree(real_case_path, case_temp)
        case_path = case_temp

    # ------------------------------------------------------------
    # 3. Load integration + main cases
    # ------------------------------------------------------------
    integ = GoldenCase.from_path(case_path).data
    main = GoldenCase.from_path(main_path).data

    # ------------------------------------------------------------
    # 4. Determine diff scope
    # ------------------------------------------------------------
    do_template = diff_all or diff_template
    do_snippet = diff_all or diff_snippet
    do_results = diff_all or diff_results
    do_inputs = diff_all or diff_inputs
    do_manifest = diff_all or diff_manifest

    # ------------------------------------------------------------
    # 5. Diff helpers
    # ------------------------------------------------------------
    def unified(a: str, b: str, fromfile: str, tofile: str):
        return list(
            difflib.unified_diff(
                a.splitlines(),
                b.splitlines(),
                fromfile=fromfile,
                tofile=tofile,
                lineterm="",
            )
        )

    diffs = {
        "template": False,
        "snippet": False,
        "results": [],
        "inputs": [],
        "manifest": False,
    }

    # ------------------------------------------------------------
    # 6. Template diff
    # ------------------------------------------------------------
    if do_template:
        integ_t = integ.load_expected().template.content
        main_t = main.load_canonical().template.content

        if integ_t != main_t:
            diffs["template"] = True
            diff_lines = unified(
                integ_t,
                main_t,
                "integration/expected/textfsm.template",
                "main/canonical/textfsm.template",
            )
            record_fail("template mismatch", diff_lines)

            if not json_output:
                log(
                    "template mismatch",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )
                for line in diff_lines:
                    print(line)

    # ------------------------------------------------------------
    # 7. Snippet diff
    # ------------------------------------------------------------
    if do_snippet:
        integ_s = integ.load_expected().snippet.content
        main_s = main.load_canonical().snippet.content

        if integ_s != main_s:
            diffs["snippet"] = True
            diff_lines = unified(
                integ_s,
                main_s,
                "integration/expected/snippet.txt",
                "main/canonical/snippet.txt",
            )
            record_fail("snippet mismatch", diff_lines)

            if not json_output:
                log(
                    "snippet mismatch",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )
                for line in diff_lines:
                    print(line)

    # ------------------------------------------------------------
    # 8. Expected results diff
    # ------------------------------------------------------------
    if do_results:
        mismatches = []
        for inp, exp in integ.load_input_result_pairs():
            name = Path(inp.fullname).name

            main_expected_result = None
            for main_res in main.load_expected_results():
                if Path(main_res.fullname).name == Path(exp.fullname).name:
                    main_expected_result = main_res.content
                    break

            if main_expected_result is None:
                mismatches.append(name)
                record_fail(f"missing expected_result: {name}", diff_lines=[])
                if not json_output:
                    log(
                        f"missing expected_result in main case: {name}",
                        level="FAIL",
                        quiet=quiet,
                        verbose=verbose,
                        debug=debug,
                        compact=compact,
                    )
                continue

            integ_json = json.dumps(exp.content, indent=2)
            main_json = json.dumps(main_expected_result, indent=2)

            if integ_json != main_json:
                mismatches.append(name)
                diff_lines = unified(
                    integ_json,
                    main_json,
                    f"integration/expected_results/{name}",
                    f"main/expected_results/{name}",
                )
                record_fail(f"result mismatch: {name}", diff_lines)

                if not json_output:
                    log(
                        f"result mismatch: {name}",
                        level="FAIL",
                        quiet=quiet,
                        verbose=verbose,
                        debug=debug,
                        compact=compact,
                    )
                    for line in diff_lines:
                        print(line)

        diffs["results"] = mismatches

    # ------------------------------------------------------------
    # 9. Inputs diff
    # ------------------------------------------------------------
    if do_inputs:
        mismatches = []
        for inp in integ.load_inputs():
            name = Path(inp.fullname).name

            main_input = None
            for m_inp in main.load_inputs():
                if Path(m_inp.fullname).name == name:
                    main_input = m_inp.content
                    break

            if main_input is None:
                mismatches.append(name)
                record_fail(f"missing input: {name}", diff_lines=[])
                if not json_output:
                    log(
                        f"missing input in main case: {name}",
                        level="FAIL",
                        quiet=quiet,
                        verbose=verbose,
                        debug=debug,
                        compact=compact,
                    )
                continue

            integ_text = inp.content
            main_text = main_input

            if integ_text != main_text:
                mismatches.append(name)
                diff_lines = unified(
                    integ_text,
                    main_text,
                    f"integration/inputs/{name}",
                    f"main/inputs/{name}",
                )
                record_fail(f"input mismatch: {name}", diff_lines)

                if not json_output:
                    log(
                        f"input mismatch: {name}",
                        level="FAIL",
                        quiet=quiet,
                        verbose=verbose,
                        debug=debug,
                        compact=compact,
                    )
                    for line in diff_lines:
                        print(line)

        diffs["inputs"] = mismatches

    # ------------------------------------------------------------
    # 10. Manifest diff
    # ------------------------------------------------------------
    if do_manifest:
        integ_m = json.dumps(integ.load_manifest(), indent=2)
        main_m = json.dumps(main.load_manifest(), indent=2)

        if integ_m != main_m:
            diffs["manifest"] = True
            diff_lines = unified(
                integ_m,
                main_m,
                "integration/manifest.json",
                "main/manifest.json",
            )
            record_fail("manifest mismatch", diff_lines)

            if not json_output:
                log(
                    "manifest mismatch",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )
                for line in diff_lines:
                    print(line)

    # ------------------------------------------------------------
    # 11. Build summary
    # ------------------------------------------------------------
    def status(value):
        if value is False or value == []:
            return "identical"
        if value is True:
            return "diff"
        if isinstance(value, list):
            return f"diff ({len(value)})"
        return "diff"

    json_summary = {
        "template": status(diffs["template"]),
        "snippet": status(diffs["snippet"]),
        "manifest": status(diffs["manifest"]),
        "results": status(diffs["results"]),
        "inputs": status(diffs["inputs"]),
        "total_diffs": (
            int(diffs["template"])
            + int(diffs["snippet"])
            + int(diffs["manifest"])
            + len(diffs["results"])
            + len(diffs["inputs"])
        ),
    }

    # ------------------------------------------------------------
    # 12. JSON output
    # ------------------------------------------------------------
    if json_output:
        output = {
            "case": str(case_path),
            "main_case": str(main_path),
            "sandbox": sandbox_info,
            "events": json_events,
            "summary": json_summary,
        }
        print(json.dumps(output, indent=2))
        has_diff = json_summary["total_diffs"] > 0
        return 0 if not has_diff else 1

    # ------------------------------------------------------------
    # 13. Compact summary
    # ------------------------------------------------------------
    if compact:
        print(
            f"[PROMOTE-DIFF] {short_path(case_path)} diffs={json_summary['total_diffs']}"
        )
        return 0 if json_summary["total_diffs"] == 0 else 1

    # ------------------------------------------------------------
    # 14. Human summary
    # ------------------------------------------------------------
    print("[PROMOTE-DIFF]")
    print(f"  source:     {short_path(case_path)}")
    print(f"  main:       {short_path(main_path)}")
    print(f"  template:   {json_summary['template']}")
    print(f"  snippet:    {json_summary['snippet']}")
    print(f"  manifest:   {json_summary['manifest']}")
    print(f"  results:    {json_summary['results']}")
    print(f"  inputs:     {json_summary['inputs']}")

    # ------------------------------------------------------------
    # 15. Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        shutil.rmtree(case_temp)
        sandbox_info["kept"] = False

        if not json_output:
            log(
                "[sandbox] cleaned up sandbox directory",
                level="sandbox",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

    if sandbox_keep:
        sandbox_info["kept"] = True

    # ------------------------------------------------------------
    # 16. Exit code
    # ------------------------------------------------------------
    return 0 if json_summary["total_diffs"] == 0 else 1
