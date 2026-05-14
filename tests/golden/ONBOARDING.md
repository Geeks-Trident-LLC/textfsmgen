
# 🧭 **Developer Onboarding Guide**

Welcome to the TextFSM Golden Test development workflow.  
This page gives new contributors everything they need to become productive in **under 10 minutes**.

---

## 🎯 What You’ll Be Working With

This project uses **Golden Master Testing** to ensure TextFSM templates, snippets, and builders remain stable over time.

You’ll interact with two tools:

- **Tester CLI** — your daily toolbelt  
- **Pytest** — full‑suite validation + CI drift detection  

If you understand the difference, you’re already halfway onboarded.

---

## 🧰 Your Daily Tools (CLI)

Use the CLI for all case‑level work:

```
textfsmgen tester run <case>
textfsmgen tester quicktest <case>
textfsmgen tester regen <case>
textfsmgen tester diff <case>
textfsmgen tester new <case>
textfsmgen tester new-from-input ...
```

This is how you:

- run a case  
- validate changes  
- regenerate derived files  
- create new cases  
- merge or dedupe cases  

The CLI is fast and designed for iteration.

---

## 🧪 Full Suite Validation (Pytest)

Use pytest when you want to validate the entire golden suite:

```
pytest tests/golden
```

Or regenerate all cases at once:

```
pytest tests/golden --regen-golden
```

Pytest is the final judge used by CI.

---

## 🧩 Authoritative vs Derived Files

### **Authoritative (you edit these)**  
Define intended behavior:

```
manifest.json
canonical/snippet.txt
canonical/textfsm.template
expected/snippet.txt
expected/textfsm.template
inputs/*.txt
```

### **Derived (never edit manually)**  
Generated from authoritative truth:

```
canonical/result.json
expected_results/*.json
meta.json
golden.hash
```

If authoritative files change → regenerate.

---

## 🔄 Regeneration Rule (the one rule to remember)

If you change **any** authoritative file:

```
textfsmgen tester regen <case>
```

Or for all cases:

```
pytest tests/golden --regen-golden
```

---

## 🛡️ Drift Detection

Pytest ensures golden files match `golden.hash`.  
If not, you’ll see:

```
Golden files drift detected.
```

Fix by regenerating.

---

## 🚀 Typical Contributor Workflow

1. Edit template/snippet/manifest  
2. Run quicktest  
3. Inspect diff  
4. If intentional → regenerate  
5. Commit authoritative + derived files  
6. Push PR  

This is the loop you’ll use every day.

---

## 📚 Where to Go Next

- **CLI-TESTER-GUIDE.md** — full command reference  
- **QUICKSTART.md** — fast hands‑on examples  
- **README.md** — golden master testing concepts  

You’re ready to contribute.

---

# 🔀 **Merge Workflow Flowchart**

A compact visual guide to how merge operations work.

```
                   ┌──────────────────────────┐
                   │   Start Merge Workflow   │
                   └─────────────┬────────────┘
                                 │
                                 ▼
                     ┌─────────────────────┐
                     │ Select source cases │
                     │   (src1, src2...)   │
                     └─────────────┬───────┘
                                   │
                                   ▼
                     ┌────────────────────┐
                     │ Choose destination │
                     │       (dst)        │
                     └─────────────┬──────┘
                                   │
                                   ▼
                     ┌────────────────────────────┐
                     │ Evaluate reference options │
                     │  merge-preview <srcs...>   │
                     └─────────────┬──────────────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │  Reference selected?       │
                     └─────────────┬──────────────┘
                                   │Yes
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │ Simulate merge plan       │
                     │  - copy inputs            │
                     │  - rename conflicts       │
                     │  - compute actions        │
                     └─────────────┬─────────────┘
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │ Review merge plan         │
                     │ merge-review dst srcs...  │
                     └─────────────┬─────────────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │  Accept merge plan?        │
                     └─────────────┬──────────────┘
                                   │Yes
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │ Perform merge             │
                     │ textfsmgen tester merge   │
                     │   --author A dst srcs...  │
                     └─────────────┬─────────────┘
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │ Quicktest merged case     │
                     │ tester quicktest dst      │
                     └─────────────┬─────────────┘
                                   │
                                   ▼
                     ┌────────────────────────────┐
                     │ Commit merged case         │
                     └────────────────────────────┘
```
