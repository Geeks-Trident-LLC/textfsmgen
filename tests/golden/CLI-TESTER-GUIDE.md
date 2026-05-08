
# 📘 **CLI Tester Guide**

---

# 🧩 **1. Overview**

Golden tests live under:

```
tests/golden/<category>/<case>/
```

Each case contains:

- **Authoritative files** (canonical/ or expected/)
- **Derived files** (expected_results/, meta.json, golden.hash)
- **Manifest** (manifest.json)
- **Inputs** (raw device output)
- **Expected results** (parsed JSON rows)

The tester CLI helps developers:

- create new cases  
- copy or duplicate existing cases  
- preview builder output  
- diff authoritative vs generated artifacts  
- regenerate derived files  
- validate correctness  

---

# 🗂️ **2. Action List**

```
textfsmgen tester list
textfsmgen tester info <case>

textfsmgen tester create <case> [flags]
textfsmgen tester create <case> --config <file>

textfsmgen tester copy author=<author> <target-case> <new-case>
textfsmgen tester duplicate author=<author> <target-case>

textfsmgen tester run <case>
textfsmgen tester drift <case>

textfsmgen tester preview-template <case>
textfsmgen tester preview-snippet <case>
textfsmgen tester preview-generated-template <case>
textfsmgen tester preview-results <case>

textfsmgen tester diff-template <case>
textfsmgen tester diff-snippet <case>
textfsmgen tester diff-results <case>

textfsmgen tester edit-manifest <case>
textfsmgen tester set <case> <field> <value>

textfsmgen tester regen <case>
textfsmgen tester regen-all

textfsmgen tester validate-manifest <case>
textfsmgen tester clean <case>
textfsmgen tester clean-all
```

---

# 📁 **3. Case Creation**

## **3.1 Create using flags**

```
textfsmgen tester create <case> \
    --category <main|integration|other> \
    --builder <builder-type> \
    [--saved] \
    [--author <name>] \
    [--email <email>]
```

## **3.2 Create using a config file**

```
textfsmgen tester create <case> --config <config-file>
```

Flags override config values.

---

# ⭐ **3.3 Unified Path Resolution Logic (Relative + Full Path)**

When creating a new test case, the CLI determines **where** to place `<case>` using the following ordered rules.  
The first matching rule wins.

## 📘 Path Resolution Table

| Rule  | `<pwd>` condition                                     | `<case>` is full path | Parent `tests/golden/<category>` exists     | Creation path                          |
|-------|-------------------------------------------------------|-----------------------|---------------------------------------------|----------------------------------------|
| **1** | `<pwd>` ends with `tests/golden/<category>`           | No                    | N/A                                         | `<pwd>/<case>`                         |
| **2** | `<pwd>` ends with `tests/golden`                      | No                    | `<pwd>/<category>` exists                   | `<pwd>/<category>/<case>`              |
| **3** | `<pwd>` ends with `tests`                             | No                    | `<pwd>/golden/<category>` exists            | `<pwd>/golden/<category>/<case>`       |
| **4** | `<pwd>/tests/golden/<category>` exists anywhere below | No                    | Yes                                         | `<pwd>/tests/golden/<category>/<case>` |
| **5** | `<case>` contains slashes                             | Yes                   | Ancestors include `tests/golden/<category>` | `<case>`                               |
| **6** | No rule matches                                       | N/A                   | N/A                                         | ❌ Error                                |

## ⭐ Summary

- If you’re inside the correct category → create directly  
- If inside `tests/golden` or `tests` → CLI finds the right category  
- If anywhere inside project → CLI searches for `tests/golden/<category>`  
- If full path → validated and used  
- If nothing matches → error with instructions  

---

# ⭐ **3.4 Files Created (Category‑Aware)**

## If category = `"main"`

```
<case>/manifest.json
<case>/canonical/result.json
<case>/canonical/sample.txt
<case>/canonical/snippet.txt
<case>/canonical/textfsm.template
<case>/inputs/
<case>/expected_results/
<case>/README.md
```

**Not created:**  
- `expected/`

---

## If category ≠ `"main"`

```
<case>/manifest.json
<case>/expected/snippet.txt
<case>/expected/textfsm.template
<case>/inputs/
<case>/expected_results/
<case>/README.md
```

**Not created:**  
- `canonical/`

---

## Quick Note About `golden.hash` and `meta.json`

These files **do not exist** in a newly created case.

If you see them later, it means the case has been:

- run  
- approved  
- regenerated  

They are **derived artifacts**, not authoritative files.

---

# ⭐ **3.5 Copying and Duplicating Cases**

## **3.5.1 Copy**

```
textfsmgen tester copy author=<author> <target-case> <new-case>
```

### Behavior
1. Locate `<target-case>`  
2. Determine category  
3. Create `<new-case>` using same path rules as `create`  
4. Copy authoritative files only  
   - main → copy `canonical/` + `inputs/`  
   - non‑main → copy `expected/` + `inputs/`  
5. Do **not** copy derived files  
6. Create fresh manifest.json  
7. Run quick test → generate new expected_results, meta.json, golden.hash  
8. Print next steps  

---

## **3.5.2 Duplicate**

```
textfsmgen tester duplicate author=<author> <target-case>
```

