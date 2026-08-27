---
name: python-engineering
description: >-
  Best practices for writing idiomatic, well-typed, and maintainable modern
  Python (3.11+). Covers the Google Python Style Guide (naming, imports,
  docstrings, type annotations, formatting) and modern patterns for typing,
  data modeling (dataclasses, pydantic v2, TypedDict), asyncio, exceptions,
  logging, pytest, and tooling with ruff and uv. Use when writing or
  reviewing Python code, designing modules, choosing between dataclass and
  pydantic, adding type hints, structuring async code, writing tests, or
  configuring a Python project.
disable-model-invocation: false
compatibility: >-
  Targets Python 3.11+. Assumes ruff, uv and pytest; recommendations adjust if
  the project uses a different toolchain.
---

# Python Engineering

## Overview

Apply the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) for readability, naming, docstrings, and type annotations; layer on modern Python 3.11+ idioms (structural typing, `TaskGroup`, `Self`, `ExceptionGroup`, `match`, PEP 604 `X | None`, `dataclass(slots=True)`, pydantic v2) and a lean toolchain (`uv`, `ruff`, `pytest`). Prefer standard library primitives; reach for third-party only when they solve a real problem at the boundary (validation, HTTP, ORM).

## Ground rules

- **Target 3.11+.** Use `list[int]`, `dict[str, int]`, `X | None`, `match`, `Self`, `TaskGroup`, `asyncio.timeout`, `ExceptionGroup`, `tomllib`, `StrEnum`.
- **Mind the feature floor above 3.11.** `override` is 3.12+, PEP 695 generics (`def f[T]`, `type X = ...`) are 3.12+, `TypeIs` is 3.13+. Below those versions import from `typing_extensions` — never from `typing`.
- **Type public APIs.** Annotate module-level functions, class methods, and public dataclasses/protocols. Internal helpers can be inferred.
- **Prefer `collections.abc` in signatures.** Accept `Sequence`/`Mapping`/`Iterable`; return concrete `list`/`dict`/`tuple` when identity matters.
- **`ruff` for lint + format, `uv` for env + deps, `pytest` for tests.** No `black` + `isort` + `flake8` + `pylint` stack in new projects.
- **Docstrings: Google style.** `Args:`, `Returns:`/`Yields:`, `Raises:` with hanging indent.
- **Don't reach for power features** (metaclasses, `__init_subclass__`, dynamic imports, monkey-patching) until a simpler design has been tried and rejected.

## Workflow

1. **Identify the task** — new module, refactor, review, test suite, packaging, or async pipeline.
2. **Read the relevant reference** — use the routing tables below.
3. **Check the code with tools** — `ruff check --fix .`, `ruff format .`, `mypy .` (or `pyright`), `pytest -q`. Fix or explicitly silence each finding with a comment explaining why.

## When to Read Which Reference

### Google Python Style Guide (pyguide)

- **Language rules — imports, exceptions, mutable defaults, comprehensions, decorators, threading, power features** → Read [references/pyguide/language-rules.md](references/pyguide/language-rules.md)
- **Style rules — line length, indentation, whitespace, strings, statements, `main`, function length** → Read [references/pyguide/style-rules.md](references/pyguide/style-rules.md)
- **Docstrings — module, function, class, generator, overridden method** → Read [references/pyguide/docstrings.md](references/pyguide/docstrings.md)
- **Naming — modules, classes, functions, constants, protected/private, `TypeVar` conventions** → Read [references/pyguide/naming.md](references/pyguide/naming.md)
- **Type annotations — general rules, line breaking, forward refs, `NoneType`, aliases, generics, string types, typing imports** → Read [references/pyguide/type-annotations.md](references/pyguide/type-annotations.md)

### Modern Python (3.11+)

- **Advanced typing — `Protocol`, `TypeVar`, `ParamSpec`, `Self`, `@overload`, `TypeGuard`/`TypeIs`, `override`, PEP 695 generics** → Read [references/modern/typing.md](references/modern/typing.md)
- **Data modeling — when to use `@dataclass`, `pydantic` v2, `TypedDict`, `NamedTuple`, `Protocol`** → Read [references/modern/data-modeling.md](references/modern/data-modeling.md)
- **Async — `asyncio.run`, `TaskGroup`, cancellation, timeouts, sync/async boundaries** → Read [references/modern/async.md](references/modern/async.md)
- **Errors — custom exception design, chaining, `ExceptionGroup`, `try`/`except`/`else`/`finally` layout** → Read [references/modern/errors.md](references/modern/errors.md)
- **Logging — stdlib `logging`, structured logs, `%`-style args, per-module loggers, config** → Read [references/modern/logging.md](references/modern/logging.md)
- **Testing — pytest fixtures, parametrize, mocking, coverage, async tests** → Read [references/modern/testing.md](references/modern/testing.md)
- **Tooling & packaging — `pyproject.toml`, `uv`, `ruff`, `mypy`/`pyright`, src layout, entry points** → Read [references/modern/tooling.md](references/modern/tooling.md)

