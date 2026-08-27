# Tooling and Packaging

Recommended stack for modern Python (3.11+): `pyproject.toml` as the single source of truth, `uv` for envs and deps, `ruff` for lint and format, `mypy` or `pyright` for types, `pytest` for tests.

## Contents

- [Project layout](#project-layout)
- [`pyproject.toml`](#pyprojecttoml)
- [`uv` — envs, deps, lockfile, running](#uv--envs-deps-lockfile-running)
- [`ruff` — lint and format](#ruff--lint-and-format)
- [Type checking: mypy or pyright](#type-checking-mypy-or-pyright)
- [Pre-commit](#pre-commit)
- [CI outline](#ci-outline)
- [Entry points and CLIs](#entry-points-and-clis)
- [Distributing a package](#distributing-a-package)

## Project layout

Use the **src layout**. It prevents accidental imports from the working directory and forces you to test against the installed package.

```
myproj/
├── pyproject.toml
├── README.md
├── .python-version              # pin CPython version
├── uv.lock                      # locked deps
├── src/
│   └── myproj/
│       ├── __init__.py
│       ├── __main__.py          # optional: python -m myproj
│       └── ...
└── tests/
    ├── conftest.py
    └── test_*.py
```

- No top-level `myproj/` next to `tests/` — that's the flat layout, and it lets `pytest` pick up the un-installed source tree.
- Use `__main__.py` if the package should be runnable as `python -m myproj`.
- `.python-version` pins CPython for `uv`, `pyenv`, and IDEs (`3.11.9`, `3.12.6`, etc.).

## `pyproject.toml`

One file for build system, project metadata, dependencies, and every tool's config. Minimal example:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myproj"
version = "0.1.0"
description = "One-line description."
readme = "README.md"
requires-python = ">=3.11"
license = "Apache-2.0"           # PEP 639 SPDX string; the { text = ... } table form is deprecated
license-files = ["LICENSE"]
authors = [{ name = "You", email = "you@example.com" }]
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.7",
]

[dependency-groups]              # PEP 735 — dev-only, never published in wheel metadata
dev = [
    "mypy>=1.11",
    "pre-commit>=3.7",
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.6",
]

[project.scripts]
myproj = "myproj.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/myproj"]
```

Notes:

- Pick a build backend: **hatchling** (recommended default), **flit-core** (simpler, single-package), **setuptools** (if you need C extensions). Poetry's backend is fine too but ties you to Poetry.
- `requires-python = ">=3.11"` matches the language features we use.
- **`[dependency-groups]` (PEP 735) for dev-only deps**, not `[project.optional-dependencies]`. `uv sync` installs the `dev` group by default; `uv sync --no-dev` skips it, and `uv sync --group docs` picks up another. Optional-dependencies are *extras* — they ship in the published metadata and become part of your package's public interface, which linting and test tooling has no business being.
- Reserve `[project.optional-dependencies]` for real extras a consumer would install (`myproj[postgres]`, `myproj[cli]`).

## `uv` — envs, deps, lockfile, running

`uv` is a fast, all-in-one project + package + Python-version manager. Replaces `pip`, `venv`, `pip-tools`, `pyenv`, and most of `poetry` in one binary.

### Everyday commands

```bash
uv venv                          # create .venv/ using .python-version
uv sync                          # install deps + the `dev` group, from uv.lock
uv sync --no-dev                 # runtime deps only (what CI ships)
uv sync --group docs             # another PEP 735 group
uv add httpx                     # add a dep, update lockfile
uv add --dev pytest              # add to the `dev` group
uv remove httpx                  # drop a dep
uv lock --upgrade                # refresh the lockfile
uv run pytest -q                 # run inside the venv without activating
uv run python -m myproj          # run the package
uv python install 3.12           # install a Python interpreter
uv python pin 3.12               # write to .python-version
```

- `uv.lock` should be committed. It pins the full dep graph and hashes.
- `uv run <cmd>` is preferable to activating the venv — commands run in an ephemeral shell with the right `PATH`.

### `uv` vs `poetry`

Prefer `uv` for new projects: same feature set, ~10× faster, does Python-version management too. `poetry` is fine to keep on existing projects — no forced migration.

### `pip` + `venv` (stdlib-only fallback)

If `uv` isn't allowed:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e . --group dev     # --group needs pip 25.1+; below that, use an extra
```

Generate a lockfile with `pip-tools` (`uv pip compile pyproject.toml -o requirements.txt` also works).

## `ruff` — lint and format

`ruff` covers the ground of `flake8`, `isort`, `pyupgrade`, `pep8-naming`, `pydocstyle`, `bandit` (partial), and formatting (drop-in `black` compatible). One tool, one config.

```toml
[tool.ruff]
line-length = 80
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E", "W",      # pycodestyle
    "F",           # pyflakes
    "I",           # isort
    "N",           # pep8-naming
    "UP",          # pyupgrade
    "B",           # flake8-bugbear
    "C4",          # flake8-comprehensions
    "SIM",         # flake8-simplify
    "PL",          # pylint (subset)
    "RUF",         # ruff-specific
    "D",           # pydocstyle
    "ANN",         # flake8-annotations
    "PT",          # pytest style
    "TID",         # tidy imports
    "TC",          # typing imports (TYPE_CHECKING) — "TCH" is the deprecated alias
]
ignore = [
    "D203", "D213",     # conflicting docstring rules
    "PLR2004",          # magic values — often noisy
    "ANN401",           # explicit Any in *args/**kwargs
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["D", "ANN"]
"**/__init__.py" = ["F401"]      # re-exports
"**/_*.py" = ["ANN"]             # private modules: annotate by judgment, not by rule

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
docstring-code-format = true
```

Two notes on that `select` list:

- **`ANN101` / `ANN102` no longer exist.** Ruff removed them (annotating `self`/`cls` is never wanted, so the rules were deleted rather than merely disabled). Leaving them in `ignore` gets you `warning: The following rules have been removed and ignoring them has no effect` on every run — drop them.
- **`ANN` demands annotations on *every* function**, which is stricter than this skill's rule that public APIs are typed and internal helpers can be inferred. Either accept the stricter line (defensible — it's mechanical and `ruff format` keeps it cheap), or scope it with `per-file-ignores` as above. Don't select `ANN` and then scatter `# noqa` through the codebase.

Commands:

```bash
uv run ruff check --fix .
uv run ruff format .
uv run ruff check --statistics .   # rule frequency
```

**Don't stack `black` + `isort` + `flake8` + `pylint` alongside `ruff`.** Pick one.

## Type checking: mypy or pyright

Both are good. Pick one per project.

| Trade-off       | `mypy`                     | `pyright`                 |
| --------------- | -------------------------- | ------------------------- |
| Author          | Community (`python/mypy`)  | Microsoft                 |
| Speed           | Slower                     | Fast                      |
| IDE integration | Via LSP                    | Native in Pylance/VS Code |
| Configurability | Very high, mature          | Fewer knobs, opinionated  |
| Strict mode     | `strict = true` + per-flag | `strict = true`           |

### `mypy` config

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unreachable = true
warn_no_return = true
disallow_any_generics = true
disallow_untyped_decorators = true
show_error_codes = true
plugins = ["pydantic.mypy"]        # if using pydantic

[[tool.mypy.overrides]]
module = ["untyped_lib.*"]
ignore_missing_imports = true
```

Run: `uv run mypy src tests`.

### `pyright` config

```toml
[tool.pyright]
pythonVersion = "3.11"
include = ["src", "tests"]
strict = ["src"]
reportMissingTypeStubs = "warning"
```

Run: `uv run pyright`. Or install `basedpyright` (a stricter community fork) — it's a drop-in for `pyright` with more rules.

**Turn on strict mode from day one on new code.** Retrofitting is painful. Ratchet gradually on existing code by scoping `strict` to specific directories.

## Pre-commit

```yaml
# .pre-commit-config.yaml
# `rev:` values below are examples — run `pre-commit autoupdate` to pin current ones.
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: check-yaml
      - id: check-toml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

Install once: `uv run pre-commit install`.

Don't run `mypy` / `pyright` / `pytest` in pre-commit — they're too slow to be worth it in every commit. Run them in CI.

## CI outline

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v5
      - uses: astral-sh/setup-uv@v6
        with: { enable-cache: true }
      - run: uv python install ${{ matrix.python }}
      - run: uv sync            # installs the `dev` dependency group by default
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy src tests
      - run: uv run pytest -q --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v5
        with: { files: ./coverage.xml }
```

Action versions move; check the marketplace rather than copying these verbatim. `--cov` needs `pytest-cov` in the `dev` group — it's in the `pyproject.toml` above.

## Entry points and CLIs

Define CLIs in `[project.scripts]`:

```toml
[project.scripts]
myproj = "myproj.cli:main"
myproj-worker = "myproj.worker:main"
```

Then `pip install -e .` (or `uv sync`) puts them on `PATH`. Use `argparse` for zero-dep CLIs, `click` or `typer` for anything with subcommands or auto-generated help.

## Distributing a package

```bash
uv build                         # produces sdist + wheel in dist/
uv publish                       # to PyPI (UV_PUBLISH_TOKEN, or trusted publishing in CI)
```

- Version once, in `[project].version`. For single-source-of-truth versioning driven by git tags, use `hatch-vcs`. (`hatch-fancy-pypi-readme` is unrelated — it assembles the long description, not the version.)
- **Trusted Publishing** on PyPI is the current best practice — no long-lived API tokens. Locally, `uv publish` reads `UV_PUBLISH_TOKEN` (or `UV_PUBLISH_USERNAME` / `UV_PUBLISH_PASSWORD`) — not `PYPI_TOKEN`, which is a `twine` convention.
- Announce breaking changes clearly. Follow SemVer: MAJOR for breaks, MINOR for features, PATCH for fixes.

## Anti-patterns

- `setup.py` in new projects. Use `pyproject.toml`.
- `requirements.txt` as the source of truth for direct deps. It's a lock artifact, not a spec.
- Committing `.venv/`.
- Global `pip install` outside a venv.
- Mixing tool configs across `pyproject.toml`, `setup.cfg`, `.flake8`, `.isort.cfg`. Consolidate under `[tool.*]` in `pyproject.toml`.
- Long-running lock files without `uv lock --upgrade` cadence. Refresh at least monthly.
