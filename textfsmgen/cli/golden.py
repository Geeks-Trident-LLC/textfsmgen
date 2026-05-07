import click


def _import_dev_utils():
    """
    Import golden utilities from the local tests/ folder.
    This only works when running inside the project root.
    """
    try:
        from tests.integration.golden.utils import ensure_scaffold
        from tests.integration.golden.index import generate_index
        return ensure_scaffold, generate_index
    except ModuleNotFoundError:
        print(
            "ERROR: Golden CLI tools can only be run inside the project root.\n"
            "The 'tests/' folder is not available in installed packages.\n"
            "Run this command from the repository root:\n\n"
            "    python -m textfsmgen.cli.golden <command>\n"
        )
        raise SystemExit(1)


@click.group()
def golden():
    """Golden test utilities."""
    pass


@golden.command("new")
@click.argument("path")
def new_case(path):
    """Create a new golden test case: <kind>/<case>."""
    ensure_scaffold, _ = _import_dev_utils()   # <-- FIXED

    try:
        kind, case = path.split("/", 1)
    except ValueError:
        click.echo("ERROR: requires <kind>/<case>")
        raise SystemExit(1)

    case_dir = ensure_scaffold(kind, case)
    click.echo(f"Created golden case at: {case_dir}")


@golden.command("index")
def index_cmd():
    """Generate golden index.json."""
    _, generate_index = _import_dev_utils()    # <-- FIXED
    out = generate_index()
    click.echo(f"Generated index at: {out}")


def main():
    golden()


if __name__ == "__main__":
    main()
