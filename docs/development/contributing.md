# Contributing Guide

Thank you for your interest in contributing!

This project values clean code, clear documentation, and predictable behavior.
Please follow the guidelines below.

---

## 1. Development Setup

Clone the repository:

```
git clone https://github.com/Geeks-Trident-LLC/textfsmgen.git
cd textfsmgen
```

Install dependencies:

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 2. Code Style

- Follow PEP8.
- Use intention‑revealing names.
- Prefer early returns.
- Group related logic.
- Avoid noisy exception handling.
- Keep UI text clean and professional.
- Keep documentation concise and Markdown‑friendly.

---

## 3. Testing

Run all tests:

```
pytest
```

All PRs must pass tests before merging.

---

## 4. Versioning

Do **not** manually edit version numbers.

Use bump2version:

```
bump2version patch
bump2version minor
bump2version major
```

Version is stored in:

```
textfsmgen/__init__.py
```

---

## 5. Submitting Pull Requests

- Keep PRs focused and small.
- Include tests for new features.
- Update documentation when needed.
- Use clear commit messages.
- Ensure PR title is descriptive.
- Link related issues.

---

## 6. Branching Model

- `main`: stable, production-ready
- `develop`: active development
- feature branches: `feature/<name>`
- bugfix branches: `fix/<name>`

---

## 7. Reporting Issues

Use the GitHub Issue Template.  
Provide:

- steps to reproduce  
- expected behavior  
- actual behavior  
- environment details  

---

## 8. Code of Conduct

Be respectful, constructive, and collaborative.  
We welcome contributions from everyone.

---

Thank you for contributing!
```
