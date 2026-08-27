# Data Modeling

How to represent structured data: pick between `@dataclass`, `pydantic.BaseModel`, `TypedDict`, `NamedTuple`, and `Protocol`.

## Decision matrix

| Need                                                                 | Use                                   |
| -------------------------------------------------------------------- | ------------------------------------- |
| Internal value object; no validation                                 | `@dataclass(frozen=True, slots=True)` |
| Value object with hashing + pattern matching                         | `@dataclass(frozen=True, slots=True)` |
| Validate JSON / HTTP / YAML / config at the boundary                 | `pydantic.BaseModel`                  |
| Type-check a dict literal (e.g. an API response schema)              | `TypedDict`                           |
| Small, immutable, positional record                                  | `typing.NamedTuple`                   |
| Structural contract implementers must satisfy (duck-typed interface) | `Protocol`                            |
| Sum type / tagged union                                              | `Union` of dataclasses + `match`      |
| Enumerable set of constants                                          | `Enum` / `StrEnum` / `IntEnum`        |

**Rule of thumb:** default to `@dataclass`. Cross into `pydantic` only where **untrusted input** meets your code (HTTP handlers, config loaders, message consumers).

## `@dataclass`

Prefer `frozen=True` (immutable, hashable) and `slots=True` (faster attribute access, less memory, catches typos).

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime

@dataclass(frozen=True, slots=True)
class Money:
    """A currency amount."""

    amount_minor: int
    currency: str  # ISO 4217

    def add(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount_minor + other.amount_minor, self.currency)


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Order:
    id: str
    customer_id: str
    items: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)
```

**Key rules:**

- `default_factory` for mutable defaults — never `items: list[str] = []`.
- **`datetime.utcnow()` is deprecated (3.12+) and returns a naive datetime.** Use `datetime.now(UTC)` via a small factory (a `lambda` works too). Applies everywhere `created_at` / `updated_at` fields appear.
  - `datetime.UTC` is the 3.11+ alias for `datetime.timezone.utc` — same object, and it's the spelling ruff's `UP017` rewrites to when `target-version` is `py311` or higher. Write `UTC` so `ruff check --fix` leaves your code alone. Below 3.11, `timezone.utc` is the only spelling.
- **`frozen=True` + a mutable field silently breaks hashing.** `@dataclass(frozen=True)` auto-generates `__hash__`, which hashes every field that takes part in comparison. A `list`/`dict`/`set` field then raises `TypeError: unhashable type: 'list'` the first time the instance is used as a dict key or set member. Three ways out, cheapest first:
  - `field(hash=False, compare=False)` on the offending field — keeps `frozen=True`, keeps value equality on every *other* field. Usually what you want.
  - Freeze the container: `items: tuple[str, ...]`.
  - `eq=False` — drops the generated `__eq__` *and* `__hash__`, falling back to identity for both. Only when identity semantics are actually correct.
- **`slots=True` breaks `functools.cached_property`.** `cached_property` writes to `self.__dict__`, which slotted classes don't have. Either drop `slots=True` on classes that need cached properties, or add `"__dict__"` to `__slots__` manually (defeats most of the point), or compute the value eagerly in `__post_init__`.
- `kw_only=True` when there are many fields with defaults, to avoid `TypeError: non-default argument follows default argument`.
- `order=True` for sortable value objects (produces `__lt__` etc.).
- `__post_init__` for cheap invariants (raise on invalid combinations). Don't do I/O here.

```python
@dataclass(frozen=True, slots=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"end before start: {self.start=} {self.end=}")
```

## Pattern matching + dataclasses

Combine `match` with dataclasses for tagged-union style:

```python
@dataclass(frozen=True, slots=True)
class Success:
    value: str

@dataclass(frozen=True, slots=True)
class Failure:
    error: str

Result = Success | Failure

def render(r: Result) -> str:
    match r:
        case Success(value=v):
            return f"OK: {v}"
        case Failure(error=e):
            return f"ERR: {e}"
