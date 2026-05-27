from __future__ import annotations

import json
import shutil
from pathlib import Path
import click

from textfsmgen import parse_textfsm_to_dicts
from textfsmgen.libs import file

from ..cli_decorator import (
    timed_command,
    validate_sandbox_flags,
)
from ..core.utils import validate_case_path
from ..core.golden_case import GoldenCase
from .shared import _open_directory


@click.command(
    name="generate", help="Generate expected artifacts for an existing case."
)
@timed_command
@validate_sandbox_flags
@click.option("--author", required=True, help="Set the author for the generating case.")
@click.option(
    "--dry-run",
    "--dryrun",
    is_flag=True,
    help="Simulate generation without writing files.",
)
@click.option(
    "--sandbox", is_flag=True, help="Write into <case>.temp and delete on success."
)
@click.option(
    "--sandbox-keep", is_flag=True, help="Write into <case>.temp and preserve it."
)
@click.option(
    "--open",
    "open_after",
    is_flag=True,
    help="Open the case directory after generation.",
)
@click.option("--summary", is_flag=True, help="Show summary of generated case.")
@click.option("--verbose", is_flag=True, help="Show detailed generation steps.")
@click.argument("case", type=click.Path(exists=True, file_okay=False))
def cmd_generate(
    case, author, dry_run, sandbox, sandbox_keep, open_after, summary, verbose
):
    return cmd_generate_(
        Path(case).resolve(),
        author=author,
        dry_run=dry_run,
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        open_after=open_after,
        summary=summary,
        verbose=verbose,
    )


