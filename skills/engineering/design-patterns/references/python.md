# Python: idiomatic patterns

This file is the source of truth for what each pattern looks like in Python 3.11+.
The catalog files ([creational.md](creational.md), [structural.md](structural.md),
[behavioral.md](behavioral.md)) say when a pattern is worth it and what it costs.
Here the only question is: once the force is real, what is the smallest Python that
answers it? Names that a snippet does not define (`Order`, `Document`, `ApiClient`)
stand for your own domain types.

## Contents

- [What changes the catalog in Python](#what-changes-the-catalog-in-python)
- [SOLID in Python](#solid-in-python)
- [Creational](#creational): [Factory Method](#factory-method),
  [Abstract Factory](#abstract-factory), [Builder](#builder),
  [Prototype](#prototype), [Singleton](#singleton)
- [Structural](#structural): [Adapter](#adapter), [Bridge](#bridge),
  [Composite](#composite), [Decorator](#decorator), [Facade](#facade),
  [Flyweight](#flyweight), [Proxy](#proxy)
- [Behavioral](#behavioral): [Chain of Responsibility](#chain-of-responsibility),
  [Command](#command), [Interpreter](#interpreter), [Iterator](#iterator),
  [Mediator](#mediator), [Memento](#memento), [Observer](#observer),
  [State](#state), [Strategy](#strategy), [Template Method](#template-method),
  [Visitor](#visitor)
- [Java in Python: smells to catch in review](#java-in-python-smells-to-catch-in-review)

## What changes the catalog in Python

- **Functions are values.** Strategy, Command, the steps of Template Method, and
  most factories become a function argument or a `dict` of callables. A class with
  `__init__` and one public method is usually a function in disguise.
- **Modules are singletons and facades.** A module is imported once per process and
  cached in `sys.modules`, so a module-level value is already one shared instance. A
  package whose `__init__.py` exports a few names, with the rest in `_private`
  modules, is already a facade.
- **Duck typing, checked by `typing.Protocol`.** Any object with the right methods
  fits. A `Protocol` lets mypy or pyright verify that without the implementation
  importing or inheriting anything. This is what makes Adapter, Decorator and Proxy
  cheap.
- **ABCs only when you need enforcement.** `abc.ABC` refuses to instantiate a
  subclass that is missing an abstract method. Use it when you own a plugin
  hierarchy and want that failure early. Otherwise a `Protocol` is lighter.
- **Generators are iterators.** `yield` turns any traversal into an Iterator with no
  class at all, and `yield from` delegates to a nested one.
- **`@decorator` syntax overlaps with the Decorator pattern but is not the same
  thing.** The `@` syntax wraps a function or class once, at definition time, for
  every caller. The pattern wraps an object at runtime, only for the callers you hand
  the wrapper to. `@retry` on a function is the pattern applied statically;
  `RetryingClient(client)` is the pattern applied per instance.
- **Context managers own acquire and release.** `with` gives Proxy-style lazy
  acquisition with guaranteed cleanup. `contextlib.contextmanager` builds one from a
  generator.
- **`match` and `functools.singledispatch`** give type-based dispatch without
  Visitor's double dispatch. `match` suits a closed set of types you own;
  `singledispatch` suits an open set that other modules extend.
- **Dataclasses give value semantics.** `dataclasses.replace` covers Prototype and
  Memento for flat data, and `frozen=True` makes a snapshot safe to share.
- **Keyword arguments with defaults** cover almost every use of Builder.
- **`__getattr__` forwards unknown attributes**, so a wrapper only defines the
  methods it changes. It also hides the surface from type checkers, so prefer
  explicit methods on anything public.
- **`enum.Enum` and `StrEnum`** give closed sets of states or kinds, and a `match`
  over one is checked for exhaustiveness with `typing.assert_never`.

## SOLID in Python

The same running examples as [solid.md](solid.md), in Python terms.

- **Single Responsibility:** a `User` dataclass, a `UserStore` that saves it, and a
  `send_welcome_email` function, rather than one `User` class that also writes SQL and
  sends mail. It applies to modules too: a `utils.py` that billing and marketing both
  keep editing has two actors.
- **Open/Closed:** a `ShippingCalculator` with an `if`/`elif` over ground, air and sea
  is fine until drones arrive and the same branch shows up in the label printer too.
  Only then is the fix earned: a `dict[str, Callable[[Parcel], Decimal]]` of cost
  functions, so a new carrier is one new entry.
- **Liskov Substitution:** `Penguin(Bird)` whose `fly()` raises `NotImplementedError`
  breaks every caller holding a `Bird`. Duck typing is no exemption. Give the callers
  that fly a narrower `Flier` protocol and leave `fly` off `Bird`. mypy and pyright
  flag incompatible override signatures, not a changed contract, so the rule lives in
  the docstring and the tests.
- **Interface Segregation and Dependency Inversion:** a `RobotWorker` stubbing `eat()`
  and `sleep()` to satisfy a fat `Worker` is the ISP smell. The fix for both principles
  is the same move: the consumer declares a small `Protocol` in its own terms, with no
  `I` prefix, and the entry point plugs in the concrete adapter.

```python
# store.py owns this protocol and imports nothing from stripe or paypal.
from decimal import Decimal
from typing import Protocol


class PaymentProcessor(Protocol):
    def charge(self, amount: Decimal, source: str) -> str: ...


class Store:
    def __init__(self, payments: PaymentProcessor) -> None:
        self._payments = payments  # was: self._payments = stripe.StripeClient(KEY)

    def checkout(self, cart: Cart, source: str) -> str:
        return self._payments.charge(cart.total(), source)


# main.py: the only place that knows which processor is real.
# store = Store(payments=StripeAdapter(stripe.StripeClient(api_key)))
```

## Creational

### Factory Method

**Idiomatic form:** a `@classmethod` alternative constructor for "build from another
format" (the stdlib's `datetime.fromisoformat`, `int.from_bytes`, `dict.fromkeys`),
or a plain function returning a `Protocol` for "pick the implementation".

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Self


@dataclass(frozen=True, slots=True)
class Money:
    cents: int
    currency: str

    @classmethod
    def parse(cls, text: str) -> Self:
        amount, currency = text.split()
        return cls(int(Decimal(amount) * 100), currency)


def open_store(url: str) -> BlobStore:
    if url.startswith("s3://"):
        return S3Store(url)
    return LocalStore(url)
```

**Avoid:** a `MoneyFactory` class, or an abstract `Creator` whose subclasses override
`create()`.

**Gotcha:** build with `cls(...)`, not `Money(...)`, and annotate `-> Self`, so a
subclass calling `parse` gets its own type back.

### Abstract Factory

**Idiomatic form:** a frozen dataclass that bundles the matching constructors,
chosen once at startup.

```python
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CloudKit:
    blob_store: Callable[[str], BlobStore]
    queue: Callable[[str], JobQueue]


AWS = CloudKit(blob_store=S3Store, queue=SQSQueue)
GCP = CloudKit(blob_store=GCSStore, queue=PubSubQueue)


def build_app(kit: CloudKit) -> App:
    return App(store=kit.blob_store("uploads"), jobs=kit.queue("jobs"))
```

**Avoid:** an `AbstractCloudFactory` ABC with one `...FactoryImpl` subclass per
provider. The kit above is the same guarantee with no hierarchy.

### Builder

**Idiomatic form:** keyword-only fields with defaults, validated in `__post_init__`.
The object is never half-built because it only exists once every argument is in.

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class HttpClientConfig:
    base_url: str
    timeout_s: float = 10.0
    retries: int = 3
    user_agent: str = "orders-service/1.0"

    def __post_init__(self) -> None:
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if self.retries < 0:
            raise ValueError("retries must not be negative")


config = HttpClientConfig(base_url="https://api.example.com", retries=5)
```

**Avoid:** `ConfigBuilder().with_timeout(5).with_retries(3).build()` for a flat set of
options. Keyword arguments already are that, checked by the type checker. A fluent
builder earns its place only for step-by-step assembly, like SQLAlchemy's
`select(...).where(...)`, and there each step should return a new immutable value.

**Gotcha:** never use a mutable default (`tags: list[str] = []`); dataclasses reject
it, and plain functions silently share it. Use `field(default_factory=list)`.

### Prototype

**Idiomatic form:** `dataclasses.replace` for "the same, but with these fields
changed". Keep fields immutable (`str`, `tuple`, `frozenset`) and the shallow copy is
all you need.

```python
import copy
from dataclasses import dataclass, field, replace


@dataclass(frozen=True, slots=True)
class ReportTemplate:
    title: str
    columns: tuple[str, ...]
    filters: dict[str, str] = field(default_factory=dict)


monthly = ReportTemplate("Monthly sales", ("region", "total"))
quarterly = replace(monthly, title="Quarterly sales")  # columns tuple is safely shared

# quarterly.filters is the SAME dict as monthly.filters: replace is shallow.
isolated = replace(monthly, filters=copy.deepcopy(monthly.filters))
```

**Avoid:** a `clone()` method on every class plus a prototype registry. Python
already has `copy.copy`, `copy.deepcopy`, and the `__copy__`/`__deepcopy__` hooks.

**Gotcha:** `replace`, `copy.copy` and `frozen=True` are all shallow. A mutable field
is shared between the original and every copy. Python 3.13 adds `copy.replace`,
which extends `replace` to any type that defines `__replace__`.

### Singleton

**Idiomatic form:** build the object once in `main()` and pass it in. When a lazily
created shared instance is truly needed, use a module-level value or
`functools.cache` on a zero-argument function.

```python
import functools
import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    debug: bool


@functools.cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.environ["DATABASE_URL"],
        debug=os.environ.get("DEBUG") == "1",
    )


def main() -> None:
    settings = get_settings()  # read once here, then pass it down
    run_server(settings)
```

**Avoid:** `__new__` overrides that return a cached instance, singleton metaclasses,
the Borg shared-state trick, and `get_instance()` classmethods. They all hide a
global and force tests to reset private state.

**Gotcha:** `functools.cache` keeps its own data consistent across threads, but two
threads calling at the same moment can both run the function. If construction has
side effects (opening a connection pool), build it in `main()` or guard it with a
lock. In tests, reset it with `get_settings.cache_clear()`.

## Structural

### Adapter

**Idiomatic form:** a small class that satisfies your `Protocol` by delegating to the
object you do not own.

```python
from typing import Protocol

from slack_sdk import WebClient


class Notifier(Protocol):
    def notify(self, user_id: str, message: str) -> None: ...


class SlackNotifier:
    """Adapts slack_sdk's WebClient to our Notifier protocol."""

    def __init__(self, client: WebClient) -> None:
        self._client = client

    def notify(self, user_id: str, message: str) -> None:
        self._client.chat_postMessage(channel=user_id, text=message)
```

**Avoid:** subclassing the vendor class to bolt your method on. That couples you to
every vendor method and every vendor release.

**Gotcha:** `SlackNotifier` does not inherit from `Notifier`; the protocol matches
structurally. Inherit explicitly only if you want the checker to flag a missing
method at the class definition instead of at the call site.

### Bridge

**Idiomatic form:** an attribute typed as a `Protocol`. Two dimensions that would
multiply into N×M subclasses become one class plus a pluggable collaborator.

```python
from typing import Protocol


class Renderer(Protocol):
    def heading(self, text: str) -> str: ...
    def paragraph(self, text: str) -> str: ...


class Invoice:
    def __init__(self, renderer: Renderer) -> None:
        self.renderer = renderer

    def render(self, number: str, body: str) -> str:
        title = self.renderer.heading(f"Invoice {number}")
        return title + self.renderer.paragraph(body)


html_invoice = Invoice(HtmlRenderer())
pdf_invoice = Invoice(PdfRenderer())
```

**Avoid:** `HtmlInvoice`, `PdfInvoice`, `HtmlReceipt`, `PdfReceipt`. Every new
document or format adds a row or column of subclasses.

### Composite

**Idiomatic form:** a recursive dataclass or a union of dataclasses, with one function
that handles a leaf and a group alike.

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class File:
    name: str
    size: int


@dataclass(slots=True)
class Folder:
    name: str
    children: list["File | Folder"] = field(default_factory=list)


def total_size(node: File | Folder) -> int:
    match node:
        case File(size=size):
            return size
        case Folder(children=children):
            return sum(total_size(child) for child in children)
```

**Avoid:** an abstract `Component` base with `add()` and `remove()` that leaves must
implement by raising.

**Gotcha:** recursion depth. A tree deeper than about 1000 levels hits
`RecursionError`; walk it with an explicit stack if the input is untrusted.

### Decorator

**Idiomatic form:** for a function, a `@` decorator built with `functools.wraps`. For
an object at runtime, a class with the same `Protocol` that delegates (see
[Proxy](#proxy); the shape is identical, the intent differs).

```python
import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def retry(
    attempts: int, delay_s: float = 0.5
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorate(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, attempts):
                try:
                    return fn(*args, **kwargs)
                except ConnectionError:
                    time.sleep(delay_s * attempt)
            return fn(*args, **kwargs)  # last try: let the error propagate

        return wrapper

    return decorate
```

**Avoid:** a `Component` / `ConcreteDecorator` class hierarchy for behavior a function
wrapper adds in a dozen lines.

**Gotcha:** without `functools.wraps` the wrapper loses the wrapped function's name,
docstring and `__wrapped__`, which breaks logging, `inspect.signature` and debuggers.
On 3.12+ the `ParamSpec`/`TypeVar` lines can become `def retry[**P, R](...)`.

### Facade

**Idiomatic form:** a class or module with a few intention-named methods that hide the
subsystem. Keep the subsystem in `_private` modules and export only the facade.

```python
# billing/__init__.py exports only this; _gateway, _tax and _invoices stay private.
class Billing:
    """The one entry point the rest of the app uses for payments."""

    def __init__(self, gateway: StripeGateway, invoices: InvoiceStore) -> None:
        self._gateway = gateway
        self._invoices = invoices

    def charge_order(self, order_id: str, amount_cents: int, country: str) -> str:
        total = amount_cents + tax_for(amount_cents, country)
        charge_id = self._gateway.charge(order_id, total)
        self._invoices.record(order_id, charge_id, total)
        return charge_id
```

**Avoid:** a facade that also re-exports every subsystem type, so callers reach
through it anyway.

### Flyweight

**Idiomatic form:** `sys.intern` for repeated strings, a cached constructor for
repeated immutable objects, and `slots=True` to shrink the instances that remain.

```python
import functools
import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Style:
    font: str
    size: int
    bold: bool


@functools.lru_cache(maxsize=1024)
def style(font: str, size: int, bold: bool) -> Style:
    return Style(font, size, bold)  # one shared instance per distinct key


def parse_log_line(line: str) -> tuple[str, str]:
    level, message = line.split(" ", 1)
    return sys.intern(level), message  # millions of lines, a handful of levels
```

**Avoid:** a `FlyweightFactory` class with a hand-written dict and lock.

**Gotcha:** measure with `tracemalloc` first; `slots=True` alone often gets most of
the saving. The shared objects must be immutable, and an unbounded `functools.cache`
over an unbounded key space is a memory leak, hence `lru_cache(maxsize=...)`.

### Proxy

**Idiomatic form:** a class with the same `Protocol` that adds access control,
laziness or caching before delegating. For lazy acquire-and-release, a context
manager; for a lazily computed attribute, `functools.cached_property`.

```python
from typing import Protocol


class Reports(Protocol):
    def fetch(self, report_id: str) -> bytes: ...


class AuthorizedReports:
    def __init__(self, inner: Reports, user: User) -> None:
        self._inner = inner
        self._user = user

    def fetch(self, report_id: str) -> bytes:
        if not self._user.can_read(report_id):
            raise PermissionError(f"{self._user.id} cannot read {report_id}")
        return self._inner.fetch(report_id)
```

**Avoid:** `__getattr__` forwarding on a public API. Type checkers lose the surface,
and a typo becomes a runtime `AttributeError` from the wrapped object. It is fine for
debugging or recording proxies.

**Gotcha:** `__getattr__` never sees dunder lookups. `len(proxy)`, `iter(proxy)` and
`proxy[0]` look up `__len__`, `__iter__` and `__getitem__` on the type, so a
forwarding proxy must define them explicitly.

## Behavioral

### Chain of Responsibility

**Idiomatic form:** a list of handler functions tried in order, where the first
non-`None` answer wins. For request pipelines, use your framework's middleware.

```python
from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Expense:
    amount: int
    category: str


Approver = Callable[[Expense], str | None]  # approver's name, or None to pass on


def team_lead(e: Expense) -> str | None:
    return "team lead" if e.amount <= 500 else None


def finance(e: Expense) -> str | None:
    return "finance" if e.category != "travel" and e.amount <= 5_000 else None


def approver_for(expense: Expense, chain: Sequence[Approver]) -> str:
    for approve in chain:
        if (who := approve(expense)) is not None:
            return who
    return "cfo"
```

**Avoid:** linked `Handler` objects with `set_next()`. A list is the chain, and its
order is visible in one place.

### Command

**Idiomatic form:** a callable (a closure or `functools.partial`) when the command only
needs to run later. A frozen dataclass with `do` and `undo` when it must be undone,
logged or serialized.

```python
import functools
import queue
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

# Deferred work only: a callable is the whole pattern.
jobs: queue.Queue[Callable[[], None]] = queue.Queue()
jobs.put(functools.partial(send_email, to="ana@example.com", template="welcome"))


# Undo needs data, so the command becomes a value.
class Command(Protocol):
    def do(self) -> None: ...
    def undo(self) -> None: ...


@dataclass(frozen=True, slots=True)
class Rename:
    doc: Document
    old: str
    new: str

    def do(self) -> None:
        self.doc.title = self.new

    def undo(self) -> None:
        self.doc.title = self.old
```

**Avoid:** a `Command` ABC plus an `Invoker` class for work that is just "call this
later".

**Gotcha:** a lambda in a loop captures the variable, not its value.
`[lambda: send(u) for u in users]` sends to the last user every time. Use
`functools.partial(send, u)`.

### Interpreter

**Idiomatic form:** a small tree of frozen dataclasses and one `match` that evaluates
it. First check whether a config format, `ast.literal_eval`, or an existing rules or
expression library already does the job.

```python
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Eq:
    field: str
    value: object


@dataclass(frozen=True, slots=True)
class All:
    rules: tuple["Rule", ...]


@dataclass(frozen=True, slots=True)
class Not:
    rule: "Rule"


Rule = Eq | All | Not


def matches(rule: Rule, user: Mapping[str, object]) -> bool:
    match rule:
        case Eq(field, value):
            return user.get(field) == value
        case All(rules):
            return all(matches(r, user) for r in rules)
        case Not(inner):
            return not matches(inner, user)
```

**Avoid:** an `interpret(context)` method on a class per grammar rule, and never
`eval()` on input you did not write.

### Iterator

**Idiomatic form:** a generator function, or `__iter__` written as a generator.

```python
from collections.abc import Iterator
from typing import Any


def paginate(client: ApiClient, path: str) -> Iterator[dict[str, Any]]:
    """Yields every item across all pages, fetching a page only when needed."""
    cursor: str | None = None
    while True:
        page = client.get(path, cursor=cursor)
        yield from page["items"]
        cursor = page.get("next")
        if cursor is None:
            return
```

**Avoid:** a class with `has_next()` and `next()` methods, or a hand-written
`__next__` that tracks an index.

**Gotcha:** a generator object can be consumed only once. A class whose `__iter__`
is a generator can be looped over many times. A generator abandoned halfway runs its
`finally` block only when it is closed or garbage-collected, so wrap one that holds a
file or connection in `contextlib.closing`.

### Mediator

**Idiomatic form:** one coordinating object that components report to, instead of
calling each other. Often it is just the service function or form controller that
already exists.

```python
class CheckoutForm:
    """Coordinates the widgets so none of them references another."""

    def __init__(self, country: Select, shipping: Select, total: Label) -> None:
        self.country, self.shipping, self.total = country, shipping, total
        country.on_change(self.country_changed)
        shipping.on_change(self.shipping_changed)

    def country_changed(self, value: str) -> None:
        self.shipping.set_options(shipping_methods_for(value))
        self.recalculate()

    def shipping_changed(self, _value: str) -> None:
        self.recalculate()

    def recalculate(self) -> None:
        self.total.set_text(format_total(self.country.value, self.shipping.value))
```

**Avoid:** a generic `Mediator.notify(sender, event: str)` with string dispatch. It
hides who depends on whom, and the mediator grows into a god object.

### Memento

**Idiomatic form:** keep state in a frozen dataclass; the snapshot is simply the
previous value. A bounded `deque` holds the history.

```python
from collections import deque
from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class EditorState:
    text: str
    cursor: int


class Editor:
    def __init__(self) -> None:
        self.state = EditorState(text="", cursor=0)
        self._history: deque[EditorState] = deque(maxlen=100)

    def insert(self, chars: str) -> None:
        self._history.append(self.state)
        s = self.state
        text = s.text[: s.cursor] + chars + s.text[s.cursor :]
        self.state = replace(s, text=text, cursor=s.cursor + len(chars))

    def undo(self) -> None:
        if self._history:
            self.state = self._history.pop()
```

**Avoid:** separate Originator, Caretaker and Memento classes with tricks to keep the
snapshot's fields private.

**Gotcha:** `frozen=True` stops reassignment, not mutation. A `list` or `dict` inside
a snapshot can still change under you, so snapshots must hold immutable values.

### Observer

**Idiomatic form:** a list of callbacks, where `subscribe` returns the function that
unsubscribes.

```python
from collections.abc import Callable

Listener = Callable[[Order], None]


class OrderEvents:
    def __init__(self) -> None:
        self._listeners: list[Listener] = []

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def publish(self, order: Order) -> None:
        for listener in list(self._listeners):  # copy: a listener may unsubscribe
            listener(order)
```

**Avoid:** `Subject` and `Observer` ABCs with `attach`, `detach` and `update`. A
callable is already an observer.

**Gotcha:** the list holds strong references, so a subscribed bound method keeps its
object alive until someone unsubscribes. To let listeners die with their owners, store
`weakref.WeakMethod(obj.method)`. A `weakref.WeakSet` of bound methods does not work:
it is empty immediately, because `obj.method` creates a new bound-method object on
every access. Decide too whether one listener raising should stop the rest.

### State

**Idiomatic form:** an `Enum` plus a transition table when states only gate what is
allowed. Use state objects only when each state carries substantial behavior of its
own.

```python
from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PENDING: frozenset({OrderStatus.PAID, OrderStatus.CANCELLED}),
    OrderStatus.PAID: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


def transition(current: OrderStatus, target: OrderStatus) -> OrderStatus:
    if target not in TRANSITIONS[current]:
        raise ValueError(f"cannot move an order from {current} to {target}")
    return target
```

**Avoid:** a class per state where most methods raise (`ShippedState.pay()`), when
the table says the same thing in a dozen lines and can be tested exhaustively.

### Strategy

**Idiomatic form:** pass a function. When the strategy is picked by name, use a `dict`
of functions. The stdlib does this everywhere: `sorted(key=...)`,
`json.dumps(default=...)`.

```python
from collections.abc import Callable
from decimal import Decimal

Pricer = Callable[[Decimal], Decimal]


def standard(subtotal: Decimal) -> Decimal:
    return subtotal


def member(subtotal: Decimal) -> Decimal:
    return subtotal * Decimal("0.9")


PRICERS: dict[str, Pricer] = {"standard": standard, "member": member}


def checkout_total(subtotal: Decimal, tier: str) -> Decimal:
    try:
        pricer = PRICERS[tier]
    except KeyError:
        raise ValueError(f"unknown pricing tier: {tier!r}") from None
    return pricer(subtotal)
```

**Avoid:** a `PricingStrategy` ABC, a `StandardPricingStrategy` subclass, and a
`Context` class to hold it. A stateless class with one method is a function. If a
strategy needs configuration, use a closure, `functools.partial`, or a small class
with `__call__`. If it needs several methods (say `charge` and `refund`), declare a
`Protocol` with those methods.

**Gotcha:** a bare `PRICERS[tier]` lets an unknown key escape as a `KeyError` far from
the config that caused it. Translate it into an error that names the bad value.

### Template Method

**Idiomatic form:** a function that takes the varying steps as arguments.

```python
from collections.abc import Callable, Iterable


def run_import(
    read: Callable[[], Iterable[dict[str, str]]],
    transform: Callable[[dict[str, str]], Row],
    write: Callable[[list[Row]], None],
    batch_size: int = 500,
) -> int:
    batch: list[Row] = []
    count = 0
    for record in read():
        batch.append(transform(record))
        if len(batch) == batch_size:
            write(batch)
            count, batch = count + len(batch), []
    if batch:
        write(batch)
        count += len(batch)
    return count
```

**Avoid:** an `AbstractImporter` with abstract `read`, `transform` and `write` and a
`run` that subclasses must not override, especially stacked several levels deep.
Framework hooks are the fair exception: `unittest.TestCase.setUp` and
`socketserver.BaseRequestHandler.handle` are the stdlib's own template methods, and
subclassing them is the expected use.

### Visitor

**Idiomatic form:** `match` over a closed union with `assert_never` when you own all
the types. `functools.singledispatch` when other modules add types. The stdlib's one
real Visitor, `ast.NodeVisitor`, is the right tool for walking Python syntax trees.

```python
import math
from dataclasses import dataclass
from typing import assert_never


@dataclass(frozen=True, slots=True)
class Circle:
    radius: float


@dataclass(frozen=True, slots=True)
class Rect:
    width: float
    height: float


Shape = Circle | Rect


def area(shape: Shape) -> float:
    match shape:
        case Circle(radius=r):
            return math.pi * r * r
        case Rect(width=w, height=h):
            return w * h
        case _:
            assert_never(shape)
```

**Avoid:** an `accept(visitor)` method on every node and a `ShapeVisitor` interface
with `visit_circle`, `visit_rect`, when you own every type and one `match` per
operation does the job.

**Gotcha:** `assert_never` is what makes this safe. Add a `Triangle` to `Shape` and
mypy or pyright fails every `match` that does not handle it. Without it, the new
type falls through silently.

## Java in Python: smells to catch in review

- **`get_name()` / `set_name()` pairs.** Use a plain attribute; switch to `@property`
  later without changing a single caller.
- **An ABC for every interface**, often with one implementation. Declare a `Protocol`
  at the consumer when something needs it, or nothing at all.
- **A class with `__init__` and one public method** (`EmailSender(cfg).send(msg)`).
  That is a function, possibly with `functools.partial`.
- **Singleton machinery:** `__new__` overrides, metaclasses, `get_instance()`. A
  module-level value or an argument does the job.
- **Factory classes** (`ParserFactory.create(kind)`). Use a `dict` of callables or a
  `@classmethod` constructor.
- **Classes of only `@staticmethod`s** used as namespaces. The module is the
  namespace.
- **`Manager`, `Impl`, `Abstract...Base` and `I`-prefixed names.** Name by domain role.
- **Inheritance for code reuse:** deep base-class chains and stacks of mixins, where
  understanding one method means reading five classes.
- **`isinstance` chains** in callers that pick behavior by type. Use a method, a
  `match` with `assert_never`, or `singledispatch`.
- **Interfaces added "for dependency injection"** next to their only implementation.
  Pass the object; Python needs no interface to substitute a fake in a test.
