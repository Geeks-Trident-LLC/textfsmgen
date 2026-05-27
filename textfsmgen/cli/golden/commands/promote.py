from __future__ import annotations

from pathlib import Path
import json
import shutil
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command
from .shared import log, short_path
from .run import cmd_run_


@click.command(
    name="promote",
    help="Promote an integration case into a main case by generating canonical sample and result.",
)
@timed_command
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.option("--summary", is_flag=True, help="Show summary of promotion.")
@click.argument("case", type=click.Path(exists=True))
def cmd_promote(case, quiet, verbose, debug, compact, summary):
    return cmd_promote_(
        case_path=Path(case).resolve(),
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
        summary=summary,
    )


def cmd_promote_(
    case_path: Path,
    *,
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
    summary=False,
):
    # ------------------------------------------------------------
    # 1. Load and validate integration case (using run(...quicktest=True))
    # ------------------------------------------------------------
    case = GoldenCase.from_path(case_path)

    if not case.is_integration():
        raise click.ClickException(
            f"{short_path(case_path)} is not an integration case"
        )

    rc = cmd_run_(
        case_path,
        quicktest=True,
        # quiet=quiet,
        # verbose=verbose,
        # debug=debug,
        # compact=compact,
    )
    if rc != 0:
        raise click.ClickException(f"{short_path(case_path)} failed quicktest")

    log(
        f"{short_path(case_path)} — integration and tested",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 2. Determine promote path (integration → main)
    # ------------------------------------------------------------
    parts = list(case_path.parts)
    try:
        idx = parts.index("integration")
    except ValueError:
        raise click.ClickException("Path does not contain 'integration'")

    parts[idx] = "main"
    promote_path = Path(*parts)

    if promote_path.exists():
        raise click.ClickException(
            f"Main case already exists: {short_path(promote_path)}"
        )

    log(
        f"promote path: {short_path(promote_path)}",
        level="debug",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 3. Find canonical sample by loader.build(sample)
    # ------------------------------------------------------------
    loader = case.data
    expected = loader.load_expected()
    expected_template = expected.template.content

    canonical_sample = None
    canonical_result = None

    for inp in loader.load_inputs():
        sample = inp.content
        name = Path(inp.fullname).name

        log(
            f"trying sample: {name}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        built = loader.build(sample)
        generated_template = built.template

        if generated_template == expected_template:
            log(
                f"canonical sample found: {name}",
                level="SUCCESS",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
            canonical_sample = sample
            canonical_result = parse_textfsm_to_dicts(generated_template, sample)
            break
        else:
            log(
                f"sample {name} does not match expected template",
                level="debug",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

    if canonical_sample is None:
        raise click.ClickException(
            "No input sample can reproduce expected template; cannot promote."
        )

    # ------------------------------------------------------------
    # 4. Create promote directory structure
    # ------------------------------------------------------------
    promote_path.mkdir(parents=True)

    canonical_dir = promote_path / "canonical"
    canonical_dir.mkdir()

    inputs_dir = promote_path / "inputs"
    expected_results_dir = promote_path / "expected_results"

    inputs_dir.mkdir()
    expected_results_dir.mkdir()

    log(
        f"created promote directories under {short_path(promote_path)}",
        level="debug",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 5. Write manifest.json
    # ------------------------------------------------------------
    manifest = loader.load_manifest()
    manifest_path = promote_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    log(
        f"wrote manifest.json → {short_path(manifest_path)}",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 6. Write canonical template + snippet
    # ------------------------------------------------------------
    (canonical_dir / "textfsm.template").write_text(expected.template.content)
    (canonical_dir / "snippet.txt").write_text(expected.snippet.content)

    # ------------------------------------------------------------
    # 7. Write canonical sample + result
    # ------------------------------------------------------------
    (canonical_dir / "sample.txt").write_text(canonical_sample)
    (canonical_dir / "result.json").write_text(
        json.dumps(canonical_result, indent=2, ensure_ascii=False)
    )

    log(
        "canonical artifacts written under canonical/",
        level="debug",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 8. Copy inputs
    # ------------------------------------------------------------
    for inp in loader.load_inputs():
        name = Path(inp.fullname).name
        out_path = inputs_dir / name
        out_path.write_text(inp.content)

    log(
        f"copied inputs → {short_path(inputs_dir)}",
        level="debug",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 9. Copy expected_results
    # ------------------------------------------------------------
    for _, exp in loader.load_input_result_pairs():
        name = Path(exp.fullname).name
        out_path = expected_results_dir / name
        out_path.write_text(json.dumps(exp.content, indent=2, ensure_ascii=False))

    log(
        f"copied expected_results → {short_path(expected_results_dir)}",
        level="debug",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 10. Run quicktest on promoted case (must generate golden.hash/meta.json)
    # ------------------------------------------------------------
    rc = cmd_run_(
        promote_path,
        # quicktest=True,
        # quiet=quiet,
        # verbose=verbose,
        # debug=debug,
        # compact=compact,
    )

    if rc != 0:
        shutil.rmtree(promote_path)
        raise click.ClickException(
            "Promoted case failed quicktest (golden.hash/meta.json not valid)"
        )

    # ------------------------------------------------------------
    # 11. Compact mode
    # ------------------------------------------------------------
    if compact:
        print(f"[PROMOTE] Case: {short_path(case_path)}")
        print(f"[PROMOTE] Promoted: {short_path(promote_path)}")
        print("[PROMOTE] Result: success")
        return 0

    # ------------------------------------------------------------
    # 12. Summary mode
    # ------------------------------------------------------------
    if summary:
        print("===== PROMOTE SUMMARY =====")
        print(f"source:   {short_path(case_path)}")
        print(f"promoted: {short_path(promote_path)}")
        print("canonical:")
        print("  template: canonical/textfsm.template")
        print("  snippet:  canonical/snippet.txt")
        print("  sample:   canonical/sample.txt")
        print("  result:   canonical/result.json")
        print("===========================")
        return 0

    # ------------------------------------------------------------
    # 13. Normal output
    # ------------------------------------------------------------
    log(
        f"promotion completed: {short_path(promote_path)}",
        level="SUCCESS",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    return 0