def cmd_generate_(
    case_path, author, dry_run, sandbox, sandbox_keep, open_after, summary, verbose
):
    """Generate expected artifacts for an existing case."""
    ok = validate_case_path(case_path)
    if not ok:
        click.echo(f"[FAIL] {ok}")
        return 1

    golden_case = GoldenCase.from_path(case_path)

    # ------------------------------------------------------------------
    # 0. Enforce: generate is ONLY allowed inside integration/
    # ------------------------------------------------------------------
    if golden_case.is_main():
        raise click.ClickException(
            "'generate' is only allowed for integration cases, "
            "but this case is categorized as: main"
        )

    # ------------------------------------------------------------------
    # 1. Load inputs
    # ------------------------------------------------------------------
    if verbose:
        click.echo(f"[info] Loading inputs from {golden_case.name}")

    inputs = list(golden_case.data.load_inputs())
    if not inputs:
        raise click.ClickException(f"No inputs found in {golden_case.name}/inputs")

    snippets = []
    templates = []
    builders = []

    # ------------------------------------------------------------------
    # 2. Build snippet/template for each input
    # ------------------------------------------------------------------
    for inp in inputs:
        if verbose:
            click.echo(f"[info] Building from input: {file.path_name(inp.fullname)}")

        builder = golden_case.data.build(inp.content)
        if not builder:
            raise click.ClickException(
                f"Builder returned None for input: {file.path_name(inp.fullname)}"
            )

        builders.append(builder)
        snippets.append(builder.snippet)
        templates.append(builder.template)

    # ------------------------------------------------------------------
    # 3. Ensure exactly one snippet + one template
    # ------------------------------------------------------------------
    unique_snippets = set(snippets)
    unique_templates = set(templates)

    if len(unique_snippets) != 1:
        raise click.ClickException(
            f"Multiple snippets detected ({len(unique_snippets)}). "
            "All inputs must produce the same snippet."
        )

    if len(unique_templates) != 1:
        raise click.ClickException(
            f"Multiple templates detected ({len(unique_templates)}). "
            "All inputs must produce the same template."
        )

    snippet = snippets[0]
    template = templates[0]

    # ------------------------------------------------------------------
    # 4. Validate template parses all inputs
    # ------------------------------------------------------------------
    for inp in inputs:
        rows = parse_textfsm_to_dicts(template, inp.content)
        if not rows:
            raise click.ClickException(
                f"Template failed to parse input or produced no records: "
                f"{file.path_name(inp.fullname)}"
            )

    # ------------------------------------------------------------------
    # 5. Load + update manifest
    # ------------------------------------------------------------------
    manifest = golden_case.data.load_manifest()
    manifest["author"] = author

    # ------------------------------------------------------------------
    # 6. Determine output directory (sandbox or real)
    # ------------------------------------------------------------------
    out_dir = case_path
    temp_dir = None

    if sandbox or sandbox_keep:
        temp_dir = case_path.with_suffix(".temp")
        out_dir = temp_dir

        if verbose:
            click.echo(
                f"[sandbox] Using temporary directory: {file.path_name(temp_dir)}"
            )

        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        shutil.copytree(case_path, temp_dir)

    manifest_path = out_dir / "manifest.json"
    expected_dir = out_dir / "expected"
    results_dir = out_dir / "expected_results"

    # ------------------------------------------------------------------
    # 7. Dry-run mode
    # ------------------------------------------------------------------
    if dry_run:
        click.echo("[DRY-RUN] Would write:")
        click.echo(f"  manifest → {file.path_name(manifest_path)}")
        click.echo(f"  snippet → {file.path_name(expected_dir / 'snippet.txt')}")
        click.echo(f"  template → {file.path_name(expected_dir / 'textfsm.template')}")

        for inp in inputs:
            base = Path(inp.fullname).stem
            click.echo(
                f"  result → {file.path_name(results_dir / f'{base}_result.json')}"
            )
        return 0

    # ------------------------------------------------------------------
    # 8. Write manifest
    # ------------------------------------------------------------------
    manifest_path.write_text(json.dumps(manifest, indent=2))
    if verbose:
        click.echo(f"[write] {file.path_name(manifest_path)}")

    # ------------------------------------------------------------------
    # 9. Write snippet + template
    # ------------------------------------------------------------------
    expected_dir.mkdir(parents=True, exist_ok=True)
    (expected_dir / "snippet.txt").write_text(snippet)
    (expected_dir / "textfsm.template").write_text(template)

    if verbose:
        click.echo(f"[write] {file.path_name(expected_dir / 'snippet.txt')}")
        click.echo(f"[write] {file.path_name(expected_dir / 'textfsm.template')}")

    # ------------------------------------------------------------------
    # 10. Write expected_results
    # ------------------------------------------------------------------
    results_dir.mkdir(parents=True, exist_ok=True)

    for builder, inp in zip(builders, inputs):
        base = Path(inp.fullname).stem
        result_path = results_dir / f"{base}_result.json"

        result_path.write_text(json.dumps(builder.result, indent=2))

        if verbose:
            click.echo(f"[write] {file.path_name(result_path)}")

    # ------------------------------------------------------------------
    # 11. Optional summary
    # ------------------------------------------------------------------
    if summary:
        click.echo("")
        click.echo("[SUMMARY]")
        click.echo(f"  Inputs  : {len(inputs)}")
        click.echo(f"  Snippet : {file.path_name(expected_dir / 'snippet.txt')}")
        click.echo(f"  Template: {file.path_name(expected_dir / 'textfsm.template')}")
        click.echo(f"  Manifest: {file.path_name(manifest_path)}")
        click.echo(f"  Results : {len(inputs)} files")

    # ------------------------------------------------------------------
    # 12. Cleanup sandbox
    # ------------------------------------------------------------------
    if sandbox and temp_dir:
        shutil.rmtree(temp_dir)
        if verbose:
            click.echo("[sandbox] Temporary directory removed")

    # ------------------------------------------------------------------
    # 13. Final message
    # ------------------------------------------------------------------
    click.echo(f"[SUCCESS] Generated golden test artifacts for {golden_case.name}")

    if open_after:
        _open_directory(case_path)

    return 0
