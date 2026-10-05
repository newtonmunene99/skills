# Contributing

## Setup

```bash
uv sync
uv run pytest
```

## Code style

- Format with `ruff format`, lint with `ruff check`.
- Docstrings follow the NumPy convention (numpydoc), because our API reference
  is built with Sphinx and numpydoc. Do not repeat parameter types in the
  docstring; the annotations already carry them and the two copies drift.
- Keep commits small and focused.
