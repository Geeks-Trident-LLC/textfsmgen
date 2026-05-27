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
    name="merge-plan",
    help="Dry-run of merge: show reference, merged template/snippet, input merge plan, and expected_results plan.",
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--summary", is_flag=True, help="Show summary of merge-plan results.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_merge_plan(srcs, quiet, verbose, debug, summary, compact):
    return cmd_merge_plan_(
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


def cmd_merge_plan_(
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
    # 2. Find reference candidate (same logic as merge-preview)
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
            print("[MERGE-PLAN] Reference: (none)")
            print("[MERGE-PLAN] Inputs: 0")
            print("[MERGE-PLAN] Result: fail")
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
    ref_expected = reference_case.data.load_expected()
    ref_template_text = ref_expected.template.content
    ref_snippet_text = ref_expected.snippet.content

    # ------------------------------------------------------------
    # 3. Build input merge plan (BASE / COPY / OVERWRITE / RENAME)
    # ------------------------------------------------------------
    simulated_inputs = {}
    merge_actions = []

    # BASE inputs from reference
    for inp in reference_case.data.load_inputs():
        name = Path(inp.fullname).name
        simulated_inputs[name] = inp.content
        merge_actions.append(("BASE", name, "", ref_name))

    # Merge other cases
    for c in src_cases:
        if c.case_dir == reference_case.case_dir:
            continue

        case_name = short_path(c.case_dir)

        for inp in c.data.load_inputs():
            name = Path(inp.fullname).name
            content = inp.content

            if name not in simulated_inputs:
                simulated_inputs[name] = content
                merge_actions.append(("COPY", name, "", case_name))
                continue

            if simulated_inputs[name] == content:
                merge_actions.append(("OVERWRITE", name, "", case_name))
                continue

            # rename
            base = Path(name).stem
            ext = Path(name).suffix
            counter = 2

            while True:
                new_name = f"{base}_{counter}{ext}"
                if new_name not in simulated_inputs:
                    simulated_inputs[new_name] = content
                    merge_actions.append(("RENAME", name, new_name, case_name))
                    break
                counter += 1

    # ------------------------------------------------------------
    # 4. Expected_results plan (what would be generated)
    # ------------------------------------------------------------
    expected_plan = sorted(simulated_inputs.keys())

    # ------------------------------------------------------------
    # 5. Compact summary
    # ------------------------------------------------------------
    if compact:
        print(f"[MERGE-PLAN] Reference: {ref_name}")
        print(f"[MERGE-PLAN] Inputs: {len(simulated_inputs)}")
        print("[MERGE-PLAN] Result: success")
        return 0

    # ------------------------------------------------------------
    # 6. Full output (verbose)
    # ------------------------------------------------------------
    log(
        f"[PLAN] Reference case: {ref_name}",
        level="info",
        quiet=quiet,
        verbose=True,
        debug=debug,
        compact=compact,
    )

    log(
        "[PLAN] Merged template (from reference):",
        level="info",
        quiet=quiet,
        verbose=True,
        debug=debug,
        compact=compact,
    )
    print(ref_template_text)

    log(
        "[PLAN] Merged snippet (from reference):",
        level="info",
        quiet=quiet,
        verbose=True,
        debug=debug,
        compact=compact,
    )
    print(ref_snippet_text)

    log(
        "[PLAN] Input merge plan:",
        level="info",
        quiet=quiet,
        verbose=True,
        debug=debug,
        compact=compact,
    )

    action_w = max(len(a[0]) for a in merge_actions)
    name_w = max(len(a[1]) for a in merge_actions)
    new_w = max(len(a[2]) for a in merge_actions)

    for action, name, new_name, src in merge_actions:
        if action == "RENAME":
            print(
                f"  {action:<{action_w}}  {name:<{name_w}} → {new_name:<{new_w}}  (from {src})"
            )
        else:
            print(f"  {action:<{action_w}}  {name:<{name_w}}      (from {src})")

    log(
        "[PLAN] Expected_results to be generated:",
        level="info",
        quiet=quiet,
        verbose=True,
        debug=debug,
        compact=compact,
    )

    for name in expected_plan:
        print(f"  - expected_results/{name}_result.json")

    # ------------------------------------------------------------
    # 7. Summary
    # ------------------------------------------------------------
    if summary:
        log(
            "===== MERGE-PLAN SUMMARY =====",
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
            f"merged_inputs: {len(simulated_inputs)}",
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

    return 0
