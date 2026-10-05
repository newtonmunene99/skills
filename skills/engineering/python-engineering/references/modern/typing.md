# Advanced Typing (Modern Python 3.11+)

Covers patterns that go beyond the pyguide's §3.19: `Protocol`, `TypeVar` bounds and variance, `ParamSpec`, `Self`, `@overload`, `override`, `TypeGuard`/`TypeIs`, `Never`, PEP 695 generics, and typed decorators.

For pyguide baseline rules (line breaking, forward refs, `NoneType`, aliases, imports), see [../pyguide/type-annotations.md](../pyguide/type-annotations.md).

## Contents

- [Version floor](#version-floor)
- [Choose the right generic tool](#choose-the-right-generic-tool)
- [`Protocol` — structural typing](#protocol--structural-typing)
- [`TypeVar` — bounds, constraints, variance](#typevar--bounds-constraints-variance)
- [`ParamSpec` — typed decorators](#paramspec--typed-decorators)
- [`Self`](#self)
- [`@overload`](#overload)
- [`override`](#override)
- [`TypeGuard` and `TypeIs`](#typeguard-and-typeis)
- [`Never` and `NoReturn`](#never-and-noreturn)
- [`Final` and `ClassVar`](#final-and-classvar)
- [`Annotated` — carry metadata alongside types](#annotated--carry-metadata-alongside-types)
- [PEP 695 generics (3.12+)](#pep-695-generics-312)
- [Callable signatures](#callable-signatures)
- [Generic containers in signatures](#generic-containers-in-signatures)
- [`Any` vs `object`](#any-vs-object)
- [`cast` sparingly](#cast-sparingly)
- [Common pitfalls](#common-pitfalls)

## Version floor

The skill targets 3.11, but several names below landed later. On a version that predates them, import from `typing_extensions` — the runtime objects are the same and type checkers treat them identically.

| Name                              | In `typing` since | Below that                    |
| --------------------------------- | ----------------- | ----------------------------- |
| `Self`, `Never`, `assert_never`   | 3.11              | —                             |
| `override`                        | **3.12**          | `typing_extensions.override`  |
| PEP 695 syntax (`def f[T]`)       | **3.12**          | `TypeVar` / `Generic[T]`      |
| `TypeIs`                          | **3.13**          | `typing_extensions.TypeIs`    |

```python
import sys

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override
```

In practice: if you already depend on `typing_extensions` (pydantic pulls it in), just import from it unconditionally and drop the shim when the floor moves.

## Choose the right generic tool

| Need                                    | Use                                                    |
| --------------------------------------- | ------------------------------------------------------ |
| Function/method generic in one type     | `TypeVar` or PEP 695 `def f[T](...)`                   |
| Class generic in one type               | `Generic[T]` or PEP 695 `class C[T]`                   |
| Structural interface ("has method `f`") | `Protocol`                                             |
| Preserve full callable signature        | `ParamSpec` + `TypeVar`                                |
| Multiple type-safe overloads            | `@overload`                                            |
| Refine a type after a check             | `TypeGuard` (3.10+) or `TypeIs` (3.13+)                |
| Function that never returns             | `-> Never` (3.11+) / `NoReturn`                        |
| Return the current class type           | `Self` (3.11+)                                         |
| Fixed-shape record                      | `TypedDict` (see [data-modeling.md](data-modeling.md)) |

## `Protocol` — structural typing

Prefer `Protocol` over abstract base classes for duck-typed interfaces. Implementers don't have to inherit — they just need the right methods.

```python
from collections.abc import Iterator
from typing import Protocol

class Readable(Protocol):
    def read(self, n: int, /) -> bytes: ...

def consume(source: Readable) -> bytes:
    return source.read(1024)
```

Runtime checkability: decorate with `@runtime_checkable` to enable `isinstance(x, MyProto)`. Only method presence is checked, not signatures — use sparingly.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...
```

## `TypeVar` — bounds, constraints, variance

```python
from collections.abc import Sequence
from typing import TypeVar

# Unconstrained — short private name is fine
_T = TypeVar("_T")

# Bound: T must be a subtype of Comparable. Bound TypeVars get a descriptive
# name (see ../pyguide/naming.md#type-variables).
ComparableType = TypeVar("ComparableType", bound="SupportsLessThan")

# Constrained: T must be exactly one of these types (never their union)
AnyStrType = TypeVar("AnyStrType", str, bytes)

def smallest(items: Sequence[ComparableType]) -> ComparableType: ...
def echo(x: AnyStrType) -> AnyStrType: ...
```

**Don't reach for the `numbers` ABCs as bounds.** `bound=numbers.Real` looks right but doesn't work statically — typeshed never registers `int`/`float` as subclasses of `numbers.Real`, so `smallest([1, 2])` fails to type-check ([mypy #3186](https://github.com/python/mypy/issues/3186)). Use `bound=float` (which the type system special-cases to accept `int`), or a `Protocol`:

```python
from typing import Protocol, Self

class SupportsLessThan(Protocol):
    def __lt__(self, other: Self, /) -> bool: ...
```

**Variance:** the default `TypeVar` is invariant. Use `covariant=True` for container-like read-only outputs, `contravariant=True` for consumers. In most application code, invariant is the right default — only add variance when the type checker demands it or you're building a library.

## `ParamSpec` — typed decorators

`ParamSpec` captures a callable's full signature so decorators don't erase types.

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")

def logged(fn: Callable[_P, _R]) -> Callable[_P, _R]:
    @wraps(fn)
    def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        return fn(*args, **kwargs)
    return inner

@logged
def add(a: int, b: int) -> int:
    return a + b
```

Callers of `add` still see `add(a: int, b: int) -> int`.

## `Self`

Return the current class type from methods (avoids repeating the class name and stays correct in subclasses):

```python
from typing import Self

class QueryBuilder:
    def where(self, cond: str) -> Self:
        ...
        return self

    @classmethod
    def new(cls) -> Self:
        return cls()
```

## `@overload`

Declare multiple type-safe signatures for a single implementation:

```python
from typing import overload

@overload
def get(key: str) -> str: ...
@overload
def get(key: str, default: int) -> str | int: ...

def get(key: str, default: int | None = None) -> str | int:
    ...
```

Overloads must all appear before the runtime implementation. Only the overloads participate in type checking; the implementation signature is checked for compatibility with each of them but is invisible to callers. Annotate it anyway — the checker verifies the body against it.

## `override`

Mark a method that deliberately overrides a base-class method. The checker then errors if the base method is renamed or removed — catching the silent-dead-code failure that refactors cause.

```python
from typing import override  # 3.12+; typing_extensions below that

class JsonStore(Store):
    @override
    def load(self, key: str) -> bytes: ...
```

Google style also lets `@override` stand in for a repeated docstring when the contract is unchanged — see [../pyguide/docstrings.md](../pyguide/docstrings.md#overridden-methods).

## `TypeGuard` and `TypeIs`

Narrow a union type after a boolean check.

**`TypeGuard`** (3.10+, positive narrowing only — narrows in the `if` branch but leaves the `else` branch's type untouched):

```python
from typing import TypeGuard

def is_str_list(x: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(item, str) for item in x)

def upper_all(items: list[object]) -> list[str]:
    if is_str_list(items):
        return [s.upper() for s in items]
    return []
```

**`TypeIs`** (3.13+ in `typing`, `typing_extensions.TypeIs` below that — both positive and negative narrowing, stronger, prefer when available):

```python
from typing import TypeIs

def is_string(x: object) -> TypeIs[str]:
    return isinstance(x, str)
```

## `Never` and `NoReturn`

- `NoReturn` — function never returns (raises or exits).
- `Never` — the bottom type; also used with `assert_never` for exhaustiveness in `match` statements.

```python
from typing import Never, assert_never

def die(msg: str) -> Never:
    raise SystemExit(msg)

def handle(shape: Circle | Square) -> float:
    match shape:
        case Circle(radius=r):
            return math.pi * r ** 2
        case Square(side=s):
            return s * s
        case _ as other:
            assert_never(other)
```

The `assert_never` call makes the type checker fail if a new variant is added but not handled.

## `Final` and `ClassVar`

- `Final` — immutable after initial assignment (compile-time, not enforced at runtime).
- `ClassVar` — attribute on the class, not the instance.

```python
from typing import ClassVar, Final

MAX_CONN: Final = 100

class Cache:
    default_ttl: ClassVar[int] = 60
```

## `Annotated` — carry metadata alongside types

`Annotated[T, ...]` attaches metadata visible to frameworks (pydantic, FastAPI, msgspec) while remaining transparent to type checkers.

```python
from typing import Annotated
from pydantic import Field

Age = Annotated[int, Field(ge=0, le=150)]

def register(name: str, age: Age) -> None: ...
```

## PEP 695 generics (3.12+)

Cleaner syntax; no explicit `TypeVar` at module scope.

```python
def head[T](items: list[T]) -> T:
    return items[0]

class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

type Result[T] = tuple[bool, T | None]
```

Backwards-compatible option: keep `TypeVar` for 3.11 support; migrate once 3.12 is the floor.

## Callable signatures

- `Callable[[int, str], bool]` — positional signature.
- `Callable[..., bool]` — any args (loses arg-type info).
- Use `Protocol` with `__call__` for keyword-argument signatures:

```python
class Handler(Protocol):
    def __call__(self, *, request: Request, timeout: float = 30) -> Response: ...
```

## Generic containers in signatures

Follow the pyguide default: **accept `Sequence`/`Mapping`/`Iterable`**, **return concrete `list`/`dict`/`tuple`**.

```python
from collections.abc import Iterable, Mapping, Sequence

def normalize(names: Sequence[str]) -> list[str]:
    return [n.strip().lower() for n in names]

def index(items: Iterable[User]) -> dict[str, User]:
    return {u.id: u for u in items}
```

## `Any` vs `object`

- **`Any`** disables checking — the value can do anything.
- **`object`** is the top type — the caller must narrow (with `isinstance` or `cast`) before using type-specific methods.

Default to `object`. Reach for `Any` when a value truly is opaque (raw JSON before parsing, generic dispatcher).

## `cast` sparingly

`cast(T, x)` is a runtime no-op; it just tells the checker "trust me". Prefer restructuring code so the checker can infer the type. Every `cast` is a soft `# type: ignore`.

## Common pitfalls

- Annotating `self` or `cls` (usually unnecessary — the checker infers).
- Using `list[...]` in an `isinstance` check — use `list` alone.
- Writing `Optional[X]` in new code. It means exactly `X | None` — same type, older spelling. Use the `|` form.
- Assuming `from __future__ import annotations` is free for runtime-introspecting libraries. Pydantic v2 and dataclasses resolve string annotations fine; what breaks is a name that isn't importable at module scope when resolution happens (a type defined inside a function, or one only imported under `TYPE_CHECKING` in a *different* module). The fix is `model_rebuild()` or moving the type somewhere resolvable — see [../pyguide/type-annotations.md](../pyguide/type-annotations.md#forward-references).
- Using `Any` when `object` would work.
