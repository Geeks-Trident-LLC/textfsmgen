# 🟡 Golden Tests for `textfsmgen`

Golden tests ensure that `textfsmgen` produces **stable, deterministic output** for a wide variety of input samples.  
Each golden case captures:

- the **expected snippet**
- the **expected template**
- the **expected parsed results**
- metadata describing the case

When the generator changes intentionally, golden files are updated.  
When it changes unintentionally, golden tests fail — protecting you from regressions.

---

## 📁 Folder Structure

Each golden case lives under:

```
tests/integration/golden/<kind>/<case>/
```

A typical case looks like:

```
snippet.txt
template.txt
config.json
meta.json
input/
    sample1.txt
    sample2.txt
expected/
    sample1_result.json
    sample2_result.json
```

### Required files

| File           | Purpose                                                            |
|----------------|--------------------------------------------------------------------|
| `snippet.txt`  | Expected snippet output                                            |
| `template.txt` | Expected TextFSM template                                          |
| `config.json`  | Parameters for the builder (author, description, notes, overrides) |
| `meta.json`    | Auto‑generated metadata (timestamp, tester, etc.)                  |
| `input/`       | Raw input samples                                                  |
| `expected/`    | Expected parsed results for each input sample                      |

Missing or malformed files will cause schema validation errors.

---

## ▶️ Running Golden Tests

Run all golden tests:

```
pytest tests/integration/golden
```

Run the entire suite (golden tests included):

```
pytest
```

Run a specific golden case:

```
pytest --golden-case category_form/cisco
```

---

## 📋 Listing Golden Cases

```
pytest --list-golden
```

Output example:

```
Golden Test Cases:

  category_form/cisco
  category_form/juniper
  interface/show_ip
```

---

## ✨ Creating a New Golden Case

Using pytest:

```
pytest --new-golden category_form/new_case
```

Using the CLI tool:

```
textfsmgen-golden new category_form/new_case
```

This scaffolds:

```
tests/integration/golden/category_form/new_case/
```

with empty input/expected folders and placeholder files.

---

## 🔄 Updating Golden Files

When generator logic changes intentionally:

```
pytest --update-golden --tester "Tuyen"
```

Requirements:

- `--tester` must be provided  
  **unless** `config.json` contains `"author": "..."`.

This updates:

- `snippet.txt`
- `template.txt`
- all `expected/*.json`
- `meta.json`

---

## 🧪 How Golden Tests Work

Each test case is parametrized automatically by the plugin:

```python
def test_api(golden_case, run_golden_test):
    kind, case = golden_case
    run_golden_test(kind, case)
```

The plugin:

1. Loads parameters from `config.json`
2. Builds snippet + template using `CategoryTemplateBuilder`
3. Compares them to expected files  
   (with colorized diffs on mismatch)
4. Runs `verify_textfsm` against each input sample
5. Compares parsed results to expected JSON
6. Writes updated files when `--update-golden` is used

---

## 🧩 Schema Validation

Each golden case is validated for:

- required files present  
- required folders present  
- no malformed JSON  
- no missing expected results  
- warnings for unexpected files

This prevents silent corruption of golden cases.

---

## 📊 Golden Index (Drift Tracking)

Generate a reproducibility index:

```
textfsmgen-golden index
```

This produces:

```
tests/integration/golden/index.json
```

containing:

- all golden cases  
- snippet/template hashes  
- expected result hashes  
- last updated timestamp  
- author  

Useful for:

- detecting drift  
- verifying reproducibility  
- CI checks  

---

## 🧰 Developer Tools

### CLI

```
textfsmgen-golden new <kind>/<case>
textfsmgen-golden index
```

### Plugin Tests

Golden plugin behavior is validated via:

```
tests/integration/golden/test_plugin_behavior.py
```

Ensuring:

- plugin loads correctly  
- scaffolding works  
- listing works  
- parametrization works  

---

## 🤝 Contributing

When adding or modifying golden cases:

1. Add new input samples under `input/`
2. Run:

   ```
   pytest --update-golden --tester "<your name>"
   ```

3. Review diffs carefully  
4. Commit updated golden files  
5. Regenerate index:

   ```
   textfsmgen-golden index
   ```