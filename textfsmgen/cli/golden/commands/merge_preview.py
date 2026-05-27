from __future__ import annotations

from pathlib import Path
import click
import pathlib

from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs import file

from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command


# ======================================================================
# LOGGING UTILITIES
# ======================================================================


def log(
    msg,
    *,
    level="info",
    indent=0,
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
):
    if compact:
        return
    if quiet and level not in ("FAIL", "SUCCESS"):
        return
    if not debug:
        if level == "debug":
            return
        if not verbose and level in ("info", "warn"):
            return
    if msg.startswith("["):
        end = msg.find("]")
        if end != -1:
            msg = msg[end + 1 :].lstrip()
    prefix = f"[{level}]"
    pad = " " * indent
    print(f"{prefix} {pad}{msg}")


def short_path(value):
    if isinstance(value, pathlib.Path):
        value = str(value)
    return file.path_name(value)


# ======================================================================
# CLI ENTRYPOINT
# ======================================================================


@click.command(
    name="merge-preview",
    help="Preview merge reference selection: find which src case can serve as reference.",
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--summary", is_flag=True, help="Show summary of merge-preview results.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_merge_preview(srcs, quiet, verbose, debug, summary, compact):
    return cmd_merge_preview_(
        src_paths=[Path(s).resolve() for s in srcs],
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        summary=summary,
        compact=compact,
    )


# ======================================================================
# MAIN IMPLEMENTATION
# ======================================================================


def cmd_merge_preview_(src_paths, *, quiet, verbose, debug, summary, compact):
    if not src_paths:
        raise click.ClickException("No source cases provided.")

    # ------------------------------------------------------------
    # 1. Load and validate src cases
    # ------------------------------------------------------------
    src_cases = []
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

        src_cases.append(c)

    if validation_failures:
        if compact:
            print("[MERGE-PREVIEW] Reference: (none)")
            print(f"[MERGE-PREVIEW] Candidates: {len(src_paths)}")
            print("[MERGE-PREVIEW] Result: fail")
            return 1

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
    # 2. Try each src as reference candidate
    # ------------------------------------------------------------
    reference_case = None

    for candidate in src_cases:
        cand_name = short_path(candidate.case_dir)

        log(
            f"trying candidate: {cand_name}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        cand_template = candidate.data.load_expected().template.content

        candidate_ok = True

        for other in src_cases:
            for input_info, exp_info in other.data.load_input_result_pairs():
                rows = parse_textfsm_to_dicts(cand_template, input_info.content)
                if rows != exp_info.content:
                    candidate_ok = False
                    break
            if not candidate_ok:
                break

        if candidate_ok:
            reference_case = candidate
            log(
                f"{cand_name} selected as reference candidate",
                level="SUCCESS",
                indent=2,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
            break
        else:
            log(
                f"{cand_name} rejected",
                level="info",
                indent=2,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

    # ------------------------------------------------------------
    # 3. Compact mode
    # ------------------------------------------------------------
    if compact:
        print(
            f"[MERGE-PREVIEW] Reference: {short_path(reference_case.case_dir) if reference_case else '(none)'}"
        )
        print(f"[MERGE-PREVIEW] Candidates: {len(src_cases)}")
        print(f"[MERGE-PREVIEW] Result: {'success' if reference_case else 'fail'}")
        return 0 if reference_case else 1

    # ------------------------------------------------------------
    # 4. Summary mode
    # ------------------------------------------------------------
    if summary:
        print("===== MERGE-PREVIEW SUMMARY =====")
        print(
            f"reference_case: {short_path(reference_case.case_dir) if reference_case else '(none)'}"
        )
        print(f"candidates_total: {len(src_cases)}")
        print("================================")
        return 0 if reference_case else 1

    # ------------------------------------------------------------
    # 5. Normal output
    # ------------------------------------------------------------
    if reference_case:
        log(
            f"reference candidate: {short_path(reference_case.case_dir)}",
            level="SUCCESS",
            quiet=quiet,
            verbose=True,
            debug=debug,
            compact=compact,
        )
        return 0

    log(
        "no valid reference candidates found",
        level="FAIL",
        quiet=False,
        verbose=True,
        debug=debug,
        compact=compact,
    )
    return 1