Equivalent to:

```
copy <target-case> <target-case>-duplicated
```

If name exists, append numeric suffix:

```
-duplicated-2
-duplicated-3
```

---

# 🧪 **4. Running and Validating a Case**

```
textfsmgen tester run <case>
textfsmgen tester drift <case>
```

---

# 🔍 **5. Preview Commands (Non‑Mutating)**

```
textfsmgen tester preview-template <case>
textfsmgen tester preview-snippet <case>
textfsmgen tester preview-generated-template <case>
textfsmgen tester preview-results <case>
```

---

# 🧭 **6. Diff Commands (Non‑Mutating)**

```
textfsmgen tester diff-template <case>
textfsmgen tester diff-snippet <case>
textfsmgen tester diff-results <case>
```

---

# 📝 **7. Manifest Editing (Mutating)**

```
textfsmgen tester edit-manifest <case>
textfsmgen tester set <case> <field> <value>
```

---

# 🔄 **8. Regeneration**

```
textfsmgen tester regen <case>
textfsmgen tester regen-all
```

---

# 🧹 **9. Maintenance**

```
textfsmgen tester validate-manifest <case>
textfsmgen tester clean <case>
textfsmgen tester clean-all
```

---

# 🧭 **10. Typical Developer Workflow**

1. Modify code or templates  
2. Run a single case  
3. Inspect diffs if drift detected  
4. Regenerate if intentional  
5. Commit authoritative + derived files  
6. Push PR  

---

# 📘 **11. Manifest Schema Documentation**

---

## ⭐ 11.1 Manifest Structure (Top‑Level)

```json
{
  "builder": "...",
  "parameters": { ... },
  "meta": { ... }
}
```

| Field        | Type   | Required | Description                                    |
|--------------|--------|----------|------------------------------------------------|
| `builder`    | string | yes      | Builder type (`tabular`, `category`)           |
| `parameters` | object | yes      | Builder‑specific configuration                 |
| `meta`       | object | yes      | Metadata (author, saved state, schema version) |

---

## ⭐ 11.2 Builder Field

Allowed values:

- `"tabular"`
- `"category"`

Changing builder requires regeneration.

---

# ⭐ 11.3 Builder‑Specific Parameter Schemas

## 11.3.1 `"category"` Builder

### Schema
```json
{
  "builder": "category",
  "parameters": {
    "user_data": "",
    "user_data_file": "",
    "count": 1,
    "separator": ":",
    "starting_from": null,
    "ending_at": null,
    "replacing_rules": null
  }
}
```

### Field Descriptions

| Field           | Type        | Default | Description                                 |
|-----------------|-------------|---------|---------------------------------------------|
| user_data       | string      | ""      | Inline input data or canonical sample       |
| user_data_file  | string      | ""      | File path for input data                    |
| count           | int         | 1       | Number of `(key, value)` pairs              |
| separator       | string      | ":"     | Key/value separator                         |
| starting_from   | string/null | null    | Start marker (raw or `"--regex <pattern>"`) |
| ending_at       | string/null | null    | End marker (raw or `"--regex <pattern>"`)   |
| replacing_rules | list/null   | null    | Post‑processing rules                       |

---

## 11.3.2 `"tabular"` Builder

### Schema
```json
{
  "builder": "tabular",
  "parameters": {
    "user_data": "",
    "user_data_file": "",
    "column_divider": "",
    "column_count": 0,
    "column_widths": null,
    "headers": null,
    "header_rows": null,
    "custom_header_text": "",
    "starting_from": null,
    "ending_at": null,
    "has_header_row": true,
    "replacing_rules": null
  }
}
```

### Field Descriptions

| Field              | Type             | Default | Description                      |
|--------------------|------------------|---------|----------------------------------|
| user_data          | string           | ""      | Inline input data                |
| user_data_file     | string           | ""      | File path for input data         |
| column_divider     | string           | ""      | Column separator                 |
| column_count       | int              | 0       | Number of columns                |
| column_widths      | list/string/null | null    | Widths (`"10,12"` or `[10,12]`)  |
| headers            | list/string/null | null    | Headers (`"A,B"` or `["A","B"]`) |
| header_rows        | string/null      | null    | Multi‑line header text           |
| custom_header_text | string           | ""      | Override for headerless tables   |
| has_header_row     | bool             | true    | Whether table has a header       |
| starting_from      | string/null      | null    | Start marker                     |
| ending_at          | string/null      | null    | End marker                       |
| replacing_rules    | list/null        | null    | Post‑processing rules            |

---

# ⭐ 11.4 `meta` Field

```json
"meta": {
  "saved": true,
  "author": "John",
  "email": "",
  "description": "",
  "notes": "",
  "schema_version": "1.0"
}
```

---

# ⭐ 11.5 Validation Rules

A manifest is valid if:

- required fields exist  
- builder is known  
- parameters match builder schema  
- meta contains required fields  
- no derived fields appear  

---

# ⭐ 11.6 Summary

- `manifest.json` defines how a test case is built  
- `builder` determines which parameters apply  
- `"--regex "` prefix enables regex markers  
- `replacing_rules` supports iterative refinement  
- Changing manifest requires regeneration  
- `golden.hash` and `meta.json` are derived  
