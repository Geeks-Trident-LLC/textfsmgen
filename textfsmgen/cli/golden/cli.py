# ruff: noqa: E402

from __future__ import annotations

import click
from typing import cast

from .commands.run import cmd_run
from .commands.regen import cmd_regen
from .commands.diff import cmd_diff
from .commands.drift import cmd_drift
from .commands.copy import cmd_copy
from .commands.duplicate import cmd_duplicate
from .commands.new import cmd_new
from .commands.generate import cmd_generate
from .commands.batch_generate import cmd_batch_generate
from .commands.batch_regen import cmd_batch_regen
from .commands.batch_quicktest import cmd_batch_quicktest
from .commands.merge import cmd_merge
from .commands.merge_review import cmd_merge_review
from .commands.merge_preview import cmd_merge_preview
from .commands.merge_diff import cmd_merge_diff
from .commands.merge_plan import cmd_merge_plan
from .commands.identical import cmd_identical
from .commands.promote import cmd_promote
from .commands.promote_plan import cmd_promote_plan
from .commands.promote_review import cmd_promote_review


__version__ = "1.0.0"

__all__ = [
    "cli",
    "__version__",
]


@click.group(
    help="Golden test utilities for TextFSMGen.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.version_option(
    version=__version__,
    prog_name="textfsmgen-golden-tests",
    message="%(prog)s %(version)s",
)
@click.option("--time", is_flag=True, help="Show execution time for the command.")
@click.pass_context
def cli(ctx, time):
    """Golden test utilities for TextFSMGen."""
    ctx.ensure_object(dict)
    ctx.obj["time"] = time


@cli.command(name="version", help="Show the Golden Tests CLI version.")
def version():
    click.echo(f"textfsmgen-golden-tests {__version__}")


cli.add_command(cast(click.Command, cmd_run))
cli.add_command(cast(click.Command, cmd_regen))
cli.add_command(cast(click.Command, cmd_diff))
cli.add_command(cast(click.Command, cmd_drift))
cli.add_command(cast(click.Command, cmd_copy))
cli.add_command(cast(click.Command, cmd_duplicate))
cli.add_command(cast(click.Command, cmd_new))
cli.add_command(cast(click.Command, cmd_generate))
cli.add_command(cast(click.Command, cmd_batch_generate))
cli.add_command(cast(click.Command, cmd_batch_regen))
cli.add_command(cast(click.Command, cmd_batch_quicktest))

cli.add_command(cast(click.Command, cmd_merge))
cli.add_command(cast(click.Command, cmd_merge_review))
cli.add_command(cast(click.Command, cmd_merge_preview))
cli.add_command(cast(click.Command, cmd_merge_diff))
cli.add_command(cast(click.Command, cmd_merge_plan))

cli.add_command(cast(click.Command, cmd_identical))

cli.add_command(cast(click.Command, cmd_promote))
cli.add_command(cast(click.Command, cmd_promote_plan))
cli.add_command(cast(click.Command, cmd_promote_review))