## Quick Cues

- **Types on public APIs:** Use `list[int]`, `dict[str, int]`, `X | None`. Prefer `Sequence`/`Mapping`/`Iterable` from `collections.abc` in parameter positions.
- **No mutable defaults:** `def f(x: list[int] | None = None): x = x or []`. Empty tuples (`()`) are fine as immutable defaults.
- **`is None`, not `== None`:** Use `if x is None:` / `if x is not None:`. Use implicit falsy (`if not seq:`) for containers but never for integers where `0` and `None` differ meaningfully.
- **Never catch `Exception` bare.** Catch the narrowest exception you can act on; re-raise otherwise. Use `except SomeError as e: raise MyError(...) from e`. (`except Exception:` does *not* catch `asyncio.CancelledError` — that's a `BaseException` — but it does hide every programming error.)
- **`with` for all closeable resources.** Files, sockets, DB connections, `asyncio.TaskGroup`, `contextlib.closing(...)`.
- **Google docstrings:** One-line summary ending in `.`, blank line, then details. `Args:` / `Returns:` / `Raises:` with hanging indent.
- **Dataclasses:** `@dataclass(frozen=True, slots=True)` for value objects. Reach for `pydantic.BaseModel` only at IO/config/API boundaries where validation and JSON schema matter.
  - Two footguns before you copy that default: `frozen=True` generates a `__hash__` that raises on a `list`/`dict`/`set` field, and `slots=True` breaks `functools.cached_property`. See [data-modeling.md](references/modern/data-modeling.md#dataclass).
- **Async:** Use `asyncio.TaskGroup` (3.11+) instead of hand-rolled `gather` + cancellation. Wrap every `await` that talks to the outside world in `asyncio.timeout(...)`.
- **Loggers:** `logger = logging.getLogger(__name__)`. Call as `logger.info("processed %s", key)` — never f-strings in log calls (the formatter can lazy-skip and log aggregators can group by pattern).
- **Tooling:** `pyproject.toml` is the single source of truth. `uv sync` for envs. `ruff check --fix && ruff format` before commit. Pin Python via `requires-python = ">=3.11"` and `.python-version`.

## Anti-patterns

- **`from module import *`** in application code. Explicit imports only.
- **`assert` for runtime validation.** `-O` strips them. Use `if not cond: raise ValueError(...)` — `assert` is fine only in tests.
- **String concatenation in loops.** Append to a `list` then `"".join(...)`, or write to `io.StringIO`.
- **Type comments (`# type: X`).** Use annotated assignments (`x: X = ...`).
- **`typing.List` / `typing.Dict` / `typing.Optional` / `typing.Union` in new code (3.11+).** Use `list`, `dict`, `X | None`, `A | B`.
- **`Any` as an escape valve.** Prefer `object`, a `Protocol`, or a `TypeVar` bound. Add `# type: ignore[reason]` only with a specific rule and a comment.
- **Broad `except Exception:` swallowing errors silently.** At the outermost boundary of a thread/task, log with `logger.exception(...)` and re-raise or fail fast.
- **Global mutable state.** Prefer explicit dependency injection or a per-request context object.

## References

- **Google Python Style Guide:** https://google.github.io/styleguide/pyguide.html
- **Python docs (3.11+):** https://docs.python.org/3/
- **PEPs:** [PEP 8](https://peps.python.org/pep-0008/) (style), [PEP 257](https://peps.python.org/pep-0257/) (docstrings), [PEP 484](https://peps.python.org/pep-0484/)/[526](https://peps.python.org/pep-0526/)/[544](https://peps.python.org/pep-0544/)/[604](https://peps.python.org/pep-0604/)/[673](https://peps.python.org/pep-0673/) (typing), [PEP 654](https://peps.python.org/pep-0654/) (`ExceptionGroup`), [PEP 695](https://peps.python.org/pep-0695/) (generics)
- **Tooling:** [ruff](https://docs.astral.sh/ruff/), [uv](https://docs.astral.sh/uv/), [pytest](https://docs.pytest.org/), [mypy](https://mypy.readthedocs.io/), [pyright](https://microsoft.github.io/pyright/)
- **Pydantic v2:** https://docs.pydantic.dev/latest/
