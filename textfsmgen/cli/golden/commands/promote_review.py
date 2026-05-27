from __future__ import annotations

from pathlib import Path
import json
import shutil
import difflib
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors, validate_case_path
from ..cli_decorator import timed_command, validate_sandbox_flags
from .shared import log, short_path


@click.command(
    name="promote-review",
    help="Explain WHY an integration case cannot be promoted. Shows diffs and mismatches.",
)
@timed_command
@validate_sandbox_flags
@click.option(
    "--sandbox", is_flag=True, help="Run inside <case>.temp and delete on success."
)
@click.option(
    "--sandbox-keep", is_flag=True, help="Run inside <case>.temp and preserve it."
)
@click.option("--dry-run", is_flag=True, help="Simulate promote-review itself.")
@click.option(
    "--show-template-diff",
    is_flag=True,
    help="Show unified diff for template mismatch.",
)
@click.option(
    "--show-snippet-diff", is_flag=True, help="Show unified diff for snippet mismatch."
)
@click.option(
    "--show-result-diff", is_flag=True, help="Show unified diff for result mismatches."
)
@click.option(
    "--json", "json_output", is_flag=True, help="Output machine-readable JSON summary."
)
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("case", type=click.Path())
def cmd_promote_review(
    sandbox,
    sandbox_keep,
    dry_run,
    show_template_diff,
    show_snippet_diff,
    show_result_diff,
    json_output,
    quiet,
    verbose,
    debug,
    compact,
    case,
):
    return cmd_promote_review_(
        Path(case).resolve(),
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        show_template_diff=show_template_diff,
        show_snippet_diff=show_snippet_diff,
        show_result_diff=show_result_diff,
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )


