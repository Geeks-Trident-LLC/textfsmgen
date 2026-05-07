import json
import hashlib
from pathlib import Path
from .utils import iter_testcases, get_inputs_and_results

def hash_file(path: Path):
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()

def generate_index():
    index = {}
    for kind, case, case_dir in iter_testcases():
        entry = {
            "kind": kind,
            "case": case,
            "snippet_hash": hash_file(case_dir / "snippet.txt"),
            "template_hash": hash_file(case_dir / "template.txt"),
            "results": {},
        }

        for basename, _, _, result_path in get_inputs_and_results(kind, case):
            entry["results"][basename] = hash_file(result_path)

        index[f"{kind}/{case}"] = entry

    out = Path(__file__).parent / "index.json"
    out.write_text(json.dumps(index, indent=2))
    return out
