from __future__ import annotations

from pathlib import Path
import json
import click


from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command
from .shared import log, short_path, canonical_json


# ======================================================================
# Helpers
# ======================================================================


def diff_cases(case_a: GoldenCase, case_b: GoldenCase):
    """
    Return a list of human-readable reasons why two cases differ.
    """
    diffs = []

    exp_a = case_a.data.load_expected()
    exp_b = case_b.data.load_expected()

    # Template
    if exp_a.template.content != exp_b.template.content:
        diffs.append("template differs")

    # Snippet
    if exp_a.snippet.content != exp_b.snippet.content:
        diffs.append("snippet differs")

    # Inputs
    inputs_a = sorted(
        (Path(i.fullname).name, i.content) for i in case_a.data.load_inputs()
    )
    inputs_b = sorted(
        (Path(i.fullname).name, i.content) for i in case_b.data.load_inputs()
    )
    if inputs_a != inputs_b:
        diffs.append("inputs differ")

    # Expected results
    results_a = sorted(
        (Path(e.fullname).name, canonical_json(e.content))
        for _, e in case_a.data.load_input_result_pairs()
    )
    results_b = sorted(
        (Path(e.fullname).name, canonical_json(e.content))
        for _, e in case_b.data.load_input_result_pairs()
    )
    if results_a != results_b:
        diffs.append("expected_results differ")

    return diffs


# ======================================================================
# CLI ENTRYPOINT
# ======================================================================


@click.command(
    name="identical",
    help="Identify integration cases that are completely identical (template, snippet, inputs, expected_results).",
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.option("--summary", is_flag=True, help="Show summary of identical groups.")
@click.option(
    "--json", "json_output", is_flag=True, help="Output machine-readable JSON."
)
@click.option(
    "--diff", "show_diff", is_flag=True, help="Show why cases are NOT identical."
)
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_identical(
    srcs, quiet, verbose, debug, compact, summary, json_output, show_diff
):
    if json_output:
        quiet = True
        verbose = False
        debug = False
        compact = False

    return cmd_identical_(
        src_paths=[Path(s).resolve() for s in srcs],
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
        summary=summary,
        json_output=json_output,
        show_diff=show_diff,
    )


# ======================================================================
# MAIN IMPLEMENTATION
# ======================================================================


def cmd_identical_(
    src_paths,
    *,
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
    summary=False,
    json_output=False,
    show_diff=False,
):
    if not src_paths:
        raise click.ClickException("No source cases provided.")

    # ------------------------------------------------------------
    # 1. Load + validate cases
    # ------------------------------------------------------------
    cases = []
    validation_failures = []

    for p in src_paths:
        log(
            f"validating src: {short_path(p)}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        c = GoldenCase.from_path(p)

        if not c.is_integration():
            validation_failures.append(f"{short_path(p)} is not an integration case")
            continue

        try:
            c.tested()
        except Exception as e:
            validation_failures.append(f"{short_path(p)} is not tested:\n{e}")
            continue

        log(
            f"{short_path(p)} — tested and valid",
            level="OK",
            indent=2,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        cases.append(c)

    if validation_failures:
        for msg in validation_failures:
            log(
                msg,
                level="FAIL",
                quiet=False,
                verbose=True,
                debug=debug,
                compact=compact,
            )
        return 1

    # ------------------------------------------------------------
    # 2. Build canonical signatures
    # ------------------------------------------------------------
    signatures = {}  # signature → list[GoldenCase]

    for c in cases:
        expected = c.data.load_expected()

        template = expected.template.content
        snippet = expected.snippet.content

        inputs = sorted(
            (Path(i.fullname).name, i.content) for i in c.data.load_inputs()
        )

        results = sorted(
            (Path(e.fullname).name, canonical_json(e.content))
            for _, e in c.data.load_input_result_pairs()
        )

        signature = (
            template,
            snippet,
            tuple(inputs),
            tuple(results),
        )

        signatures.setdefault(signature, []).append(c)

    # ------------------------------------------------------------
    # 3. Collect identical groups
    # ------------------------------------------------------------
    groups = [group for group in signatures.values() if len(group) > 1]

    # ------------------------------------------------------------
    # 4. JSON output
    # ------------------------------------------------------------
    if json_output:
        out = {
            "groups": [[short_path(c.case_dir) for c in group] for group in groups],
            "non_identical": {},
        }

        if show_diff:
            for a in cases:
                for b in cases:
                    if a is b:
                        continue
                    diffs = diff_cases(a, b)
                    if diffs:
                        out["non_identical"][
                            f"{short_path(a.case_dir)} vs {short_path(b.case_dir)}"
                        ] = diffs

        print(json.dumps(out, indent=2))
        return 0

    # ------------------------------------------------------------
    # 5. Compact mode
    # ------------------------------------------------------------
    if compact:
        print(f"[IDENTICAL] Groups: {len(groups)}")
        return 0

    # ------------------------------------------------------------
    # 6. Summary mode
    # ------------------------------------------------------------
    if summary:
        print("===== IDENTICAL SUMMARY =====")
        print(f"groups: {len(groups)}")
        for idx, group in enumerate(groups, start=1):
            print(f"  group {idx}:")
            for c in group:
                print(f"    - {short_path(c.case_dir)}")
        print("=============================")
        return 0

    # ------------------------------------------------------------
    # 7. Normal output
    # ------------------------------------------------------------
    if not groups:
        log(
            "[IDENTICAL] No identical cases found",
            level="info",
            quiet=quiet,
            verbose=True,
            debug=debug,
            compact=compact,
        )
    else:
        for idx, group in enumerate(groups, start=1):
            print(f"[IDENTICAL] Group {idx}:")
            for c in group:
                print(f"  - {short_path(c.case_dir)}")
            print()

    # ------------------------------------------------------------
    # 8. Diff mode (why cases differ)
    # ------------------------------------------------------------
    if show_diff:
        print("[IDENTICAL] Differences between non-identical cases:")
        for a in cases:
            for b in cases:
                if a is b:
                    continue
                diffs = diff_cases(a, b)
                if diffs:
                    print(f"  {short_path(a.case_dir)} vs {short_path(b.case_dir)}:")
                    for d in diffs:
                        print(f"    - {d}")
                    print()

    return 0
