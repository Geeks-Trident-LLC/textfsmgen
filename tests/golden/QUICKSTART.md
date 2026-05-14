# 🚀 Golden Tests Quick‑Start

This guide shows the **fastest way** to work with golden tests using the `textfsmgen tester` CLI.  
If you only read one document, read this one.

---

## 🧪 1. Run a Golden Test Case

```
textfsmgen tester run <case>
```

Example:

```
textfsmgen tester run tests/golden/integration/show_version
```

Runs the case non‑destructively and reports mismatches.

---

## ⚡ 2. Quicktest (fast validation)

```
textfsmgen tester quicktest <case>
```

Quickly checks:

- template generation  
- snippet parsing  
- expected results  

Useful during development.

---

## 🔄 3. Regenerate a Case

Regenerates all **derived** files for a single case:

```
textfsmgen tester regen <case>
```

Use this when:

- manifest.json changes  
- canonical/expected snippet or template changes  
- input samples change  
- expected behavior intentionally changes  

---

## 🆕 4. Create a New Case

```
textfsmgen tester new <case>
```

Creates a scaffolded case directory (auto‑detects main vs integration).

---

## 📥 5. Create a Case From Input Samples

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

## 📑 6. Duplicate or Copy a Case

Duplicate (auto‑named):

```
textfsmgen tester duplicate <author> <src>
```

Copy (explicit destination):

```
textfsmgen tester copy <author> <src> <dst>
```

---

## 🔍 7. Diff a Case

```
textfsmgen tester diff <case>
```

Shows differences between expected and generated results.

---

## 🛡️ 8. Detect Drift

```
textfsmgen tester drift <case>
```

Reports whether the case is out of sync with its golden state.

---

## 🧭 9. Typical Workflow

1. Edit template/snippet/manifest  
2. Run quicktest  
3. If behavior changed intentionally → regenerate  
4. Commit authoritative + derived files  
5. Open PR

---

# 🆚 **CLI vs Pytest Workflows (Side‑by‑Side Comparison)**

This table makes the distinction crystal clear for contributors.

| Purpose                        | **CLI Tester (`textfsmgen tester …`)**              | **Pytest (`pytest tests/golden …`)**              |
|--------------------------------|-----------------------------------------------------|---------------------------------------------------|
| **Primary Use**                | Day‑to‑day development                              | CI validation + regeneration                      |
| **Who uses it**                | Developers editing cases                            | CI, reviewers, maintainers                        |
| **Scope**                      | Single case or batch of cases                       | Entire golden suite                               |
| **Typical Actions**            | run, quicktest, regen, diff, copy, duplicate, merge | validate, drift‑check, regenerate all             |
| **Regeneration**               | Per‑case (`tester regen <case>`)                    | All cases (`pytest --regen-golden`)               |
| **Drift Detection**            | Per‑case (`tester drift <case>`)                    | Automatic during test run                         |
| **Speed**                      | Fast, targeted                                      | Slower, full suite                                |
| **When to use**                | While developing or modifying a case                | Before commit, CI, or after authoritative changes |
| **Edits authoritative files?** | Yes                                                 | Yes                                               |
| **Edits derived files?**       | Yes (per case)                                      | Yes (all cases)                                   |
| **Entry Point**                | `textfsmgen tester <action>`                        | `pytest tests/golden`                             |

### **Mental Model**
- **CLI = your daily toolbelt**  
- **Pytest = the final judge**  

---

# 🔁 **Quickstart Flowchart (Developer Workflow)**

A compact, visual flow that matches your CLI Quickstart.

```
                   ┌──────────────────────────┐
                   │   Start Working on Case  │
                   └─────────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────┐
                     │ Edit authoritative │
                     │ files (manifest,   │
                     │ snippet, template, │
                     │ inputs)            │
                     └─────────────┬──────┘
                                   │
                                   ▼
                     ┌────────────────────┐
                     │ Run quicktest      │
                     │ textfsmgen tester  │
                     │ quicktest <case>   │
                     └─────────────┬──────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │  Quicktest passes?         │
                     └─────────────┬──────────────┘
                                   │Yes
                                   │
                                   ▼
                     ┌──────────────────────────┐
                     │   Continue development   │
                     └─────────────┬────────────┘
                                   │No
                                   ▼
                     ┌──────────────────────────┐
                     │ Inspect diff             │
                     │ textfsmgen tester diff   │
                     │ <case>                   │
                     └─────────────┬────────────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │  Change intentional?       │
                     └─────────────┬──────────────┘
                                   │Yes
                                   │
                                   ▼
                     ┌──────────────────────────┐
                     │ Regenerate case          │
                     │ textfsmgen tester regen  │
                     │ <case>                   │
                     └─────────────┬────────────┘
                                   │
                                   ▼
                     ┌──────────────────────────┐
                     │ Commit authoritative +   │
                     │ derived files            │
                     └─────────────┬────────────┘
                                   │No
                                   ▼
                     ┌──────────────────────────┐
                     │ Fix authoritative files  │
                     └─────────────┬────────────┘
                                   │
                                   ▼
                     (loop back to quicktest)
```

---

## 📝 Summary

- Use the **CLI** for all day‑to‑day golden test work  
- Use **pytest** only for CI and full‑suite validation  
- If you change authoritative files, run:
