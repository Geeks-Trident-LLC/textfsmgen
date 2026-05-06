# Architecture

`textfsmgen` generates and verifies TextFSM templates from sample network device output.

---

## Package Layout

```
textfsmgen/
├── core/        # Domain models and verification logic
├── engine/      # Template generation and translation
├── libs/        # Shared utilities
├── tools/       # Developer-facing tools (samples, suggestions, explanations)
├── ui/          # Tkinter UI layer
├── application.py
├── config.py
├── exceptions.py
└── main.py

scripts/         # Standalone CI/dev scripts (not an importable package)
tests/           # Mirrors source layout (see Tests section)
```

---

## Module Dependency Tiers

Files are named to communicate their allowed dependencies at a glance:

| Filename      | Allowed imports                                                    |
|---------------|--------------------------------------------------------------------|
| `generic.py`  | **stdlib only** — no third-party, no internal `textfsmgen` imports |
| `utils.py`    | stdlib + third-party + internal                                    |
| anything else | stdlib + third-party + internal                                    |

This rule is enforced by CI via `scripts/check_generic_imports.py`.
Any `generic.py` that imports outside stdlib will fail the check.

A `generic.py` file carries this one-liner at the top to make the rule visible locally:

```python
# stdlib-only module — no third-party or internal imports permitted.
```

---

## Package Responsibilities

### `core/`
Domain models and correctness logic. No UI, no generation.

| Module        | Responsibility                                           |
|---------------|----------------------------------------------------------|
| `patterns.py` | Line pattern definitions and matching                    |
| `registry.py` | Pattern registry and lookup                              |
| `template.py` | TextFSM template model                                   |
| `testing.py`  | Test case runner for templates                           |
| `verify.py`   | Verification of template output against expected results |

### `engine/`
Template generation pipeline. Takes structured input and produces TextFSM output.

| Module         | Responsibility                                 |
|----------------|------------------------------------------------|
| `line.py`      | Line-level pattern analysis                    |
| `tabular.py`   | Tabular data detection and handling            |
| `category.py`  | Category classification of input lines         |
| `translate.py` | Translates classified lines into TextFSM rules |
| `doc.py`       | Documentation generation for templates         |
| `common.py`    | Shared engine base types                       |

### `libs/`
Shared utilities used across `core/`, `engine/`, and `tools/`.

| Module          | Responsibility                                     |
|-----------------|----------------------------------------------------|
| `generic.py`    | stdlib-only helpers (safe to copy across projects) |
| `utils.py`      | General helpers using internal or third-party libs |
| `pattern.py`    | Pattern parsing and keyword mapping                |
| `token.py`      | Tokenisation primitives                            |
| `datatype.py`   | Custom data types                                  |
| `text.py`       | String manipulation                                |
| `number.py`     | Numeric parsing helpers                            |
| `file.py`       | File I/O helpers                                   |
| `shell.py`      | Shell interaction helpers                          |
| `decorators.py` | Reusable decorators                                |
| `common.py`     | Shared base types for libs                         |

### `tools/`
Developer-facing utilities. Depend on `core/` and `libs/`, not on `ui/`.

| Module            | Responsibility                       |
|-------------------|--------------------------------------|
| `samples.py`      | Random sample generation for testing |
| `samples_data.py` | Static sample data sets              |
| `suggester.py`    | Regex pattern suggestion logic       |
| `explain.py`      | Human-readable pattern explanations  |
| `token.py`        | Token-level analysis tools           |

### `ui/`
Tkinter GUI layer. Depends on `tools/`, `core/`, and `engine/`. Nothing else depends on `ui/`.

| Module              | Responsibility                   |
|---------------------|----------------------------------|
| `builder.py`        | Regex builder UI                 |
| `textfsm_tester.py` | TextFSM tester UI                |
| `suggester.py`      | Regex suggester UI               |
| `settings.py`       | Settings panel                   |
| `controls.py`       | Reusable UI controls             |
| `menu.py`           | Application menu                 |
| `callback.py`       | UI event callbacks               |
| `about.py`          | About dialog                     |
| `usage.py`          | Usage/help panel                 |
| `common.py`         | Shared UI base types and helpers |

---

## Data Flow

```
Raw device output (text)
        │
        ▼
   engine/line.py          ← classify each line
        │
        ▼
   engine/category.py      ← group lines into categories
        │
        ▼
   engine/translate.py     ← convert categories into TextFSM rules
        │
        ▼
   core/template.py        ← assemble into a TextFSM template
        │
        ├──▶ core/verify.py      ← verify template against raw input
        │
        └──▶ core/testing.py     ← run test cases against template
```

Tools operate alongside this pipeline:

```
tools/samples.py     ← generate test input for any pattern
tools/suggester.py   ← suggest patterns for a given input line
tools/explain.py     ← explain what a pattern matches
```

The UI layer calls into `tools/` and `core/` directly — it does not touch `engine/` internals.

---

## Dependency Direction

Dependencies only flow downward. No upward or circular imports are permitted.

```
ui/
 └── tools/  ──┐
 └── core/   ──┤
               ▼
            engine/
               │
               ▼
             libs/
```

---

## Tests

Tests live in `tests/` and mirror the source layout:

```
tests/
├── core/
├── engine/
├── libs/
├── tools/
└── ui/
```

Each test file maps directly to its source counterpart:
`tests/libs/test_generic.py` → `textfsmgen/libs/generic.py`

Run the full suite:

```bash
pytest
# or
tox
```

---

## Scripts

`scripts/` contains standalone CI utilities. It is not an importable package — no `__init__.py`.

| Script                     | Purpose                                               |
|----------------------------|-------------------------------------------------------|
| `check_generic_imports.py` | Fails if any `generic.py` contains non-stdlib imports |

Run manually:

```bash
python scripts/check_generic_imports.py
```