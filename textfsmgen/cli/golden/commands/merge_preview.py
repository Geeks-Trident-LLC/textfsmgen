from __future__ import annotations

from pathlib import Path
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command
from .shared import log, short_path


# ======================================================================
# CLI ENTRYPOINT
# ======================================================================


@click.command(
    name="merge-preview",
    help="Preview merge reference selection: find which src case(s) can serve as reference.",
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--summary", is_flag=True, help="Show summary of merge-preview results.")
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_merge_preview(srcs, quiet, verbose, debug, summary):
    return cmd_merge_preview_(
        src_paths=[Path(s).resolve() for s in srcs],
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        summary=summary,
    )


# ======================================================================
# MAIN IMPLEMENTATION
# ======================================================================


def cmd_merge_preview_(
    src_paths: list[Path], *, quiet=False, verbose=False, debug=False, summary=False
):
    if not src_paths:
        raise click.ClickException("No source cases provided.")

    # ------------------------------------------------------------
    # 1. Load and validate src cases (integration + tested)
    # ------------------------------------------------------------
    src_cases: list[GoldenCase] = []
    validation_failures: list[str] = []

    for p in src_paths:
        log(
            f"validating src: {short_path(p)}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        c = GoldenCase.from_path(p)

        if not c.is_integration():
            validation_failures.append(
                f"src {short_path(p)} is not an integration case"
            )
            continue

        try:
            c.tested()
        except Exception as e:
            validation_failures.append(f"src {short_path(p)} is not tested:\n{e}")
            continue

        log(
            f"{short_path(p)} — tested and valid",
            level="OK",
            indent=2,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        src_cases.append(c)

    if validation_failures:
        for msg in validation_failures:
            log(msg, level="FAIL", quiet=False, verbose=True, debug=debug)
        return 1

    # ------------------------------------------------------------
    # 2. Try each src as a reference candidate
    # ------------------------------------------------------------
    valid_candidates = []
    invalid_candidates = []

    for candidate in src_cases:
        cand_name = short_path(candidate.case_dir)

        log(
            f"trying candidate: {cand_name}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        cand_template = candidate.data.load_expected().template.content

        log(
            f"template length = {len(cand_template)} bytes",
            level="debug",
            indent=2,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        candidate_ok = True
        candidate_failures = []

        for other in src_cases:
            for input_info, exp_info in other.data.load_input_result_pairs():
                short_in = short_path(input_info.fullname)
                short_exp = short_path(exp_info.fullname)

                log(
                    f"parsing {short_in}",
                    level="info",
                    indent=2,
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                )

                rows = parse_textfsm_to_dicts(cand_template, input_info.content)

                log(
                    f"parsed rows preview: {rows[:2]}",
                    level="debug",
                    indent=6,
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                )

                if rows != exp_info.content:
                    candidate_ok = False
                    candidate_failures.append(
                        f"mismatch for {short_in} using candidate {cand_name}"
                    )
                    # mismatch is DEBUG during matching
                    log(
                        f"mismatch for {short_in}",
                        level="debug",
                        indent=4,
                        quiet=quiet,
                        verbose=verbose,
                        debug=debug,
                    )
                else:
                    log(
                        f"{short_in} matches {short_exp} ({len(rows)} rows)",
                        level="OK",
                        indent=4,
                        quiet=quiet,
                        verbose=verbose,
                        debug=debug,
                    )

        if candidate_ok:
            valid_candidates.append(candidate.case_dir)
            log(
                f"{cand_name} IS a valid reference candidate",
                level="SUCCESS",
                indent=2,
                quiet=quiet,
                verbose=True,
                debug=debug,
            )
        else:
            invalid_candidates.append((candidate.case_dir, candidate_failures))
            # NOT a failure — expected in preview
            log(
                f"{cand_name} rejected as reference candidate",
                level="info",
                indent=2,
                quiet=quiet,
                verbose=True,
                debug=debug,
            )

    # ------------------------------------------------------------
    # 3. Summary (optional)
    # ------------------------------------------------------------
    if summary:
        log(
            "===== MERGE-PREVIEW SUMMARY =====",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

        log(
            "valid reference candidates:",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )
        if valid_candidates:
            for p in valid_candidates:
                print(f"  - {short_path(p)}")
        else:
            print("  (none)")

        log("invalid candidates:", level="info", quiet=False, verbose=True, debug=debug)
        if invalid_candidates:
            for p, fails in invalid_candidates:
                print(f"  - {short_path(p)}")
                for f in fails:
                    print(f"      {f}")
        else:
            print("  (none)")

        log(
            "================================",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

    # ------------------------------------------------------------
    # 4. Final exit code
    # ------------------------------------------------------------
    if valid_candidates:
        return 0

    # Only FAIL if *no* valid candidates exist
    log(
        "no valid reference candidates found",
        level="FAIL",
        quiet=False,
        verbose=True,
        debug=debug,
    )
    return 1
