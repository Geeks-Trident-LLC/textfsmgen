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
@click.option("--all", "diff_all", is_flag=True, help="Diff everything (default).")
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
    diff_all,
    json_output,
    quiet,
    verbose,
    debug,
    compact,
    case,
):
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

    # ------------------------------------------------------------
    # 0. Validate integration case
    # ------------------------------------------------------------
    ok = validate_case_path(case_path)
    if not ok:
        log(
            f"{ok}",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 1

    case = GoldenCase.from_path(case_path)
    if not case.is_integration():
        log(
            f"{short_path(case_path)} is not an integration case",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 1

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
        log(
            f"main case does not exist: {short_path(main_path)}",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 1

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

    if sandbox or sandbox_keep:
        case_temp = real_case_path.with_name(real_case_path.name + ".temp")

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
    if not any([diff_template, diff_snippet, diff_results, diff_inputs, diff_manifest]):
        diff_all = True

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
            log(
                "template mismatch",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            for line in unified(
                integ_t,
                main_t,
                "integration/expected/textfsm.template",
                "main/canonical/textfsm.template",
            ):
                print(line)

    # ------------------------------------------------------------
    # 7. Snippet diff
    # ------------------------------------------------------------
    if do_snippet:
        integ_s = integ.load_expected().snippet.content
        main_s = main.load_canonical().snippet.content

        if integ_s != main_s:
            diffs["snippet"] = True
            log(
                "snippet mismatch",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            for line in unified(
                integ_s,
                main_s,
                "integration/expected/snippet.txt",
                "main/canonical/snippet.txt",
            ):
                print(line)

    # ------------------------------------------------------------
    # 8. Expected results diff
    # ------------------------------------------------------------
    if do_results:
        for inp, exp in integ.load_input_result_pairs():
            name = Path(inp.fullname).name

            # Find matching expected_result in main case
            main_expected_result = None
            for main_res in main.load_expected_results():
                if Path(main_res.fullname).name == Path(exp.fullname).name:
                    main_expected_result = main_res.content
                    break

            if main_expected_result is None:
                log(
                    f"missing expected_result in main case: {name}",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )
                diffs["results"].append(name)
                continue

            integ_json = json.dumps(exp.content, indent=2)
            main_json = json.dumps(main_expected_result, indent=2)

            if integ_json != main_json:
                diffs["results"].append(name)
                log(
                    f"result mismatch: {name}",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )

                for line in unified(
                    integ_json,
                    main_json,
                    f"integration/expected_results/{name}",
                    f"main/expected_results/{name}",
                ):
                    print(line)

    # ------------------------------------------------------------
    # 9. Inputs diff
    # ------------------------------------------------------------
    if do_inputs:
        for inp in integ.load_inputs():
            name = Path(inp.fullname).name

            # Find matching input in main case
            main_input = None
            for m_inp in main.load_inputs():
                if Path(m_inp.fullname).name == name:
                    main_input = m_inp.content
                    break

            if main_input is None:
                diffs["inputs"].append(name)
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
                diffs["inputs"].append(name)
                log(
                    f"input mismatch: {name}",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )

                for line in unified(
                    integ_text,
                    main_text,
                    f"integration/inputs/{name}",
                    f"main/inputs/{name}",
                ):
                    print(line)

    # ------------------------------------------------------------
    # 10. Manifest diff
    # ------------------------------------------------------------
    if do_manifest:
        integ_m = json.dumps(integ.load_manifest(), indent=2)
        main_m = json.dumps(main.load_manifest(), indent=2)

        if integ_m != main_m:
            diffs["manifest"] = True
            log(
                "manifest mismatch",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            for line in unified(
                integ_m,
                main_m,
                "integration/manifest.json",
                "main/manifest.json",
            ):
                print(line)

    # ------------------------------------------------------------
    # 11. JSON output
    # ------------------------------------------------------------
    if json_output:
        print(json.dumps(diffs, indent=2))
        return (
            0
            if not any(
                [
                    diffs["template"],
                    diffs["snippet"],
                    diffs["manifest"],
                    diffs["results"],
                    diffs["inputs"],
                ]
            )
            else 1
        )

    # ------------------------------------------------------------
    # 12. Compact summary
    # ------------------------------------------------------------
    if compact:
        diff_count = (
            int(diffs["template"])
            + int(diffs["snippet"])
            + int(diffs["manifest"])
            + len(diffs["results"])
            + len(diffs["inputs"])
        )
        print(f"[PROMOTE-DIFF] {short_path(case_path)} diffs={diff_count}")
        return 0 if diff_count == 0 else 1

    # ------------------------------------------------------------
    # 13. Normal summary
    # ------------------------------------------------------------
    print("[PROMOTE-DIFF]")
    print(f"  source:     {short_path(case_path)}")
    print(f"  main:       {short_path(main_path)}")
    print(f"  template:   {diffs['template']}")
    print(f"  snippet:    {diffs['snippet']}")
    print(f"  manifest:   {diffs['manifest']}")
    print(f"  results:    {diffs['results']}")
    print(f"  inputs:     {diffs['inputs']}")

    # ------------------------------------------------------------
    # 14. Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        shutil.rmtree(case_temp)
        log(
            "[sandbox] cleaned up sandbox directory",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

    # ------------------------------------------------------------
    # 15. Exit code
    # ------------------------------------------------------------
    has_diff = any(
        [
            diffs["template"],
            diffs["snippet"],
            diffs["manifest"],
            diffs["results"],
            diffs["inputs"],
        ]
    )
    return 0 if not has_diff else 1
