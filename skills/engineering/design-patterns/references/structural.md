# Structural patterns

Patterns about how types and objects fit together. This file is language-neutral:
for each pattern it gives the intent, the force that earns it, the shape, the cost,
and its neighbors. For what the code looks like, read the same section in
[go.md](go.md), [python.md](python.md) or [typescript.md](typescript.md).

Four of these seven are the same shape, a wrapper, told apart only by intent. The
[wrapper family table](#the-wrapper-family) at the end is the quickest way to name
one correctly.

## Contents

- [Adapter](#adapter)
- [Bridge](#bridge)
- [Composite](#composite)
- [Decorator](#decorator)
- [Facade](#facade)
- [Flyweight](#flyweight)
- [Proxy](#proxy)
- [The wrapper family](#the-wrapper-family)

## Adapter

**Intent.** Convert the interface of a type into the one its clients expect.

**The force.**

- A type you do not own (a vendor SDK, a legacy module) does the right thing with
  the wrong shape.
- You want a third-party API behind your own interface so it can be swapped or
  faked. Domain-driven design calls this an anti-corruption layer.

**Shape.** A wrapper that implements the target interface by calling the adaptee.
In languages with function types, an adapter can be a single function type with a
method, like Go's `http.HandlerFunc`.

**Cost and when not to use it.**

- An adapter that leaks the adaptee's types (its errors, its structs) defeats the
  purpose; callers are coupled to the vendor again.
- Renaming methods is the easy part. The real work is translating semantics: error
  models, pagination, retries, sync versus async, units. An adapter that skips this
  is a thin coat of paint.
- If you own both sides, change one of them instead.

**Class versus object adapter.** GoF describes both. The class adapter relies on
multiple inheritance and is a C++ artifact; use composition.

**Neighbors.** Facade (defines a new, simpler interface; Adapter conforms to an
existing one); Decorator and Proxy (keep the interface; Adapter changes it); Bridge
(designed up front; Adapter is retrofitted).

## Bridge

**Intent.** Decouple an abstraction from its implementation so the two can vary
independently.

**The force.** Two independent dimensions that would otherwise multiply into N × M
types. Notification kinds (alert, digest, receipt) × channels (email, SMS, push).
Shapes × renderers. Remote controls × devices.

**Shape.** The abstraction holds a reference to an implementor interface. Each side
has its own set of implementations, and any pairing works.

**Cost and when not to use it.**

- Premature when only one dimension varies.
- In composition-first code, Bridge is simply "a type with an interface-typed
  field". It is everywhere and rarely worth naming. Go's `database/sql` is a bridge:
  `sql.DB` is the abstraction, each `driver.Driver` an implementation.

**Neighbors.** Strategy (same structure; Strategy swaps an algorithm, Bridge splits a
whole hierarchy in two); Adapter (retrofitted, where Bridge is designed in); Abstract
Factory (can create a matching implementor).

## Composite

**Intent.** Build tree structures and treat single items and groups the same way.

**The force.** Part-whole hierarchies where clients should not care which they hold:
a file's size and a directory's size; a product's price and a bundle's price; a
widget and a panel of widgets; a user and a group in a permission check; nodes of an
expression tree.

**Shape.** A component interface with the shared operation. Leaves implement it
directly. A composite holds children and implements it by combining their results.

**The design choice: transparency or safety.** Put child management (`add`,
`remove`) on the shared interface, and leaves must reject it: uniform for clients,
but a Liskov smell. Put it on the composite only, and clients must know which they
hold for construction, but nothing lies. Prefer safety: building a tree and
operating on it are usually done by different code anyway.

**Cost and when not to use it.**

- Cycles (a group containing itself), deep recursion, and repeated recomputation of
  aggregates (cache sizes and totals if the tree is large).
- A flat list is not a tree. If there is no nesting, a slice and a loop will do.

**Neighbors.** Iterator (walk the tree); Visitor (add operations over it);
Interpreter (its AST is a Composite); Decorator (structurally a Composite with one
child, but adds behavior rather than aggregating).

## Decorator

**Intent.** Add behavior to an object without changing it, keeping its interface.

**The force.** Cross-cutting behavior that should compose in varying combinations:
logging, metrics, tracing, retries, caching, authentication, compression, rate
limiting. Subclassing for each combination would explode.

**Shape.** A wrapper that implements the same interface, holds the wrapped object,
delegates to it, and adds behavior before or after. In function-first code this is
middleware: a function that takes a handler and returns a handler.

**Cost.**

- **Order matters and is invisible at the call site.** Retry inside the timeout, or
  timeout inside each retry? Auth before cache, or cache before auth? The second of
  each pair is usually a bug. Document or centralize the order.
- **Identity breaks.** The wrapped object is not equal to the original.
- **Lost capabilities.** If the wrapped object also implemented other interfaces
  (flushing, hijacking, seeking), a plain wrapper hides them.
- **Wide interfaces make every decorator long,** since each must forward every
  method.

**Not the same as language decorators.** Python's `@decorator` and TypeScript's
decorators are syntax that wraps a function or class *when it is defined*. They can
implement the Decorator pattern for functions, but they apply to every use of the
definition, not to one object at runtime.

**Neighbors.** Proxy (same shape, controls access instead of adding behavior);
Adapter (changes the interface); Chain of Responsibility (a middleware chain where
any link may stop); Strategy (GoF: "a decorator lets you change the skin of an
object; a strategy lets you change the guts").

## Facade

**Intent.** Give a subsystem one simple entry point.

**The force.** Callers repeating the same multi-step dance with a subsystem
(configure the client, authenticate, retry, paginate, map errors), or a subsystem
whose internals should be free to change.

**Shape.** A module or type exposing a few high-level operations that orchestrate the
subsystem internally. A well-designed package *is* a facade: a small public API over
a larger private implementation. This is Ousterhout's deep module.

**Cost and when not to use it.**

- **God-object drift.** Every new need lands on the facade until it is the
  subsystem's whole API again, with an extra layer.
- **Shallow facades.** Methods that forward one-to-one to a single call below add a
  layer and hide nothing.
- Callers that genuinely need the low-level API should be able to reach it; a facade
  simplifies the common path, it does not have to be a wall.

**Neighbors.** Adapter (conforms to an existing interface; Facade invents a simpler
one); Mediator (Facade is one-way, clients to subsystem; Mediator coordinates peers
in both directions); Abstract Factory (can hide the subsystem's construction).

## Flyweight

**Intent.** Share fine-grained objects so that very large numbers of them fit in
memory.

**The key split.** *Intrinsic* state is shared and immutable (a glyph's shape, a
tree species' mesh). *Extrinsic* state varies per use and is passed in (the glyph's
position, the tree's coordinates).

**The force.** Measured memory pressure from many duplicates: characters in a text
editor, tiles and sprites in a game, repeated strings in a large dataset, map
markers sharing a few icons.

**Shape.** A factory or cache that returns a shared immutable instance per key.
Callers pass extrinsic state into its methods.

**Cost and when not to use it.**

- **Shared objects must be immutable.** A mutable flyweight is a shared-state bug
  waiting to happen.
- **The cache grows.** It needs a bound, eviction or weak references.
- Without a memory profile showing the duplicates, it is complexity for nothing.

**Already built in.** String interning and small-integer caches are flyweights your
runtime provides. Use those before writing one.

**Neighbors.** Singleton (one instance, versus one per key); Composite (leaves are
often flyweights); Prototype (copies, where Flyweight shares).

## Proxy

**Intent.** Stand in for another object, with the same interface, to control access
to it.

**The kinds.**

- **Virtual:** create the real object lazily, on first use.
- **Remote:** a local stub for an object elsewhere. Generated RPC client stubs
  (gRPC, for example) are remote proxies.
- **Protection:** check permissions before forwarding.
- **Caching:** return stored results for repeated calls.
- **Smart reference:** count references, log access, lock.

**The force.** The real object is expensive, remote or needs guarding, and callers
should not change.

**Shape.** Same interface as the real subject. Holds (or lazily creates) the real
object, forwards calls, and adds the control logic.

**Cost.**

- **Remote proxies hide latency and failure.** A method call that is really a
  network round trip still needs timeouts, retries and error handling. Do not let
  the proxy pretend otherwise.
- **Lazy creation needs to be thread-safe.**
- Dynamic proxies built on language features (JavaScript `Proxy`, Python
  `__getattr__`) trade away type checking and some performance.

**Neighbors.** Decorator (same shape, adds behavior instead of controlling access);
Adapter (changes the interface); Facade (simplifies, rather than stands in).

## The wrapper family

All four wrap something. Name them by what they do to the interface and why.

| Pattern | Interface seen by the caller | Why it exists |
| --- | --- | --- |
| Adapter | Different from the wrapped object's | Make an existing type fit an expected interface |
| Decorator | Same as the wrapped object's | Add behavior (logging, retries, caching) |
| Proxy | Same as the wrapped object's | Control access (lazy, remote, guarded) |
| Facade | New and smaller, over several objects | Simplify a subsystem |

Caching sits on the border between Decorator and Proxy. Call it whichever matches
the intent in context; the code is the same.