@catch_path_errors
def cmd_promote_review_(
    case_path: Path,
    *,
    sandbox=False,
    sandbox_keep=False,
    dry_run=False,
    show_template_diff=False,
    show_snippet_diff=False,
    show_result_diff=False,
    json_output=False,
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
) -> int:

    # ------------------------------------------------------------
    # 0. Validate case path
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

    log(
        f"Loading case: {short_path(case_path)}",
        level="debug",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 1. Sandbox setup
    # ------------------------------------------------------------
    real_case_path = case_path
    case_temp = None

    if sandbox or sandbox_keep:
        case_temp = real_case_path.with_name(real_case_path.name + ".temp")

        log(
            f"[sandbox] copying case to {short_path(case_temp)}",
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
    # 2. Load case
    # ------------------------------------------------------------
    case = GoldenCase.from_path(case_path)
    loader = case.data

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
    # 3. Determine promote path
    # ------------------------------------------------------------
    parts = list(case_path.parts)
    idx = parts.index("integration")
    parts[idx] = "main"
    promote_path = Path(*parts)

    promote_conflict = promote_path.exists()
    if promote_conflict:
        log(
            f"main case already exists: {short_path(promote_path)}",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

    # ------------------------------------------------------------
    # 4. Load expected template/snippet
    # ------------------------------------------------------------
    expected = loader.load_expected()
    expected_template = expected.template.content
    expected_snippet = expected.snippet.content

    # ------------------------------------------------------------
    # 5. Canonical detection
    # ------------------------------------------------------------
    canonical_sample = None
    canonical_name = None
    template_mismatch = False
    snippet_mismatch = False

    for inp in loader.load_inputs():
        name = Path(inp.fullname).name
        sample = inp.content

        log(
            f"trying sample: {name}",
            level="verbose",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        built = loader.build(sample)

        if built.template == expected_template:
            canonical_sample = sample
            canonical_name = name
            break

    canonical_found = canonical_sample is not None

    if not canonical_found:
        log(
            "no canonical sample found — cannot promote",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

    # ------------------------------------------------------------
    # 6. Template/snippet diff (if canonical found but mismatch)
    # ------------------------------------------------------------
    if canonical_found:
        built = loader.build(canonical_sample)

        if built.template != expected_template:
            template_mismatch = True
            log(
                "template mismatch detected",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            if show_template_diff:
                diff = difflib.unified_diff(
                    expected_template.splitlines(),
                    built.template.splitlines(),
                    fromfile="expected.template",
                    tofile="built.template",
                    lineterm="",
                )
                for line in diff:
                    print(line)

        if built.snippet != expected_snippet:
            snippet_mismatch = True
            log(
                "snippet mismatch detected",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            if show_snippet_diff:
                diff = difflib.unified_diff(
                    expected_snippet.splitlines(),
                    built.snippet.splitlines(),
                    fromfile="expected.snippet",
                    tofile="built.snippet",
                    lineterm="",
                )
                for line in diff:
                    print(line)

    # ------------------------------------------------------------
    # 7. Input/result mismatches
    # ------------------------------------------------------------
    result_mismatches = []

    for inp, exp in loader.load_input_result_pairs():
        parsed = parse_textfsm_to_dicts(expected.template.content, inp.content)
        if parsed != exp.content:
            name = Path(inp.fullname).name
            result_mismatches.append(name)

            log(
                f"result mismatch for {name}",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            if show_result_diff:
                diff = difflib.unified_diff(
                    json.dumps(exp.content, indent=2).splitlines(),
                    json.dumps(parsed, indent=2).splitlines(),
                    fromfile=f"expected_results/{name}",
                    tofile=f"parsed/{name}",
                    lineterm="",
                )
                for line in diff:
                    print(line)

    # ------------------------------------------------------------
    # 8. Promotability summary
    # ------------------------------------------------------------
    promotable = (
        not promote_conflict
        and canonical_found
        and not template_mismatch
        and not snippet_mismatch
        and not result_mismatches
    )

    # ------------------------------------------------------------
    # 9. JSON output
    # ------------------------------------------------------------
    if json_output:
        summary = {
            "case": short_path(case_path),
            "promote_path": short_path(promote_path),
            "promotable": promotable,
            "canonical_found": canonical_found,
            "canonical_sample": canonical_name,
            "template_mismatch": template_mismatch,
            "snippet_mismatch": snippet_mismatch,
            "result_mismatches": result_mismatches,
            "promote_conflict": promote_conflict,
        }
        print(json.dumps(summary, indent=2))
        return 0 if promotable else 1

    # ------------------------------------------------------------
    # 10. Dry-run
    # ------------------------------------------------------------
    if dry_run:
        print("[PROMOTE-REVIEW] DRY-RUN")
        print(f"  case:          {short_path(case_path)}")
        print(f"  promote-path:  {short_path(promote_path)}")
        print(f"  promotable:    {promotable}")
        print(f"  canonical:     {canonical_name}")
        print(f"  template mismatch: {template_mismatch}")
        print(f"  snippet mismatch:  {snippet_mismatch}")
        print(f"  result mismatches: {result_mismatches}")
        print("[DRY-RUN] promote-review simulation completed.")
        return 0 if promotable else 1

    # ------------------------------------------------------------
    # 11. Compact summary
    # ------------------------------------------------------------
    if compact:
        print(f"[PROMOTE-REVIEW] {short_path(case_path)} promotable={promotable}")
        return 0 if promotable else 1

    # ------------------------------------------------------------
    # 12. Normal output
    # ------------------------------------------------------------
    click.echo(
        f"[PROMOTE-REVIEW]\n"
        f"  source:            {short_path(case_path)}\n"
        f"  promote-path:      {short_path(promote_path)}\n"
        f"  canonical:         {canonical_name}\n"
        f"  promotable:        {promotable}\n"
        f"  template mismatch: {template_mismatch}\n"
        f"  snippet mismatch:  {snippet_mismatch}\n"
        f"  result mismatches: {result_mismatches}\n",
    )

    # ------------------------------------------------------------
    # 13. Sandbox cleanup
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

    return 0 if promotable else 1
