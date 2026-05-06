# 🟡 Golden Tests

Golden tests ensure that TextFSM template generation and parsing remain stable over time.  
Each golden case defines:

- A **canonical sample** (raw device output)
- The **expected snippet**
- The **expected TextFSM template**
- The **expected parsed result**
- Optional **additional input samples** and their expected results

Golden tests live under:

```
tests/golden/
```

Each case is a directory containing a `manifest.json` and supporting files.

---

## 📁 Directory Structure

```
tests/
  golden/
    README.md
    conftest.py
    test_api.py
    <case-name>/
      manifest.json
      canonical/
        sample.txt
        expected_snippet.txt
        expected_textfsm.template
        expected_result.json
      inputs/
        <input>.txt
      expected/
        <input>_result.json
```

---

# 🚀 Running Golden Tests

### Run full test suite (golden tests skipped)

```
pytest
```

Golden tests are collected but **not executed** unless explicitly enabled.

---

### Run only golden tests (fast)

```
pytest tests/golden
```

Golden tests are still **skipped** unless golden mode is enabled.

---

### Run golden tests with golden mode enabled

```
pytest --enable-golden tests/golden
```

This activates the golden test framework:

- Loads each manifest  
- Builds templates  
- Compares snippet/template  
- Verifies canonical parsing  
- Verifies all input samples  

---

# 🔍 Optional Flags

### `--diff-golden` — Show unified diff on mismatch

```
pytest --enable-golden --diff-golden tests/golden
```

Prints a unified diff when snippet/template mismatch occurs.

---

### `--debug-golden` — Print detailed case information

```
pytest --enable-golden --debug-golden tests/golden
```

Shows:

- Case name  
- Manifest contents  
- Canonical file paths  
- Input sample list  
- Builder class name  

Useful when adding or troubleshooting cases.

---

# 🧩 Manifest Format

Each golden case includes a `manifest.json`:

```json
{
  "case": "<case-name>",
  "kind": "tabular",
  "parameters": {},
  "canonical": {
    "sample": "canonical/sample.txt",
    "snippet": "canonical/expected_snippet.txt",
    "template": "canonical/expected_textfsm.template",
    "result": "canonical/expected_result.json"
  },
  "inputs": []
}
```

- `case` — name of the golden case  
- `kind` — parser type (e.g., `"tabular"`)  
- `parameters` — optional builder parameters  
- `canonical` — canonical reference files  
- `inputs` — list of additional input samples (auto-discovered from filesystem)

---

# 🛠 Scaffolding New Golden Cases

Use the scaffolder script:

```
tools/new_golden_case.py
```

### Create a new case:

```
python tools/new_golden_case.py <case-name>
```

Example:

```
python tools/new_golden_case.py windows_ls
```

### The scaffolder creates:

```
tests/golden/<case-name>/
  manifest.json
  canonical/
    sample.txt
    expected_snippet.txt
    expected_textfsm.template
    expected_result.json
  inputs/
  expected/
```

### Next steps:

1. Fill in `canonical/sample.txt` with real device output  
2. Generate and save:
   - `expected_snippet.txt`
   - `expected_textfsm.template`
   - `expected_result.json`
3. Add input samples under `inputs/`
4. Add expected results under `expected/`
5. Run:

```
pytest --enable-golden --diff-golden tests/golden
```

---

# 🧪 Makefile Target

Add this to your project’s `Makefile`:

```makefile
.PHONY: golden
golden:
	pytest --enable-golden --diff-golden tests/golden
```

Run with:

```
make golden
```

---

# 🎯 Summary

Golden tests provide:

- Stable template generation  
- Stable parsing behavior  
- Easy debugging via diffs  
- Fast case creation via scaffolder  
- Clean, predictable directory structure  