```

Use `typing.assert_never(other)` in the fallthrough for exhaustiveness (see [typing.md](typing.md#never-and-noreturn)).

## Pydantic v2

Use pydantic v2 at **IO/config/API boundaries**. It parses, validates, and serializes; it's not a general-purpose replacement for `@dataclass`.

```python
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class OrderRequest(BaseModel):
    """Incoming order payload."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    customer_id: str = Field(min_length=1)
    items: list[str] = Field(min_length=1)
    total_minor: int = Field(ge=0)
    submitted_at: datetime
```

**Defaults to lean on:**

- `extra="forbid"` — catch typos in incoming payloads.
- `frozen=True` — hashable, immutable models.
- `str_strip_whitespace=True` — normalize input.
- `Field(..., description=...)` — flows into the generated JSON schema.
- Use `Annotated[T, Field(...)]` when the field is a reusable domain type:

```python
from typing import Annotated

CustomerId = Annotated[str, Field(min_length=1, pattern=r"^cus_[a-zA-Z0-9]+$")]

class OrderRequest(BaseModel):
    customer_id: CustomerId
    ...
```

**Field validators (v2 style):**

```python
from pydantic import field_validator, model_validator

class OrderRequest(BaseModel):
    items: list[str]

    @field_validator("items")
    @classmethod
    def not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("items must be non-empty")
        return v

    @model_validator(mode="after")
    def check_totals(self) -> "OrderRequest":
        ...
        return self
```

**Parsing:**

```python
OrderRequest.model_validate(json_payload)      # from dict
OrderRequest.model_validate_json(raw_bytes)     # from JSON string/bytes
model.model_dump()                              # → dict
model.model_dump_json()                         # → JSON str
```

**Do not** use `.dict()` / `.json()` / `.parse_obj()` — those are v1 and deprecated.

### When _not_ to use pydantic

- Internal-only value objects (dataclass is faster and clearer).
- Anywhere `model_config` and `Field` clutter the type without adding validation value.
- Hot loops where allocation matters — pydantic v2 is fast (Rust core) but a dataclass is still faster.

## `TypedDict`

For statically typing dict literals whose keys and value types are known — often to type an existing JSON response without allocating a new class.

```python
from typing import NotRequired, TypedDict

class UserPayload(TypedDict):
    id: str
    name: str
    email: NotRequired[str]  # optional key

def render(u: UserPayload) -> str:
    return f"{u['name']} ({u['id']})"
```

- Use `total=False` (class-level) or `NotRequired[...]` (per-field) for optional keys.
- `TypedDict` provides no runtime validation. If the data comes from outside your process, validate first (pydantic) and pass the model, not the dict.
- **Handing a `TypedDict` to pydantic on 3.11?** Older pydantic v2 releases required `typing_extensions.TypedDict` below Python 3.12 and raised at schema-build time on the `typing` one; recent releases handle `typing.TypedDict` on 3.11 in most cases. Rather than guess at your pinned version, `from typing_extensions import TypedDict` whenever the type will reach a `TypeAdapter` or a `BaseModel` field — it is the same object on 3.12+ and costs nothing.

## `NamedTuple`

Immutable, positional, tiny. Prefer a `@dataclass(frozen=True, slots=True)` unless you specifically need tuple-unpacking or positional access.

```python
from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float

p = Point(1.0, 2.0)
x, y = p     # unpacks
```

## `Protocol` for domain interfaces

When many implementations must satisfy an interface but you don't want inheritance — see [typing.md](typing.md#protocol--structural-typing).

```python
from typing import Protocol

class UserRepository(Protocol):
    def get(self, user_id: str) -> User | None: ...
    def save(self, user: User) -> None: ...
```

Any class with matching methods satisfies `UserRepository` — no `class SqlUserRepository(UserRepository)` needed. Improves testability (a `dict`-backed fake satisfies the protocol without any base class).

## Enums

```python
from enum import Enum, IntEnum, StrEnum, auto

class Role(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"

class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
```

- Prefer `StrEnum` / `IntEnum` when values will be serialized — the enum _is_ the string/int.
- `IntEnum` is stdlib since forever; `StrEnum` was added in **3.11**. On 3.10 the equivalent is `class Role(str, Enum):` — mixing in `str` gives you the same JSON-friendly behavior.
- Use `auto()` when the underlying value doesn't matter (only comparisons do).
- Use `Enum` when values are arbitrary domain-meaningful literals.

## Serialization boundaries

- **Inbound:** parse with pydantic (`model_validate` / `model_validate_json`). Reject unknown fields (`extra="forbid"`).
- **Internal:** work with dataclasses / domain objects. Type checker verifies shape.
- **Outbound:** convert to a pydantic response model (or `dataclasses.asdict` + `json.dumps` for lightweight cases). Do not leak internal fields.

```python
# Boundary
incoming = OrderRequest.model_validate_json(body)

# Convert to domain object (server-assigned id, server clock)
order = Order(
    id=new_id(),
    customer_id=incoming.customer_id,
    items=list(incoming.items),
    created_at=datetime.now(UTC),
)

# On the way out
response = OrderResponse.model_validate(order, from_attributes=True)
return response.model_dump()
```

### When the wire shape _is_ the domain shape: `TypeAdapter`

The example above is a genuine transformation — the server assigns `id` and the timestamp, so `OrderRequest` and `Order` are legitimately distinct classes. When the wire shape and the domain shape are identical, defining the class twice (once as a `pydantic.BaseModel`, once as a `@dataclass`) is duplication that will drift.

`pydantic.TypeAdapter` gives you validation for any type — including a plain stdlib `@dataclass` — without defining a second class:

```python
from dataclasses import dataclass
from pydantic import TypeAdapter

@dataclass(frozen=True, slots=True)
class SkillRef:
    """A reference to a published skill."""

    owner: str
    name: str
    version: str

_skill_ref = TypeAdapter(SkillRef)

def parse_skill_ref(payload: object) -> SkillRef:
    return _skill_ref.validate_python(payload)         # dict/JSON-ish input

def parse_skill_ref_json(raw: str | bytes) -> SkillRef:
    return _skill_ref.validate_json(raw)               # raw JSON

def dump_skill_ref(ref: SkillRef) -> dict[str, object]:
    return _skill_ref.dump_python(ref)                 # or dump_json()
```

**One definition** — the dataclass — serves both the type system and the wire boundary. `TypeAdapter` also works on `TypedDict`, `list[Foo]`, unions, `NewType`, etc., so you can validate collection shapes without defining a wrapper model:

```python
_skill_refs = TypeAdapter(list[SkillRef])
refs = _skill_refs.validate_json(raw_body)
```

Reserve `pydantic.BaseModel` for cases where you _want_ a distinct wire class — extra fields on the request, computed serializer aliases, or bidirectional schema/OpenAPI generation.

## Anti-patterns

- **Dicts as records** across module boundaries — makes refactoring dangerous. Use a `@dataclass` or `TypedDict`.
- **`pydantic.BaseModel` everywhere.** Cognitive overhead + import weight in domain code that doesn't need validation.
- **`__init__` doing validation on a `@dataclass`.** Use `__post_init__` for cheap invariants; use a factory `classmethod` for parsing.
- **Mutable defaults**: `items: list[str] = []`. Always `field(default_factory=list)`.
- **Deep inheritance hierarchies** to model variants. Prefer a union of dataclasses + `match`.
