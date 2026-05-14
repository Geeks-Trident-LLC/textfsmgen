# 🧩 Golden Tests

Golden tests use **Golden Master Testing**:  
you freeze a known‑good output (“the golden master”), and every future run must match it exactly.

This protects TextFSM parsing from silent regressions, template drift, and accidental edits.

Golden tests matter because they guarantee:

- stable parsing across real device outputs  
- safe refactoring of templates and builders  
- deterministic CI behavior  
- immediate detection of unintended changes  

If the golden output changes, it must be **intentional** and **regenerated**.

---

# ⭐ The Core Mental Model

Golden tests separate files into two groups:

## **1. Authoritative Files (human‑owned)**  
These define the *intended* behavior of the test case:

```
manifest.json
canonical/sample.txt
canonical/snippet.txt
canonical/textfsm.template
canonical/result.json
expected/snippet.txt
expected/textfsm.template
```

You **may edit** these.  
Changing any of them **changes the meaning** of the test.

---

## **2. Derived Files (machine‑generated)**  
These must always match the authoritative truth:

```
expected_results/*.json
meta.json
golden.hash
```

You **must not edit** these manually.  
They are rewritten during regeneration.

---

# 🔄 When You Must Regenerate

Regenerate whenever any authoritative file changes:

- manifest.json  
- builder type or parameters  
- canonical snippet/template  
- expected snippet/template  
- input samples  

### ✔ Command (the one you must remember)

```
pytest tests/golden --regen-golden
```

This rewrites:

- canonical/result.json  
- expected_results/*.json  
- meta.json  
- golden.hash  

and brings the golden test back into a stable state.

---

# 🛡️ Drift Detection

Normal test runs:

```
pytest tests/golden
```

verify that authoritative + derived files match `golden.hash`.

If anything drifts:

```
Golden files drift detected. Run: pytest --regen-golden
```

This prevents accidental edits from entering the repository.

(`meta.json` is excluded from hashing because it contains volatile fields.)

---

# 📝 Contributor Summary

- ✔ You may edit authoritative files  
- ✔ You may add or modify input samples  
- ❗ After any such change, run:

```
pytest tests/golden --regen-golden
```

- ✔ Never edit derived files  
- ✔ Drift detection protects the repo  
- ✔ Normal test runs validate correctness  

---

# 🔍 Golden Test Lifecycle (Compact)

```
Author edits authoritative files
        │
        ▼
pytest tests/golden
  - parse inputs
  - compare results
  - check drift
        │
   mismatch or drift
        ▼
pytest tests/golden --regen-golden
  rewrites:
    - canonical/result.json
    - expected_results/*.json
    - meta.json
    - golden.hash
        │
        ▼
Stable Golden State
```