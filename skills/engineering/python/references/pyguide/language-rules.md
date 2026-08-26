# Language Rules (pyguide §2)

Distilled from [Google Python Style Guide §2](https://google.github.io/styleguide/pyguide.html#2-python-language-rules). Targeting Python 3.11+.

## Contents

- [Lint](#lint)
- [Imports](#imports)
- [Packages](#packages)
- [Exceptions](#exceptions)
- [Mutable global state](#mutable-global-state)
- [Nested / inner classes and functions](#nested--inner-classes-and-functions)
- [Comprehensions & generator expressions](#comprehensions--generator-expressions)
- [Default iterators and operators](#default-iterators-and-operators)
- [Generators](#generators)
- [Lambda functions](#lambda-functions)
- [Conditional expressions](#conditional-expressions)
- [Default argument values](#default-argument-values)
- [Properties](#properties)
- [True/False evaluations](#truefalse-evaluations)
- [Lexical scoping](#lexical-scoping)
- [Decorators](#decorators)
- [Threading](#threading)
- [Power features](#power-features)
- [`from __future__` imports](#from-__future__-imports)
- [Type-annotated code](#type-annotated-code)

## Lint

Run a linter over your code. In modern projects use [`ruff`](https://docs.astral.sh/ruff/) — it subsumes flake8, pylint (most rules), isort, pydocstyle, pyupgrade, etc.

Suppress warnings with line-level comments that name the rule and, when the name is not self-explanatory, add a reason:

```python
def do_PUT(self):  # noqa: N802 - WSGI callback name is fixed by the spec
    ...
```

Prefer `# noqa: RULE` over blanket `# noqa`. For unused arguments required by an interface, delete them at the top with a comment:

```python
def viking_cafe_order(spam: str, beans: str, eggs: str | None = None) -> str:
    del beans, eggs  # Unused by vikings.
    return spam + spam + spam
```

Prefixing with `_` or `unused_` is discouraged — it breaks keyword-argument callers and doesn't enforce non-use.

## Imports

Use `import` for **packages and modules only**, not individual types/classes/functions (small, well-known exceptions: symbols from `typing`, `collections.abc`, `typing_extensions`).

- `import x` for packages and modules.
- `from x import y` where `x` is the package prefix and `y` is a module.
- `from x import y as z` when:
  - two `y`s must be imported, or
  - `y` collides with a local top-level name, or
  - `y` collides with a common public-API parameter name, or
  - `y` is inconveniently long, or
  - `y` is too generic without the package context (`from storage.file_system import options as fs_options`).
- `import y as z` only for standard abbreviations (`import numpy as np`).
- **No relative imports.** Use the full package path even for siblings.

```python
from sound.effects import echo
echo.EchoFilter(input, output, delay=0.7, atten=4)
```

## Packages

Import each module by its full package path so `sys.path` accidents can't silently change what gets imported.

```python
# Yes
import absl.flags
from doctor.who import jodie

# Yes (idiomatic short form)
from absl import flags
from doctor.who import jodie

# No — ambiguous, depends on sys.path
import jodie
```

Never assume the main binary's directory is in `sys.path`. `import jodie` should resolve to a third-party or top-level package named `jodie`, not a local `jodie.py`.

## Exceptions

- **Use built-in exceptions where they fit.** `ValueError`, `TypeError`, `KeyError`, `RuntimeError`, `NotImplementedError`, etc. Raise `ValueError` for violated preconditions on arguments.
- **Never use `assert` for runtime validation.** `python -O` strips them. Use `if not cond: raise ValueError(...)`. `assert` is fine in tests.
- **Custom exception names end in `Error`.** Inherit from a stdlib base or your own package base. Do not repeat the package name (`foo.FooError` — no).
- **Never bare `except:` or catch `Exception`** except to (a) re-raise or (b) create an isolation point (e.g. the outer boundary of a thread or task) where you record and suppress. `except:` also catches `KeyboardInterrupt` and `SystemExit`.
- **Minimize the try body.** Larger bodies hide the origin of the exception.
- **Use `else` and `finally`.** `else` for code that runs only if no exception was raised; `finally` for cleanup that must always run.
- **Chain, don't swallow.** `raise MyError("context") from e` preserves the cause.

```python
def connect_to_next_port(self, minimum: int) -> int:
    """Connects to the next available port.

    Args:
        minimum: A port value >= 1024.

    Returns:
        The new minimum port.

    Raises:
        ConnectionError: If no available port is found.
    """
    if minimum < 1024:
        raise ValueError(f"Min. port must be at least 1024, not {minimum}.")
    port = self._find_next_open_port(minimum)
    if port is None:
        raise ConnectionError(
            f"Could not connect to service on port {minimum} or higher."
        )
    return port
```

See also [../modern/errors.md](../modern/errors.md) for `ExceptionGroup`, chaining patterns, and custom exception design.

## Mutable global state

Avoid it. It breaks encapsulation and interacts badly with imports (module-level code runs at import time).

- Module-level **constants** (`UPPER_SNAKE`) are encouraged.
- If mutable global state is truly needed, name it with a leading `_` and gate access through public functions. Document why in a comment.

## Nested / inner classes and functions

Fine when closing over a local variable other than `self`/`cls`, or for decorators. Do **not** nest a function just to hide it from a module — prefix with `_` at module level instead so tests can still reach it.

## Comprehensions & generator expressions

Use for simple cases. Optimize for readability, not conciseness.

**Rules:**

- One `for` clause and at most one `if` clause on a single line.
- If you need multiple `for`s or multiple filters, either split across lines with clear indentation *or* use a plain `for` loop.
- Generator expressions (`(x for x in ...)`) avoid materializing a list — prefer them when the result is consumed once.

```python
# Yes
result = [transform(x) for x in items if x is not None]

result = [
    transform({"key": k, "value": v}, color="black")
    for k, v in items(source)
    if is_interesting(k, v)
]

# No — too many clauses on one line
result = [(x, y) for x in range(10) for y in range(5) if x * y > 10]
```

## Default iterators and operators

Prefer default iteration and membership. Container types define `__iter__` and `__contains__`.

```python
# Yes
for key in adict: ...
if obj in alist: ...
for line in a_file: ...
for k, v in adict.items(): ...

# No
for key in adict.keys(): ...
for line in a_file.readlines(): ...
```

Never mutate a container while iterating over it.

## Generators

- Use `Yields:` in the docstring for generator functions.
- If the generator manages an expensive resource, force cleanup — build it with the `@contextlib.contextmanager` decorator (a `try`/`finally` around the `yield`) so callers must use `with`.
- Prefer generator expressions or `yield` over building intermediate lists when the caller consumes once.

## Lambda functions

- OK for one-liners.
- Prefer the `operator` module (`operator.mul`, `operator.itemgetter(0)`) over `lambda x, y: x * y` / `lambda x: x[0]`.
- If the body is multi-line or > ~60 chars, define a named nested function.

## Conditional expressions

`x = a if cond else b` — OK for simple cases. Each part fits on one line. If it wraps, break into a full `if`/`else`.

## Default argument values

- **Never a mutable default.** `def f(x: list[int] | None = None): x = x or []`.
- Empty tuples (`()`) are immutable and OK.
- Defaults evaluated at import time — never `def f(t=time.time()):`, never `def f(x=_FLAGS.value):`.

## Properties

Use `@property` for cheap, straightforward, unsurprising computed attributes. Don't use `@property` for anything expensive, side-effecting, or that a subclass might want to override — expose a method instead.

```python
class Circle:
    def __init__(self, radius: float) -> None:
        self._radius = radius

    @property
    def area(self) -> float:
        return math.pi * self._radius ** 2
```

Don't wrap trivial passthroughs — just make the attribute public.

## True/False evaluations

- **`is None` / `is not None`** for `None` checks. `== None` is wrong.
- **Implicit falsy for containers/strings**: `if not seq:`, `if not s:`.
- **Never compare booleans with `==`.** `if not x:`, not `if x == False:`.
- **Integers are risky.** `if count:` treats `None` as `0`. If both are possible and mean different things, be explicit: `if count is not None and count > 0:`.
- **NumPy arrays** raise on truthiness — use `arr.size` or `arr.any()`/`.all()`.

## Lexical scoping

OK. Watch for the classic PEP 227 gotcha: assigning to a name inside a function makes it local *for the whole function*, shadowing an outer variable of the same name.

## Decorators

Judicious use only. Rules:

- Decorators run at import time — no external I/O, no DB/socket/file access in the decorator body.
- Document decorators clearly (say "This is a decorator." in the docstring).
- Unit-test decorators.
- Never use `@staticmethod` unless forced to by an external API. Use a module-level function instead.
- Use `@classmethod` for named constructors or class-wide state (`@classmethod def from_json(cls, data): ...`).

Preserve wrapped signatures with `functools.wraps` (and `ParamSpec` for typing):

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")

def timed(fn: Callable[_P, _R]) -> Callable[_P, _R]:
    @wraps(fn)
    def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        ...
        return fn(*args, **kwargs)
    return inner
```

## Threading

- **Do not rely on the atomicity of built-in types.** Even dict operations can be non-atomic when `__hash__`/`__eq__` are Python-defined.
- Use `queue.Queue` to hand data between threads.
- Otherwise use `threading` primitives; prefer `threading.Condition` over raw locks.
- For CPU-bound work, use `multiprocessing` or a native extension — the GIL will serialize threads. (Free-threaded builds are experimental in 3.13 and officially supported but still optional in 3.14; don't assume them.)

### Threads vs processes vs asyncio

| Workload                                      | Use                                                    |
| --------------------------------------------- | ------------------------------------------------------ |
| Many concurrent network/IO waits              | `asyncio` (see [../modern/async.md](../modern/async.md)) |
| A few blocking IO calls inside an async app   | `asyncio.to_thread(...)`                               |
| Blocking IO in a sync app                     | `concurrent.futures.ThreadPoolExecutor`                |
| CPU-bound work (parsing, compression, math)   | `concurrent.futures.ProcessPoolExecutor`               |
| CPU-bound work on arrays                      | A native library that releases the GIL (`numpy`, `polars`) |

`concurrent.futures` gives one API over both pools:

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor() as pool:
    results = list(pool.map(expensive_pure_function, items))
```

- Arguments and return values must be picklable; the callable must be importable (no lambdas, no closures).
- `pool.map` propagates the first exception when you consume the iterator. Use `submit` + `as_completed` when you need per-item error handling.
- **`asyncio` does not make CPU-bound work faster.** A `TaskGroup` full of CPU-bound coroutines runs on one thread and blocks the loop. Hand that work to `asyncio.to_thread` (if the hot loop releases the GIL) or `run_in_executor` with a process pool.

## Power features

Avoid metaclasses, dynamic imports, `__init_subclass__` tricks, `getattr`/`setattr` on `self`, `__del__`-based cleanup, monkey-patching, on-the-fly compilation. Stdlib uses of these (e.g. `abc.ABCMeta`, `enum`, `dataclasses`) are fine.

## `from __future__` imports

- `from __future__ import annotations` is optional in 3.11+; you may still use it for lazily-evaluated annotations and to enable forward references without quotes. It changes behavior of runtime tools that read `__annotations__` (e.g. `pydantic` needs `model_rebuild()` when using it). See [../modern/typing.md](../modern/typing.md).
- Other `from __future__` imports (`generator_stop`, `division`, etc.) are only relevant to older versions and can be dropped.

## Type-annotated code

**Strongly encouraged.** Type-check with `mypy` or `pyright` in CI.

- Annotate public APIs.
- Annotate code that's had type-related bugs before, or that's hard to read.
- You don't have to annotate every internal helper. Use judgment.

Full details in [type-annotations.md](type-annotations.md) and [../modern/typing.md](../modern/typing.md).
