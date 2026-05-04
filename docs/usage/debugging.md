# Debugging Templates

Common issues and how to fix them.

---

## 1. No Matches Found

- Check regex patterns  
- Ensure anchors (`^`) match actual input  
- Use `--debug` flag (coming soon)

---

## 2. Incorrect Value Extraction

- Use non-greedy patterns  
- Avoid overly broad `(\S+)`  
- Validate with sample input

---

## 3. State Machine Issues

- Ensure transitions are reachable  
- Add explicit fallback states  
- Use `explain` to visualize state flow
