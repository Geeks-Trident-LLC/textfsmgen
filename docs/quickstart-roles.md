# Quickstart by Role

This guide helps different types of users get started with `textfsmgen` quickly,
based on their goals and experience level.

---

## 🧪 Test Engineer

**Goal:** Generate and maintain golden tests.

You will primarily use:

- `textfsmgen-golden-testers new`
- `textfsmgen-golden-testers run`
- `textfsmgen-golden-testers identical`
- `textfsmgen-golden-testers merge-*`
- `textfsmgen-golden-testers promote-*`

Start with:

```bash
textfsmgen-golden-testers generate ...
textfsmgen-golden-testers run ...
```

---

## 🛠 Developer

**Goal:** Integrate builders, automate workflows, or extend CLI behavior.

You will use:

- Python API (`BuilderRunner`, workflow metadata)
- CLI commands for debugging
- JSON workflow output

Start with:

```bash
textfsmgen --json run tests/cases/example
```

---

## 📦 Release Engineer

**Goal:** Prepare releases, validate workflows, and publish packages.

You will use:

- `bump2version`
- Release checklist
- CI/CD workflows
- Docs build validation

---

## 📚 Documentation Contributor

**Goal:** Improve docs, examples, and tutorials.

You will use:

```bash
mkdocs serve
```

and edit files under `docs/`.
