from pathlib import Path

gold_root = Path(__file__).parent


def get_testcases(parent_path):
    for file_path in parent_path.glob("*"):
        name = file_path.name
        if (
            file_path.is_dir()
            and (not name.startswith("_") or not name.endswith("_"))
            and name[0].isalpha()
        ):
            yield str(file_path)
