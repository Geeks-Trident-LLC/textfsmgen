Here you go, Tuyen — **three polished, compact developer‑friendly documents**:

- **CLI Cheat‑Sheet (one page)**  
- **Man‑page style version**  
- **Developer FAQ: When do I use pytest vs CLI?**  

All written in the same clean, professional tone as the rest of your docs.

---

# 📄 **CLI Tester Cheat‑Sheet (One Page)**

```
textfsmgen tester <command> [options] <args>
```

## Core Commands
- **run <case>**  
  Full execution: build → parse → compare.

- **quicktest <case>**  
  Fast validation (no regeneration).

- **regen <case>**  
  Regenerate derived files for a single case.

- **diff <case>**  
  Show differences between expected and generated results.

- **drift <case>**  
  Detect whether the case is out of sync with its golden state.

---

## Case Creation
- **new <case>**  
  Create a new case scaffold.

- **new-from-input --builder B --author A <case> <inputs>**  
  Create a case from input samples.

---

## Copying & Duplicating
- **copy <author> <src> <dst>**  
  Copy a case.

- **duplicate <author> <src>**  
  Duplicate a case with auto‑naming.

---

## Batch Operations
- **batch-generate <root>**  
  Run `generate` on all cases.

- **batch-regen <root>**  
  Regenerate all cases.

- **batch-quicktest <root>**  
  Quicktest all cases.

---

## Merging
- **merge --author A <dst> <srcs...>**  
  Merge multiple cases.

- **merge-review <dst> <srcs...>**  
  Preview merge using `<dst>` as reference.

- **merge-preview <srcs...>**  
  Preview merge with auto‑selected reference.

- **merge-diff <srcs...>**  
  Diff merged expected_results vs golden.

---

## Deduplication
- **identical <srcs...>**  
  Identify cases that produce identical results.

---

## Typical Workflow
1. Edit authoritative files  
2. `quicktest`  
3. `diff`  
4. If intentional → `regen`  
5. Commit authoritative + derived files  
