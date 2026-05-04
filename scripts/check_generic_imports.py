# scripts/check_generic_imports.py
import ast, sys
from pathlib import Path

STDLIB = sys.stdlib_module_names  # Python 3.10+; use `isort` for 3.9

errors = []
for path in Path("textfsmgen").rglob("generic.py"):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            name = (node.names[0].name if isinstance(node, ast.Import)
                    else node.module or "")
            top = name.split(".")[0]
            if top not in STDLIB:
                errors.append(f"{path}:{node.lineno} — forbidden import '{name}'")

if errors:
    print("\n".join(errors))
    sys.exit(1)