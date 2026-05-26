from __future__ import annotations

import functools
import json
import sys
import time as time_module
from io import StringIO

import click


def integration_only(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        base = kwargs.get("base")
        if not base:
            return func(*args, **kwargs)

        from .core.golden_case import GoldenCase

        # If base is a case, enforce integration
        try:
            gc = GoldenCase.from_path(base)
            if not gc.is_integration():
                cmd_name = func.__name__.replace("_", "-")
                raise click.ClickException(
                    f"{cmd_name!r} only works on integration cases, "
                    f"but {gc.name!r} is categorized as: main"
                )
        except Exception:  # noqa
            # If base is a directory containing cases, we validate per-case later
            pass

        return func(*args, **kwargs)

    return wrapper


def validate_sandbox_flags(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sandbox = kwargs.get("sandbox", False)
        sandbox_keep = kwargs.get("sandbox_keep", False)
        dry_run = kwargs.get("dry_run", False)
        open_after = kwargs.get("open_after", False)

        if sandbox and sandbox_keep:
            raise click.ClickException(
                "Cannot use --sandbox and --sandbox-keep together."
            )

        if dry_run and (sandbox or sandbox_keep):
            raise click.ClickException(
                "--dry-run cannot be combined with sandbox modes."
            )

        if open_after and (sandbox or sandbox_keep):
            raise click.ClickException(
                "--open-after cannot be used with sandbox modes."
            )

        return func(*args, **kwargs)

    return wrapper


def timed_command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ctx = click.get_current_context(silent=True)
        timing_enabled = bool(ctx and ctx.obj and ctx.obj.get("time"))
        json_mode = kwargs.get("json_mode", False)

        # ------------------------------------------------------------
        # FAST PATH: timing disabled → run normally, no stdout capture
        # ------------------------------------------------------------
        if not timing_enabled:
            return func(*args, **kwargs)

        # ------------------------------------------------------------
        # TIMING ENABLED → capture stdout
        # ------------------------------------------------------------
        buffer = StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer

        start = time_module.perf_counter()
        try:
            rc = func(*args, **kwargs)
        finally:
            end = time_module.perf_counter()
            sys.stdout = old_stdout

        output = buffer.getvalue()
        elapsed = end - start

        # ------------------------------------------------------------
        # JSON MODE
        # ------------------------------------------------------------
        if json_mode:
            json_obj = _safe_json_parse(output)
            wrapped = {
                "time": f"{elapsed:.3f}",
                "output": json_obj,
            }
            click.echo(json.dumps(wrapped, indent=2, ensure_ascii=False))
            return rc

        # ------------------------------------------------------------
        # RAW MODE
        # ------------------------------------------------------------
        click.echo(output, nl=False)
        click.echo(f"[TIME] Completed in {elapsed:.3f}s")
        return rc

    return wrapper


def _safe_json_parse(text):
    try:
        return json.loads(text)
    except Exception:  # noqa
        return None
