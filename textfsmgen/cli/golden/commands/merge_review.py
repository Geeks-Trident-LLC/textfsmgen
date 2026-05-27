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
    help="Review whether dst is a valid reference candidate for merging src cases.",
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("dst", type=click.Path(exists=True))
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_merge_review(dst, srcs, quiet, verbose, debug, compact):
    return cmd_merge_review_(
        dst_path=Path(dst).resolve(),
        src_paths=[Path(s).resolve() for s in srcs],
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )


def cmd_merge_review_(
    dst_path: Path,
    src_paths: list[Path],
    *,
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
):
    if not src_paths:
        raise click.ClickException("No source cases provided.")

    dst_case = GoldenCase.from_path(dst_path)

    if not dst_case.is_integration():
        msg = f"dst {short_path(dst_path)} is not an integration case"
        if compact:
            print(f"[MERGE-REVIEW] Dst: {short_path(dst_path)}")
            print("[MERGE-REVIEW] Result: fail")
            print(f"[MERGE-REVIEW] Reason: {msg}")
            return 1
        raise click.ClickException(msg)

    try:
        dst_case.tested()
    except Exception as e:
        msg = f"dst {short_path(dst_path)} is not tested:\n{e}"
        if compact:
            print(f"[MERGE-REVIEW] Dst: {short_path(dst_path)}")
            print("[MERGE-REVIEW] Result: fail")
            print(f"[MERGE-REVIEW] Reason: {msg}")
            return 1
        raise click.ClickException(msg)

    log(
        f"dst: {short_path(dst_path)} — tested and valid",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    src_cases: list[GoldenCase] = []
    validation_failures: list[str] = []

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
            compact=compact,
        )
        src_cases.append(c)

    if validation_failures:
        if compact:
            print(f"[MERGE-REVIEW] Dst: {short_path(dst_path)}")
            print("[MERGE-REVIEW] Result: fail")
            print("[MERGE-REVIEW] Reason:")
            for msg in validation_failures:
                print(f"  - {msg}")
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

    dst_template = dst_case.data.load_expected().template.content

    all_ok = True
    mismatch_details = []

    for other in src_cases:
        for input_info, exp_info in other.data.load_input_result_pairs():
            rows = parse_textfsm_to_dicts(dst_template, input_info.content)
            if rows != exp_info.content:
                all_ok = False
                msg = f"mismatch for {short_path(input_info.fullname)} when using dst template"
                mismatch_details.append(msg)
                log(
                    msg,
                    level="FAIL",
                    indent=2,
                    quiet=quiet,
                    verbose=True,
                    debug=debug,
                    compact=compact,
                )
            else:
                log(
                    f"{short_path(input_info.fullname)} matches {short_path(exp_info.fullname)}",
                    level="OK",
                    indent=2,
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )

    if compact:
        print(f"[MERGE-REVIEW] Dst: {short_path(dst_path)}")
        if all_ok:
            print("[MERGE-REVIEW] Result: success")
        else:
            print("[MERGE-REVIEW] Result: fail")
            if mismatch_details:
                print("[MERGE-REVIEW] Reason:")
                for msg in mismatch_details:
                    print(f"  - {msg}")
        return 0 if all_ok else 1

    if all_ok:
        log(
            "dst is a valid reference candidate for all srcs",
            level="SUCCESS",
            quiet=quiet,
            verbose=True,
            debug=debug,
            compact=compact,
        )
        return 0

    log(
        "dst is NOT a valid reference candidate for all srcs",
        level="FAIL",
        quiet=False,
        verbose=True,
        debug=debug,
        compact=compact,
    )
    return 1
