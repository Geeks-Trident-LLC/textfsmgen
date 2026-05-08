# 🧩 Golden Test Workflow: Manifest Changes & Regeneration

Golden tests in this project rely on a strict separation between:

- **Authoritative files** — the human‑approved truth  
- **Derived files** — machine‑generated outputs that depend on the authoritative truth  

Understanding this separation is essential for anyone modifying golden test cases.

---

## 📘 Authoritative Files (Never auto‑rewritten)

These files define the *intended* behavior of a golden test case:

```
manifest.json
canonical/snippet.txt
canonical/textfsm.template
expected/snippet.txt
expected/textfsm.template
```

They are written or edited **only by humans** (test authors, reviewers, or CLI testers).

These files represent the *correct* template, snippet, and configuration for the test case.

> If any authoritative file changes, the meaning of the golden test changes.

---

## 📗 Derived Files (Always regenerated)

These files are produced automatically from authoritative files:

```
canonical/result.json
expected_results/*.json
meta.json
golden.hash
```

They are rewritten during regeneration and must never be edited manually.

---

## 🔄 When You Must Regenerate

If **any authoritative file changes**, you must regenerate the derived files.

This includes:

- Editing `manifest.json`
- Changing `builder_type`
- Changing `parameters`
- Updating canonical snippet or template
- Updating expected snippet or template
- Adding or modifying input samples

### ✔ Required command:

```
pytest tests/golden --regen-golden
```

This command:

- Recomputes canonical result.json  
- Recomputes expected_results/*.json  
- Rewrites meta.json  
- Rewrites golden.hash  
- Ensures all derived files match the authoritative truth  

---

## 🧪 Why Regeneration Is Required After Manifest Changes

`manifest.json` is authoritative configuration.  
It controls:

- Which builder is used  
- How templates are generated  
- How inputs are parsed  
- How expected_results should look  

If `manifest.json` changes, the golden test’s behavior changes.

Regeneration ensures:

- expected_results match the new configuration  
- canonical result.json is updated  
- golden.hash reflects the new state  
- drift detection remains accurate  

Without regeneration, tests will fail or drift detection will trigger false positives.

---

## 🛡️ Drift Detection

During normal test runs:

```
pytest tests/golden
```

drift detection verifies that **all authoritative and derived files** match the stored `golden.hash`.

If any file changes unexpectedly, you’ll see:

```
Golden files drift detected. Run: pytest --regen-golden
```

This protects the repository from accidental edits.

> Note: `meta.json` is intentionally excluded from hashing because it contains volatile fields (timestamps, git commit, OS info).

---

## 📝 Summary for Contributors

- ✔ You may edit `manifest.json`  
- ✔ You may edit canonical/expected snippet or template  
- ✔ You may add or modify input samples  
- ❗ After any such change, you **must** run:

```
pytest tests/golden --regen-golden
```

- ✔ Never manually edit derived files  
- ✔ Drift detection ensures golden files stay consistent  
- ✔ Normal test runs validate correctness  


---

# 🧩 Golden File Lifecycle Diagram

```
                         ┌──────────────────────────┐
                         │      Author edits:       │
                         │  - manifest.json         │
                         │  - canonical snippet     │
                         │  - canonical template    │
                         │  - expected snippet      │
                         │  - expected template     │
                         └─────────────┬────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────┐
                         │   Authoritative Files    │
                         │  (Human-approved truth)  │
                         └─────────────┬────────────┘
                                       │
                                       │  Normal test run
                                       │  (pytest tests/golden)
                                       ▼
                         ┌──────────────────────────┐
                         │   Golden Test Runner     │
                         │  - Builds template       │
                         │  - Compares snippet      │
                         │  - Compares template     │
                         │  - Parses inputs         │
                         │  - Compares results      │
                         │  - Checks drift          │
                         └─────────────┬────────────┘
                                       │
                                       │  If mismatch or drift:
                                       │  “Run: pytest --regen-golden”
                                       ▼
                         ┌─────────────────────────────┐
                         │   Regeneration Mode         │
                         │  (pytest --regen-golden)    │
                         │                             │
                         │  Rewrites ONLY:             │
                         │   - canonical/result.json   │
                         │   - expected_results/*.json |
                         │   - meta.json               │
                         │   - golden.hash             │
                         │                             │
                         │  NEVER rewrites:            │
                         │   - manifest.json           │
                         │   - canonical snippet       │
                         │   - canonical template      │
                         │   - expected snippet        │
                         │   - expected template       │
                         └─────────────┬───────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────┐
                         │   Derived Golden Files   │
                         │  (Machine-generated)     │
                         └─────────────┬────────────┘
                                       │
                                       │  Drift detection hashes
                                       ▼
                         ┌───────────────────────────┐
                         │       golden.hash         │
                         │  (Hash of authoritative + │
                         │   derived files, except   │
                         │   meta.json)              │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────┐
                         │   Stable Golden State    │
                         │  (Ready for CI + review) │
                         └──────────────────────────┘
```

---
