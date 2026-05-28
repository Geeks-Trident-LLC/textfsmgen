# Contributing to textfsmgen

Thank you for your interest in contributing to **textfsmgen**!  
This guide explains how to set up your environment, run tests, update documentation, and submit high‑quality pull requests that integrate smoothly with the project’s workflows.

---

## 🛠 Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/Geeks-Trident-LLC/textfsmgen.git
cd textfsmgen
```

### 2. Install dependencies
```bash
pip install -e .
pip install -r requirements-dev.txt
```

### 3. Run the test suite
```bash
pytest
```

### 4. Validate documentation
```bash
mkdocs build --strict
```

### 5. Preview documentation locally
```bash
mkdocs serve
```

---

## 🧪 Golden Tests

Golden tests are a core part of the project’s validation workflow.

Run golden tests:
```bash
pytest --enable-golden
```

Show diffs:
```bash
pytest --enable-golden --diff-golden
```

Debug mismatches:
```bash
pytest --enable-golden --debug-golden
```

Golden tests live under:
```
textfsmgen/tests/golden/
```

---

## 🧹 Code Style & Standards

This project follows clean, intention‑revealing coding practices:

- Use clear, descriptive names
- Prefer early returns
- Group related logic
- Avoid noisy exception handling
- Keep UI text clean and professional
- Keep documentation in Markdown or plain `.txt`

Linting is handled by **Ruff**:
```bash
ruff check .
```

---

## 📚 Documentation

Documentation lives in the `docs/` directory and is built with **MkDocs Material**.

To preview:
```bash
mkdocs serve
```

To validate:
```bash
mkdocs build --strict
```

When adding new features, update:

- `docs/usage/`
- `docs/guides/`
- `docs/reference/`
- `docs/development/`

---

## 🔀 Submitting a Pull Request

1. Create a feature branch:
```bash
git checkout -b feature/my-change
```

2. Make your changes.

3. Run:
```bash
pytest
mkdocs build --strict
ruff check .
```

4. Commit using clear, intention‑revealing messages.

5. Push your branch and open a Pull Request.

6. Fill out the PR template completely.

Your PR must pass:
- CI tests (`ci.yml`)
- Docs validation
- Ruff linting
- Golden tests (if applicable)

---

## 🚀 Release Process (Maintainers)

Releases follow semantic versioning:

- `MAJOR` — breaking changes  
- `MINOR` — new features  
- `PATCH` — bug fixes  

To release:

```bash
bump2version <major|minor|patch>
git push
git push --tags
```

GitHub Actions will automatically:

- Build the package  
- Publish to PyPI  
- Deploy documentation  

---

## 🤝 Code of Conduct

All contributors must follow the project’s `CODE_OF_CONDUCT.md`.

---

## 🙏 Thank You

Your contributions help make **textfsmgen** better for everyone.
