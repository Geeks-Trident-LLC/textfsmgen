from __future__ import annotations

from pathlib import Path
import json
import click
import pathlib

from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs import file

from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command
from .shared import log, short_path, canonical_json


@click.command(
    name="identical",
    help="Identify integration cases that are completely identical (template, snippet, inputs, expected_results)."
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_identical(srcs, quiet, verbose, debug, compact):
    return cmd_identical_(
        src_paths=[Path(s).resolve() for s in srcs],
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )


def cmd_identical_(src_paths, *, quiet, verbose, debug, compact):
    if not src_paths:
        raise click.ClickException("No source cases provided.")

    # ------------------------------------------------------------
    # 1. Load + validate cases
    # ------------------------------------------------------------
    cases = []
    validation_failures = []

    for p in src_paths:
        log(f"validating src: {short_path(p)}", level="info",
            quiet=quiet, verbose=verbose, debug=debug, compact=compact)

        c = GoldenCase.from_path(p)

        if not c.is_integration():
            validation_failures.append(f"{short_path(p)} is not an integration case")
            continue

        try:
            c.tested()
        except Exception as e:
            validation_failures.append(f"{short_path(p)} is not tested:\n{e}")
            continue

        log(f"{short_path(p)} — tested and valid", level="OK",
            indent=2, quiet=quiet, verbose=verbose, debug=debug, compact=compact)

        cases.append(c)

    if validation_failures:
        for msg in validation_failures:
            log(msg, level="FAIL", quiet=False, verbose=True, debug=debug, compact=compact)
        return 1

    # ------------------------------------------------------------
    # 2. Build canonical signatures for each case
    # ------------------------------------------------------------
    signatures = {}  # signature → list of cases

    for c in cases:
        expected = c.data.load_expected()

        # Template + snippet
        template = expected.template.content
        snippet = expected.snippet.content

        # Inputs
        inputs = []
        for inp in c.data.load_inputs():
            name = Path(inp.fullname).name
            inputs.append((name, inp.content))
        inputs.sort()

        # Expected results
        results = []
        for input_info, exp_info in c.data.load_input_result_pairs():
            name = Path(exp_info.fullname).name
            results.append((name, canonical_json(exp_info.content)))
        results.sort()

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
    # 4. Compact mode
    # ------------------------------------------------------------
    if compact:
        print(f"[IDENTICAL] Groups: {len(groups)}")
        return 0

    # ------------------------------------------------------------
    # 5. Normal output
    # ------------------------------------------------------------
    if not groups:
        log("[IDENTICAL] No identical cases found", level="info",
            quiet=quiet, verbose=True, debug=debug, compact=compact)
        return 0

    for idx, group in enumerate(groups, start=1):
        print(f"[IDENTICAL] Group {idx}:")
        for c in group:
            print(f"  - {short_path(c.case_dir)}")
        print()

    return 0
