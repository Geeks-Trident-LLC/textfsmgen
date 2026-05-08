# 🚀 Developer Quick‑Start Guide

This guide gives new contributors everything they need to start working with the project’s development workflow, golden tests, and regeneration rules — without reading the entire documentation set.

---

## 🛠️ 1. Set Up Your Development Environment

Clone the repository:

```
git clone <repo-url>
cd textfsmgen
```

Install development dependencies:

```
pip install -r requirements-dev.txt
```

Run the full test suite:

```
pytest
```

Run only golden tests:

```
pytest tests/golden
```

---

## 🧪 2. Running Golden Tests

Golden tests validate:

- template generation  
- snippet parsing  
- expected results  
- drift detection  

To run only golden tests:

```
pytest tests/golden
```

If everything is correct, tests pass silently.

If something changed unexpectedly, you’ll see:

```
Golden files drift detected. Run: pytest --regen-golden
```

---

## 🔄 3. Regenerating Golden Files

Regeneration updates **derived** golden files:

- `canonical/result.json`
- `expected_results/*.json`
- `meta.json`
- `golden.hash`

Run regeneration:

```
pytest tests/golden --regen-golden
```

This is required whenever:

- you change `manifest.json`
- you change canonical or expected templates/snippets
- you add or modify input samples
- you intentionally update expected behavior

---

## 📘 4. Authoritative vs. Derived Files

### Authoritative (human‑edited, never auto‑rewritten)

```
manifest.json
canonical/snippet.txt
canonical/textfsm.template
expected/snippet.txt
expected/textfsm.template
```

These define the *intended* behavior of the golden test case.

### Derived (machine‑generated, always rewritten during regen)

```
canonical/result.json
expected_results/*.json
meta.json
golden.hash
```

These reflect the authoritative truth and must never be edited manually.

---

## 🧩 5. When You MUST Regenerate

You must run:

```
pytest tests/golden --regen-golden
```

after any of the following:

- You modify `manifest.json`
- You change canonical snippet or template
- You change expected snippet or template
- You add or modify input samples
- You intentionally update expected behavior

If you forget, drift detection will fail and remind you.

---

## 🛡️ 6. Drift Detection

During normal test runs:

```
pytest tests/golden
```

drift detection verifies that all golden files match the stored `golden.hash`.

If any file changes unexpectedly, you’ll see:

```
Golden hash mismatch. Run: pytest --regen-golden
```

This protects the repository from accidental edits.

> Note: `meta.json` is excluded from hashing because it contains volatile fields.

---

## 🧭 7. Typical Contributor Workflow

Here’s the real‑world flow most developers follow:

1. Make code changes  
2. Run golden tests  
   ```
   pytest tests/golden
   ```
3. If drift is detected, inspect the diff  
4. If the change is intentional, regenerate:  
   ```
   pytest tests/golden --regen-golden
   ```
5. Commit authoritative + derived files  
6. Push and open a PR  

This keeps golden tests stable and meaningful.

---

## 🎯 8. Adding a New Golden Test Case

1. Create a new directory under `tests/golden/<case-name>/`
2. Add:
   - `manifest.json`
   - `canonical/snippet.txt`
   - `canonical/textfsm.template`
   - `inputs/*.txt`
3. Run:
   ```
   pytest tests/golden --regen-golden
   ```
4. Commit everything

Done.

---

## 🧹 9. Common Mistakes to Avoid

- ❌ Editing derived files manually  
- ❌ Forgetting to regenerate after manifest changes  
- ❌ Running regen when you didn’t intend to update behavior  
- ❌ Committing only authoritative files without derived files  
- ❌ Editing meta.json manually  

---

## 🏁 Summary

If you remember only one rule:

> **If you change manifest.json or any authoritative file, you MUST regenerate golden files.**

Everything else flows from that.
