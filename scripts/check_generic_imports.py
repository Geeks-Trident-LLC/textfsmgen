# scripts/check_generic_imports.py
"""
This script walks all `generic.py` files under the `textfsmgen` package,
parses their imports using `ast`, and reports any import whose top‑level
module is not part of the current interpreter's standard library.

It exits with status 1 if any forbidden imports are found.
"""

import ast
import sys
import sysconfig
from pathlib import Path


def load_stdlib_modules():
    """
    Return a set of top‑level standard‑library module names for the current interpreter.

    This uses `sysconfig.get_paths()["stdlib"]` to locate the stdlib directory,
    then collects both:
    - top‑level `.py` modules
    - compiled extension modules (`.so`, `.pyd`)
    - stdlib packages (directories)

    Returns
    -------
    set[str]
        A set of module names such as {"os", "sys", "pathlib"}.
    """
    stdlib_path = Path(sysconfig.get_paths()["stdlib"])
    modules = set()

    for entry in stdlib_path.iterdir():
        name = entry.name

        # Python files and compiled extensions
        if name.endswith((".py", ".so", ".pyd")):
            modules.add(name.split(".")[0])
        # Packages
        elif entry.is_dir():
            modules.add(name)

    return modules


STDLIB = load_stdlib_modules()
errors = []

for path in Path("textfsmgen").rglob("generic.py"):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                name = node.names[0].name
            else:
                name = node.module or ""

            top = name.split(".")[0]

            if top not in STDLIB:
                errors.append(f"{path}:{node.lineno} — forbidden import '{name}'")

if errors:
    print("\n".join(errors))
    sys.exit(1)
