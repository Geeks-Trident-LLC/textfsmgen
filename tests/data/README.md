# Test data layout

This directory contains curated sample inputs used to exercise the parsing engines.

## Structure

- `free-form/`
  - Free‑form, non‑tabular CLI outputs (e.g., `show version`, multi‑section tech outputs).
- `semi-structured/category-format/`
  - Category‑style key/value outputs:
    - simple key/value
    - grouped sections
    - repeated keys
    - wrapped values
- `semi-structured/tabular-format/`
  - Tabular outputs covering:
    - headered vs headerless
    - fixed vs flex width
    - header separators (column‑aligned and full‑width)
    - leading/trailing non‑tabular lines
    - empty columns
    - wrapped columns

Each file name is intention‑revealing and encodes the structural pattern it represents.
These files are used by unit tests, integration tests, and golden‑file tests.
