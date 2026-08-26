# Type Annotations (pyguide §3.19)

Distilled from [Google Python Style Guide §3.19](https://google.github.io/styleguide/pyguide.html#319-type-annotations). Targeting Python 3.11+. For advanced patterns (Protocol, ParamSpec, overloads, PEP 695) see [../modern/typing.md](../modern/typing.md).

## General rules

- **Annotate public APIs.** Module-level functions, class methods with public callers, dataclasses.
- **Do not annotate `self` / `cls`.** Use `Self` (from `typing` in 3.11+) when the return type needs to refer to the current class:

```python
from typing import Self

class BaseClass:
    @classmethod
    def create(cls) -> Self:
        return cls()

    def merge(self, other: Self) -> Self:
        ...
```

- **Annotate `__init__` as `-> None`**, and nothing else on it (never annotate `self`). The pyguide only says you needn't feel compelled to, but `mypy --strict` and ruff's `ANN204` both require it, and it's what makes a checker analyze the body at all:

```python
class Cache:
    def __init__(self, ttl: int = 60) -> None:
        self._ttl = ttl
```
- **`Any` is a last resort.** Prefer `object`, a `Protocol`, or a bound `TypeVar`. `Any` disables checking; `object` makes the caller narrow before using.
- You are not required to annotate every function. Focus on:
  - Public APIs.
  - Code that has had type-related bugs.
  - Code that is complex or non-obvious.
  - Stable modules where flexibility is no longer needed.
- Enable a type checker (`mypy` or `pyright`) in CI. See [../modern/tooling.md](../modern/tooling.md).

## Line breaking

When a signature doesn't fit on one line, break between parameters (not between a name and its type). Prefer one parameter per line with a trailing comma so the return type gets its own line:

```python
def my_method(
    self,
    first_var: int,
    second_var: Foo,
    third_var: Bar | None,
) -> int:
    ...
```

If everything fits, keep it on one line:

```python
def my_method(self, first_var: int) -> int: ...
```

Only if a single `name: LongType` doesn't fit, use a type alias. As a last resort, break after the colon and indent 4:

```python
# Yes — introduce an alias
type LongName = long_module_name.LongTypeName  # PEP 695 syntax (3.12+)

def my_function(long_variable_name: LongName) -> None: ...

# Last resort
def my_function(
    long_variable_name:
        long_module_name.LongTypeName,
) -> None: ...
```

## Forward references

For self-referential or later-defined class names, either use `from __future__ import annotations` (lazy evaluation) or a string literal:

```python
from __future__ import annotations
from collections.abc import Sequence

class Node:
    def __init__(self, children: Sequence[Node]) -> None:
        ...
```

Without `__future__`:

```python
class Node:
    def __init__(self, children: Sequence["Node"]) -> None:
        ...
```

**Caveat:** `from __future__ import annotations` makes annotations strings at runtime. Libraries that inspect annotations at runtime (pydantic, dataclasses in some patterns, attrs, FastAPI dependency injection) may need `typing.get_type_hints()` or model rebuilds. Prefer 3.11+ inline forward refs when in doubt.

## Default values

Space around `=` **only** when the parameter is annotated:

```python
def f(a: int = 0) -> int: ...   # yes
def f(a=0) -> int: ...          # yes
def f(a:int=0) -> int: ...      # no
```

## `NoneType` / optionality

**Optionality must be declared.** Use `X | None` (PEP 604, 3.10+). The older `Optional[X]` / `Union[X, None]` also works but is discouraged in new code.

```python
# Yes
def modern(a: str | int | None, b: str | None = None) -> str: ...

# Discouraged in new 3.10+ code
def older(a: Union[str, int, None], b: Optional[str] = None) -> str: ...

# No — implicit optional
def wrong(a: str = None) -> str: ...
```

## Type aliases

Complex types get an alias. Name in `CapWords`; prefix with `_` for module-private aliases.

**3.12+ syntax (PEP 695):**

```python
type LossAndGradient = tuple[Tensor, Tensor]
type ComplexTFMap = Mapping[str, LossAndGradient]
```

**3.10–3.11:**

```python
from typing import TypeAlias

_LossAndGradient: TypeAlias = tuple[Tensor, Tensor]
ComplexTFMap: TypeAlias = Mapping[str, _LossAndGradient]
```

## Ignoring types

- `# type: ignore[rule-name]` — narrow, includes the specific rule.
- `# pyright: ignore[rule]` — pyright-specific.
- Never blanket `# type: ignore` without a rule.

Add a short comment explaining why:

```python
result = untyped_lib.do_thing()  # type: ignore[no-untyped-call]  # third-party lacks stubs
```

## Typing variables

Use annotated assignments for hard-to-infer values:

```python
config: Config = load_config()
counts: dict[str, int] = {}
```

**Never** the old `# type: X` end-of-line comment form.

## Tuples vs lists

- `list[int]` — homogeneous, mutable.
- `tuple[int, ...]` — homogeneous, immutable, arbitrary length.
- `tuple[int, str, float]` — fixed-shape tuple. Common as a function's return type.

Prefer `tuple` for return values that group heterogeneous things; consider a `NamedTuple` or `@dataclass` if the caller has to index by position.

## Type variables

`TypeVar` and `ParamSpec` create generics. See [../modern/typing.md](../modern/typing.md) for full patterns.

```python
from collections.abc import Callable
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_T = TypeVar("_T")

def head(items: list[_T]) -> _T:
    return items[0]

def log_calls(f: Callable[_P, _T]) -> Callable[_P, _T]:
    def inner(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        return f(*args, **kwargs)
    return inner
```

Naming: descriptive if externally visible or constrained; short `_T` / `_P` OK if module-private and unconstrained. See [naming.md](naming.md#type-variables).

## String types

- Use `str` for text, `bytes` for binary.
- **Do not use** `typing.Text` — it's a 2/3 compat shim.
- Use `typing.AnyStr` only when *all* string arguments and the return type must be the same kind (all `str` or all `bytes`):

```python
from typing import AnyStr

def check_length(x: AnyStr) -> AnyStr:
    if len(x) <= 42:
        return x
    raise ValueError()
```

## Imports for typing

For symbols from `typing` and `collections.abc`, import the symbols themselves; multiple symbols on one line are allowed:

```python
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Generic, cast
```

- Do not shadow these names with local variables/parameters. If a collision is unavoidable, alias: `from typing import Any as AnyType`.
- **Prefer `collections.abc` in parameter positions** (accept the widest type that works), **prefer built-ins in return positions** (return the concrete type callers can rely on):

```python
def transform_coordinates(
    original: Sequence[tuple[float, float]],
) -> list[tuple[float, float]]:
    ...
```

- Never `typing.List` / `typing.Tuple` / `typing.Dict` in new code — use `list`, `tuple`, `dict`.

## Conditional imports

For expensive typing-only imports (large stubs, avoiding cycles), use `TYPE_CHECKING`:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myproject.expensive_module import HeavyClient

def handle(client: HeavyClient) -> None: ...
```

Without `from __future__ import annotations`, quote the type: `client: "HeavyClient"`.

## Circular dependencies

Break cycles by moving types to a shared module (`_types.py`), by using `TYPE_CHECKING` imports (above), or by refactoring — a real cycle usually means the seam is in the wrong place.

## Generics

Two syntaxes:

**PEP 695 (3.12+) — preferred when supported:**

```python
def first[T](items: Sequence[T]) -> T:
    return items[0]

class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()
```

**Pre-3.12:**

```python
from typing import Generic, TypeVar

_T = TypeVar("_T")

class Stack(Generic[_T]):
    def __init__(self) -> None:
        self._items: list[_T] = []

    def push(self, item: _T) -> None:
        self._items.append(item)

    def pop(self) -> _T:
        return self._items.pop()
```

See [../modern/typing.md](../modern/typing.md) for `Protocol`, `overload`, `TypeGuard`, and bounded/constrained type variables.
