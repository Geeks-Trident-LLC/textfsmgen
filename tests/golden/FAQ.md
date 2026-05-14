# ❓ **Developer FAQ: When do I use pytest vs CLI?**

## **Q: When should I use the CLI tester?**  
Use the CLI for **all day‑to‑day work**, including:

- running a case  
- quicktesting  
- regenerating a case  
- diffing  
- creating new cases  
- merging cases  
- batch operations  

The CLI is fast, targeted, and designed for developers.

---

## **Q: When should I use pytest?**  
Use pytest when you want to:

- validate the entire golden suite  
- run drift detection across all cases  
- regenerate *all* golden files at once  
- run CI or pre‑commit checks  

Examples:

```
pytest tests/golden
pytest tests/golden --regen-golden
```

---

## **Q: Why not use pytest for everything?**  
Because pytest:

- is slower  
- runs the entire suite  
- is not ergonomic for per‑case development  
- is meant for CI, not daily iteration  

The CLI is your **developer toolbelt**.  
Pytest is the **final judge**.

---

## **Q: If I change a template/snippet/manifest, what do I run?**  
Use the CLI:

```
textfsmgen tester regen <case>
```

Pytest is only needed if you want to regenerate *all* cases:

```
pytest tests/golden --regen-golden
```

---

## **Q: What if pytest reports drift?**  
Run:

```
pytest tests/golden --regen-golden
```

or regenerate the specific case:

```
textfsmgen tester regen <case>
```

---

## **Q: Which tool writes derived files?**  
Both:

- CLI → per‑case regeneration  
- pytest → full‑suite regeneration  
