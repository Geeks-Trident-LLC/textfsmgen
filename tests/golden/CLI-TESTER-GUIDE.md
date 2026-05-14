# 🧰 CLI Tester Guide  
**`textfsmgen tester <command>`**

The Tester CLI is the primary tool for developing, validating, and maintaining golden test cases.  
Use it during day‑to‑day development.  
Use pytest only for full‑suite validation and CI.

This guide covers all tester commands with short explanations and examples.

---

# 📌 1. Running & Validating Cases

## **run** — Full execution (non‑destructive)
Runs the case end‑to‑end: build → parse → compare.

```
textfsmgen tester run <case>
```

Example:
```
textfsmgen tester run tests/golden/integration/show_version
```

---

## **quicktest** — Fast validation
Runs a lightweight version of the test (no regeneration).

```
textfsmgen tester quicktest <case>
```

Use this while editing templates/snippets.

---

## **diff** — Compare expected vs generated
Shows differences between expected results and current output.

```
textfsmgen tester diff <case>
```

---

## **drift** — Detect drift
Checks whether the case is out of sync with its golden state.

```
textfsmgen tester drift <case>
```

---

# 🔄 2. Regeneration

## **regen** — Regenerate derived files for a single case
Rewrites:

- canonical/result.json  
- expected_results/*.json  
- meta.json  
- golden.hash  

```
textfsmgen tester regen <case>
```

Use this when authoritative files change.

---

# 🆕 3. Creating Cases

## **new** — Create a new case scaffold
Auto‑detects main vs integration.

```
textfsmgen tester new <case>
```

---

## **new-from-input** — Create a case from input samples
Generates snippet/template + expected results from an input folder.

```
textfsmgen tester new-from-input \
    --builder <builder> \
    --author <name> \
    <case> <inputs>
```

Example:
```
textfsmgen tester new-from-input \
    --builder ios_show_version \
    --author tuyen \
    tests/golden/integration/show_version \
    samples/show_version/
```

---

# 📁 4. Copying & Duplicating Cases

## **copy** — Copy a case to a new directory
```
textfsmgen tester copy <author> <src> <dst>
```

---

## **duplicate** — Duplicate a case with auto‑naming
```
textfsmgen tester duplicate <author> <src>
```

Creates `<src>_copy` or `<src>_copy2`, etc.

---

# 📦 5. Batch Operations

## **batch-generate**
Run `generate` on all cases under a directory.

```
textfsmgen tester batch-generate <root>
```

## **batch-regen**
Regenerate all cases under a directory.

```
textfsmgen tester batch-regen <root>
```

## **batch-quicktest**
Quicktest all cases under a directory.

```
textfsmgen tester batch-quicktest <root>
```

---

# 🔀 6. Merging Cases

## **merge**
Merge multiple integration cases into a new destination case.

```
textfsmgen tester merge --author <name> <dst> <src1> <src2> ...
```

---

## **merge-review**
Preview a merge using `<dst>` as the reference case (no writes).

```
textfsmgen tester merge-review <dst> <srcs...>
```

---

## **merge-preview**
Preview a merge by selecting a reference candidate automatically.

```
textfsmgen tester merge-preview <srcs...>
```

Options:
- `--compact`
- `--json`

---

## **merge-diff**
Diff merged expected_results against golden expected_results.

```
textfsmgen tester merge-diff <srcs...>
```

Options:
- `--compact`
- `--json`
- `--diff-count <n>`
- `--diff-names-only`

---

# 🔍 7. Identifying Duplicate Cases

## **identical**
Find integration cases that produce identical results.

```
textfsmgen tester identical <srcs...>
```

Options:
- `--compact`
- `--json`

---

# 🧭 8. Typical Developer Workflow

1. Edit authoritative files (manifest, snippet, template, inputs)  
2. Run quicktest  
   ```
   textfsmgen tester quicktest <case>
   ```
3. If behavior changed intentionally → regenerate  
   ```
   textfsmgen tester regen <case>
   ```
4. Inspect diffs if needed  
5. Commit authoritative + derived files  
6. Push and open PR  

---

# 📝 Summary

- Use the **CLI tester** for all day‑to‑day golden test work  
- Use **pytest** only for full‑suite validation and CI  
- If authoritative files change, run:  
  ```
  textfsmgen tester regen <case>
  ```
- Never edit derived files manually  
- Drift detection keeps cases stable  
