from __future__ import annotations

from pathlib import Path
import difflib
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command
from .shared import log, short_path, canonical_json


# ======================================================================
# CLI ENTRYPOINT
# ======================================================================


@click.command(
    name="merge-diff",
    help="Show diffs between golden expected_results and results from merged reference template.",
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--summary", is_flag=True, help="Show summary of merge-diff results.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_merge_diff(srcs, quiet, verbose, debug, summary, compact):
    return cmd_merge_diff_(
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


def cmd_merge_diff_(
    src_paths: list[Path],
    *,
    quiet=False,
    verbose=False,
    debug=False,
    summary=False,
    compact=False,
):
    if not src_paths:
        raise click.ClickException("No source cases provided.")

    # ------------------------------------------------------------
    # 1. Load and validate src cases
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
    # 2. Find reference candidate (same as merge-preview)
    # ------------------------------------------------------------
    reference_case: GoldenCase | None = None

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
                f"{cand_name} rejected as reference candidate",
                level="info",
                indent=2,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

    if reference_case is None:
        if compact:
            print("[MERGE-DIFF] Reference: (none)")
            print("[MERGE-DIFF] Inputs: 0, diffs: 0")
            print("[MERGE-DIFF] Result: fail")
        else:
            log(
                "no valid reference candidates found",
                level="FAIL",
                quiet=False,
                verbose=True,
                debug=debug,
                compact=compact,
            )
        return 1

    ref_name = short_path(reference_case.case_dir)

    # ------------------------------------------------------------
    # 3. Diff template + snippet + expected_results
    # ------------------------------------------------------------
    ref_expected = reference_case.data.load_expected()
    ref_template_text = ref_expected.template.content
    ref_snippet_text = ref_expected.snippet.content

    diffs: dict[str, list[str]] = {}
    total_inputs = 0

    for c in src_cases:
        if c.case_dir == reference_case.case_dir:
            continue

        case_name = short_path(c.case_dir)

        # Template diff
        case_template_text = c.data.load_expected().template.content
        if case_template_text != ref_template_text:
            diffs[f"{case_name}/template"] = ["template diff"]
            if not compact:
                diff_lines = list(
                    difflib.unified_diff(
                        ref_template_text.splitlines(keepends=True),
                        case_template_text.splitlines(keepends=True),
                        fromfile=f"ref:{ref_name}/template",
                        tofile=f"case:{case_name}/template",
                    )
                )
                for line in diff_lines:
                    print(line, end="")

        # Snippet diff
        case_snippet_text = c.data.load_expected().snippet.content
        if case_snippet_text != ref_snippet_text:
            diffs[f"{case_name}/snippet"] = ["snippet diff"]
            if not compact:
                diff_lines = list(
                    difflib.unified_diff(
                        ref_snippet_text.splitlines(keepends=True),
                        case_snippet_text.splitlines(keepends=True),
                        fromfile=f"ref:{ref_name}/snippet",
                        tofile=f"case:{case_name}/snippet",
                    )
                )
                for line in diff_lines:
                    print(line, end="")

        # expected_results diff
        for input_info, exp_info in c.data.load_input_result_pairs():
            total_inputs += 1

            merged_rows = parse_textfsm_to_dicts(ref_template_text, input_info.content)
            merged_json = canonical_json(merged_rows)
            golden_json = canonical_json(exp_info.content)

            if merged_json != golden_json:
                diffs[short_path(exp_info.fullname)] = ["expected_results diff"]
                if not compact:
                    diff_lines = list(
                        difflib.unified_diff(
                            golden_json.splitlines(keepends=True),
                            merged_json.splitlines(keepends=True),
                            fromfile=f"golden:{short_path(exp_info.fullname)}",
                            tofile=f"merged:{short_path(exp_info.fullname)}",
                        )
                    )
                    for line in diff_lines:
                        print(line, end="")

    # ------------------------------------------------------------
    # 4. Compact summary
    # ------------------------------------------------------------
    if compact:
        print(f"[MERGE-DIFF] Reference: {ref_name}")
        print(f"[MERGE-DIFF] Inputs: {total_inputs}, diffs: {len(diffs)}")
        print(f"[MERGE-DIFF] Result: {'fail' if diffs else 'success'}")
        return 1 if diffs else 0

    # ------------------------------------------------------------
    # 5. Full summary (if --summary)
    # ------------------------------------------------------------
    if summary:
        log(
            "===== MERGE-DIFF SUMMARY =====",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )

        log(
            f"reference_case: {ref_name}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )

        log(
            f"inputs_total: {total_inputs}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )

        log(
            f"diff_files: {len(diffs)}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )

        if diffs:
            log(
                "files_with_diffs:",
                level="info",
                quiet=False,
                verbose=True,
                debug=debug,
                compact=compact,
            )
            for name in sorted(diffs.keys()):
                print(f"  - {name}")
        else:
            log(
                "files_with_diffs: (none)",
                level="info",
                quiet=False,
                verbose=True,
                debug=debug,
                compact=compact,
            )

        log(
            "================================",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )

    # ------------------------------------------------------------
    # 6. Exit code
    # ------------------------------------------------------------
    return 1 if diffs else 0
