from __future__ import annotations

import json
import shutil
from pathlib import Path
import click

from textfsmgen import parse_textfsm_to_dicts

from textfsmgen.libs import file
from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors
from .copy import _open_directory


@catch_path_errors
def generate(
    case_path,
    dry_run=False,
    sandbox=False,
    sandbox_keep=False,
    open_after=False,
    verbose=False,
):
    """
    Generate snippet, template, and expected_results for a golden test case.
    """
    golden_case = GoldenCase.from_path(case_path)

    if verbose:
        click.echo(f"[info] Loading inputs from {golden_case.name}")

    # 1. Load inputs
    inputs = list(golden_case.data.load_inputs())
    if not inputs:
        raise click.ClickException(f"No inputs found in {golden_case.name}/inputs")

    snippets = []
    templates = []
    builders = []

    # 2. Build for each input
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

    # 3. Ensure exactly one snippet and one template
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

    # 4. Validate template parses inputs
    for inp in inputs:
        rows = parse_textfsm_to_dicts(template, inp.content)
        if not rows:
            raise click.ClickException(
                f"Template failed to parse input or produced no records: {file.path_name(inp.fullname)}"
            )

    # 5. Determine output directory (sandbox or real)
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

    # 6. Dry-run mode
    if dry_run:
        click.echo("[DRY-RUN] Would write:")
        click.echo(f"  snippet → {file.path_name(out_dir / 'expected/snippet.txt')}")
        click.echo(
            f"  template → {file.path_name(out_dir / 'expected/textfsm.template')}"
        )
        for inp in inputs:
            base = Path(inp.fullname).stem
            click.echo(
                f"  result → {file.path_name(out_dir / 'expected_results' / f'{base}_result.json')}"
            )
        return

    # 7. Write snippet + template
    expected_dir = out_dir / "expected"
    expected_dir.mkdir(parents=True, exist_ok=True)

    (expected_dir / "snippet.txt").write_text(snippet)
    (expected_dir / "textfsm.template").write_text(template)

    # 8. Write expected_results
    results_dir = out_dir / "expected_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    for inp in inputs:
        base = Path(inp.fullname).stem
        result_path = results_dir / f"{base}_result.json"

        builder = golden_case.data.build(inp.content)
        result = builder.result

        result_path.write_text(json.dumps(result, indent=2))

        if verbose:
            click.echo(f"[write] {file.path_name(result_path)}")

    # 9. Cleanup sandbox
    if sandbox and temp_dir:
        shutil.rmtree(temp_dir)
        if verbose:
            click.echo("[sandbox] Temporary directory removed")

    # 10. Final message
    click.echo(f"[SUCCESS] Generated golden test artifacts for {golden_case.name}")

    if open_after:
        _open_directory(case_path)
