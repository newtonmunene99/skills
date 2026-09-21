# Creational patterns

Patterns about how objects get made. This file is language-neutral: for each
pattern it gives the intent, the force that earns it, the shape, the cost, and its
neighbors. For what the code looks like, read the same section in [go.md](go.md),
[python.md](python.md) or [typescript.md](typescript.md).

Half of this catalog has been absorbed by one modern habit: **build dependencies in
one place and pass them in.** Read [Dependency injection](#dependency-injection)
before reaching for Singleton or Abstract Factory.

## Contents

- [Factory Method](#factory-method)
- [Abstract Factory](#abstract-factory)
- [Builder](#builder)
- [Prototype](#prototype)
- [Singleton](#singleton)
- [Beyond the catalog](#beyond-the-catalog)
  - [Dependency injection](#dependency-injection)
  - [Object pool](#object-pool)

## Factory Method

**Intent.** Let a function decide which concrete type to create, so callers depend
only on the interface they get back.

**Three things share the name.** Say which one you mean.

- **GoF Factory Method.** A creator class declares an overridable method that
  subclasses override to create the product. Rare outside frameworks.
- **Simple factory.** A function that picks a concrete type from its input:
  `open("s3://bucket/key")` returns an S3-backed store. The common modern form.
- **Named constructor** (Joshua Bloch's "static factory method"). A constructor
  with a descriptive name: `Duration.ofSeconds(5)`, `datetime.fromisoformat(s)`,
  `NewClientFromEnv()`. Justified by clarity alone.

**The force.**

- The concrete type depends on runtime input (config, URL scheme, file extension),
  and every caller would otherwise carry the same `switch`.
- Construction needs validation or setup that callers should not repeat.
- There are several ways to build the same type and each deserves a name.

**Shape.** A function returning an interface, often backed by a map from key to
constructor: `{"s3": newS3Store, "gs": newGCSStore, "file": newLocalStore}`.

**Cost and when not to use it.**

- One concrete type: call its constructor.
- Self-registering plugin registries (a package registers itself on import, like
  Go's `database/sql` drivers) add hidden global state and import side effects.
  Worth it for true plugins; not for application code where `main` can just list
  the options.

**Neighbors.** Abstract Factory (a family of products, not one); Prototype (clone
instead of construct); Strategy (the product is often a strategy).

## Abstract Factory

**Intent.** Create families of related objects that must be used together, without
naming their concrete types.

**The force.** Several products that must match each other, where mixing them is a
bug. A cloud provider's blob store, queue and secret manager; a UI theme's button,
checkbox and dialog; a test double set that replaces all of them at once.

**Shape.** One interface or record with a constructor per product, one
implementation per family, chosen once at startup.

**Cost and when not to use it.**

- Every new product means editing every family.
- In most application code this is a composition root in disguise. Choosing the
  AWS or GCP implementations in `main` and passing them in gets the same guarantee
  with no extra types. Reach for Abstract Factory when objects of the family are
  created *repeatedly at runtime*, not once at startup.

**Neighbors.** Factory Method (one product); Facade (often returned by it); Bridge
(each family is one side of a bridge).

## Builder

**Intent.** Construct a complex object step by step.

**Two different patterns share the name.**

- **GoF Builder.** One construction process produces *different representations*: a
  document parser drives a builder interface, and swapping the builder yields RTF,
  HTML or plain text. A director owns the steps; the builder owns the output.
- **Bloch's Builder** (*Effective Java*). A fluent way to supply many optional
  parameters to an immutable object: `Request.builder().url(u).timeout(t).build()`.
  This is what most people mean today, and language features usually replace it.

**The force.**

- Many optional parameters with defaults, where positional constructors become
  unreadable.
- Invariants that span fields and must be checked once, when construction ends.
- An immutable result.
- Assembly where the steps *are* the API: query builders, HTTP request builders,
  document and AST construction.

**Shape.** Methods that set or add parts, then a `build()` that validates and returns
the product.

**Cost and when not to use it.**

- Keyword arguments (Python), options objects (TypeScript) and functional options
  (Go) cover the optional-parameters case with less code.
- A builder lets invalid combinations exist until `build()`, so errors surface late
  and far from the mistake.
- A mutable builder shared across threads or goroutines is a race.

**Neighbors.** Abstract Factory (returns a product immediately; Builder assembles
over several calls); Composite (trees are often assembled by a builder).

## Prototype

**Intent.** Create new objects by copying a configured instance.

**The force.**

- Many variants that differ from a base in a few fields: a default request with
  headers and retries set, copied and tweaked per call.
- Construction is expensive (parsing, compilation, network lookups) and a copy is
  cheap.
- Code must copy an object whose concrete type it does not know, through an
  interface.

**Shape.** A `clone()` on the interface, or a plain value copy followed by
overrides.

**Cost and when not to use it.**

- **Shallow versus deep copy is the whole pattern.** Nested mutable data (lists,
  maps, pointers) shared between copies is the classic bug: change one, the other
  changes too.
- Identity, cycles and live resources (open files, connections, locks) cannot be
  meaningfully cloned.
- If values are immutable, copy-with-changes is free and "Prototype" is just how the
  language works.

**Neighbors.** Memento (copy to restore later); Flyweight (share instead of copy);
Factory Method (construct instead of copy).

## Singleton

**Intent.** Ensure a type has exactly one instance and provide global access to it.

**Two ideas are bundled here.** One instance, and global access. The first is
sometimes legitimate. The second is the problem.

**The force.** A resource that must be unique per process: a connection pool, a
metrics registry, a hardware device, a process-wide cache.

**Cost.**

- **A hidden dependency.** A function's signature no longer says what it uses.
- **Shared mutable state between tests,** so tests pass or fail depending on order.
- **Initialization-order bugs,** and races on lazy initialization.
- **Hard to replace** in tests without monkey-patching or reset hooks.
- **"One" is per process, per module copy.** Two processes, two class loaders or two
  copies of a bundled package each get their own "single" instance.

**The preferred form.** Build the object once at the composition root and pass it to
whoever needs it. Uniqueness becomes a decision `main` makes, not a property the
type enforces, and tests can build their own.

**When a global is acceptable.** State that is immutable after initialization:
compiled regular expressions, lookup tables, parsed embedded templates. Standard
library defaults (a default HTTP client, the root logger) are convenient globals, but
anything with I/O or configuration is better injected.

**Neighbors.** Facade and Abstract Factory objects are often singletons; Flyweight
factories hold one shared cache.

## Beyond the catalog

### Dependency injection

Not a GoF pattern, but the modern replacement for much of this file.

**What it is.** Objects receive their dependencies (usually through the constructor)
instead of creating or looking them up. The whole object graph is built in one
place, the composition root, usually `main` or the app's startup.

**Why it matters here.** It makes Singleton unnecessary (build one, pass it), turns
Abstract Factory into a few lines in `main`, and gives every test a seam without
extra patterns.

**Manual wiring versus a container.** Plain constructor calls in `main` are the
clearest option until the graph is large, or needs lifecycle scopes (per-request
objects). Containers (Go's `wire` or `fx`, NestJS, InversifyJS) automate wiring and
cost you compile-time clarity: missing bindings become startup or runtime errors.

### Object pool

**Intent.** Reuse expensive objects instead of creating and destroying them.

**The force.** Measured cost of creation: database connections, TLS sessions,
large buffers on a hot path.

**Cost.** State leaking between uses when reset is incomplete; unclear ownership (who
returns the object, and when); pool sizing. Use the pool your driver or runtime
already provides before writing one.

**Gotcha.** Go's `sync.Pool` is a cache for reducing garbage-collector pressure, not a
resource pool: it may drop objects at any time. Never use it for connections.
