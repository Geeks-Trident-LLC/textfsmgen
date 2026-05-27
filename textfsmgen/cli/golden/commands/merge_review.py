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
    name="merge-review",
    help="Review whether dst is a valid reference candidate for the given src integration cases.",
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--summary", is_flag=True, help="Show summary of merge-review results.")
@click.argument("dst", type=click.Path(exists=True))
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_merge_review(dst, srcs, quiet, verbose, debug, summary):
    return cmd_merge_review_(
        dst=Path(dst).resolve(),
        src_paths=[Path(s).resolve() for s in srcs],
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        summary=summary,
    )


# ======================================================================
# MAIN IMPLEMENTATION
# ======================================================================


def cmd_merge_review_(
    dst: Path,
    src_paths: list[Path],
    *,
    quiet=False,
    verbose=False,
    debug=False,
    summary=False,
):
    if not src_paths:
        raise click.ClickException("No source cases provided.")

    # ------------------------------------------------------------
    # 1. Load and validate dst (reference)
    # ------------------------------------------------------------
    dst_case = GoldenCase.from_path(dst)

    log(
        f"validating dst: {short_path(dst)}",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    if not dst_case.is_integration():
        raise click.ClickException(
            f"[FAIL] dst must be an integration case: {short_path(dst)}"
        )

    try:
        dst_case.tested()
    except Exception as e:
        raise click.ClickException(f"[FAIL] dst is not tested:\n{e}")

    log(
        f"{short_path(dst)} — tested and valid",
        level="OK",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    ref_expected = dst_case.data.load_expected()
    ref_template = ref_expected.template.content

    log(
        f"template length = {len(ref_template)} bytes",
        level="debug",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    # ------------------------------------------------------------
    # 2. Load and validate src cases (integration, tested, compatible)
    # ------------------------------------------------------------
    src_cases: list[GoldenCase] = []
    compat_failures: list[str] = []

    for p in src_paths:
        log(
            f"validating src: {short_path(p)}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        c = GoldenCase.from_path(p)

        # Must be integration
        if not c.is_integration():
            compat_failures.append(f"src {short_path(p)} is not an integration case")
            continue

        # Must be tested
        try:
            c.tested()
        except Exception as e:
            compat_failures.append(f"src {short_path(p)} is not tested:\n{e}")
            continue

        # Must be compatible with dst
        try:
            ok = dst_case.check(c)
            if not ok:
                compat_failures.append(
                    f"src {short_path(p)} is not compatible with dst"
                )
                continue
        except Exception as e:
            compat_failures.append(
                f"compatibility check failed for src {short_path(p)}:\n{e}"
            )
            continue

        log(
            f"{short_path(p)} — tested and compatible",
            level="OK",
            indent=2,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        src_cases.append(c)

    # If any failures occurred, print them and stop
    if compat_failures:
        for msg in compat_failures:
            log(msg, level="FAIL", quiet=False, verbose=True, debug=debug)
        return 1

    # ------------------------------------------------------------
    # 3. Use dst.template to parse src.inputs and compare to src.expected_results
    # ------------------------------------------------------------
    any_ok = False
    matching_srcs = []
    nonmatching_srcs = []

    for c in src_cases:
        log(
            f"checking src: {short_path(c.case_dir)}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        src_matched = True

        for input_info, exp_info in c.data.load_input_result_pairs():
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

            rows = parse_textfsm_to_dicts(ref_template, input_info.content)

            log(
                f"parsed rows preview: {rows[:2]}",
                level="debug",
                indent=6,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
            )

            if rows == exp_info.content:
                log(
                    f"{short_in} matches {short_exp} ({len(rows)} rows)",
                    level="OK",
                    indent=4,
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                )
            else:
                src_matched = False
                log(
                    f"mismatch for {short_in}",
                    level="FAIL",
                    indent=4,
                    quiet=quiet,
                    verbose=True,
                    debug=debug,
                )
                log(
                    f"expected rows: {len(exp_info.content)}",
                    level="debug",
                    indent=6,
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                )
                log(
                    f"actual rows:   {len(rows)}",
                    level="debug",
                    indent=6,
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                )

        if src_matched:
            any_ok = True
            matching_srcs.append(c.case_dir)
        else:
            nonmatching_srcs.append(c.case_dir)

    # ------------------------------------------------------------
    # 4. Summary (optional)
    # ------------------------------------------------------------
    if summary:
        log(
            "===== MERGE-REVIEW SUMMARY =====",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

        log(
            f"dst: {short_path(dst)}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

        log(
            f"valid reference candidate: {'YES' if any_ok else 'NO'}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

        log("matching srcs:", level="info", quiet=False, verbose=True, debug=debug)
        if matching_srcs:
            for p in matching_srcs:
                print(f"  - {short_path(p)}")
        else:
            print("  (none)")

        log("non-matching srcs:", level="info", quiet=False, verbose=True, debug=debug)
        if nonmatching_srcs:
            for p in nonmatching_srcs:
                print(f"  - {short_path(p)}")
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
    # 5. Final verdict
    # ------------------------------------------------------------
    if any_ok:
        log(
            f"dst {short_path(dst)} IS a valid reference candidate",
            level="SUCCESS",
            quiet=quiet,
            verbose=True,
            debug=debug,
        )
        return 0

    log(
        f"dst {short_path(dst)} is NOT a valid reference candidate",
        level="FAIL",
        quiet=quiet,
        verbose=True,
        debug=debug,
    )
    return 1
