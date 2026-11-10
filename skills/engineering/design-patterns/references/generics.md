# Generics

Type parameters are not a design pattern. They are a language tool, and like a
pattern they cost every reader something, so they need a force too. This file is
language-neutral: when type parameters earn their place, when they don't, what they
cost, and how they change the catalog. For the code, see
[Generics in Go](go.md#generics-in-go) and
[Generics in TypeScript](typescript.md#generics-in-typescript).

## Contents

- [The force](#the-force)
- [When they pay](#when-they-pay)
- [When they don't](#when-they-dont)
- [What they cost](#what-they-cost)
- [Generics and the catalog](#generics-and-the-catalog)
- [Review checklist](#review-checklist)

## The force

The same code, written or about to be written for a second type, where the only
difference is the type, and where callers need the type back: without a type
parameter they would receive `any`, `interface{}` or `unknown` and cast it.

Both halves matter. Code that is duplicated but only ever calls methods on its
argument needs an interface, not a type parameter. Code that is generic in shape but
used with one type needs nothing yet.

The Go team's rule of thumb fits every language: write code, don't design types.
Start with the concrete function. Add the type parameter when the second type
arrives, as with any other abstraction.

## When they pay

- **Functions over collections that assume nothing about the elements.** Filter,
  chunk, group, deduplicate, take the first. Check the standard library first; most
  of these already exist.
- **General-purpose data structures.** Sets, trees, caches, queues, ring buffers.
  Without type parameters they hold `any` and every read is a cast.
- **Keeping the caller's type.** A helper that takes a named type should return that
  named type, not its underlying form.
- **Keyed families of types.** An event bus where the event name decides the payload
  type, a registry where the key decides the handler, a typed context key.
- **Relating inputs to each other.** "`initial` must be one of `states`", "the
  handler's argument matches the event it is registered for".

## When they don't

- **The code only calls methods on the value.** Take the interface or structural
  type. A type parameter constrained by an interface, and used only to call that
  interface's methods, adds syntax and nothing else.
- **Each type needs different code.** That is polymorphism: an interface with several
  implementations, or a closed union with a `switch`. A generic function that
  switches on the type of its parameter is several functions in disguise.
- **One type is in use.** Write it for that type.
- **The constraint alone would accept the same arguments.** Then the type parameter
  relates nothing; replace it with the constraint. In TypeScript that is almost every
  type parameter that appears once, because types are structural and arrays are
  covariant. In Go it is not: `func Len[E any](s []E) int` needs `E` even though it
  appears once, since a `[]int` is not a `[]any`.
- **The type appears only in the result and nothing checks it at runtime.** The
  caller chooses the type: a cast with better manners. TypeScript's `getJson<T>()`
  is the classic case, because types are erased. Take a parser, a schema or a
  constructor, a value that exists at runtime and can be wrong loudly. A result-only
  type parameter is fine when the runtime does check it, as Go's
  `errors.AsType[E](err)` does with a type assertion.
- **Generic frameworks.** `Result<T>`, `Option<T>` and `Either` in a language whose
  convention is different, generic error-handling helpers, generic DSLs, a
  `Repository<T>` base with the same CRUD methods for every entity. Each one makes
  every caller translate between two conventions.
- **Type-level programs.** Constraints and conditional types that compute other
  types. Readers cannot step through them, and their error messages are the hardest
  to read in the language.

## What they cost

- **Reading.** Every type parameter is one more name to hold in mind, and
  constraints are a second, smaller language inside the first.
- **Error messages.** Mistakes surface as constraint failures, often far from the
  call that caused them.
- **API stability.** An exported generic signature is hard to change. Adding a type
  parameter, or reordering them, breaks every caller that wrote the type arguments
  out.
- **Performance, either way.** Generics are not automatically faster than an
  interface. Go shares one compiled body across types with the same GC shape and
  dispatches method calls through a dictionary; TypeScript erases types entirely.
  Measure before choosing generics for speed.
- **Documentation.** An exported generic API needs more of it than a concrete one:
  say what each type parameter is for, and give a runnable example.

## Generics and the catalog

Type parameters make several patterns smaller and safer. They do not change when the
pattern is needed.

| Pattern | What a type parameter adds |
| --- | --- |
| Observer | A typed event map: subscribers get the right payload without casts |
| Iterator | `iter.Seq[V]`, `Iterable<T>`, `AsyncGenerator<T>` carry the element type |
| Composite | A `Tree[T]` holds any payload with one walk function |
| Proxy, Decorator | A `Cache[K, V]` or a memoizer wraps any function's result type |
| Flyweight | Interning works on any comparable value (Go's `unique.Make[T]`) |
| Memento | A `History[T]` of snapshots works for any immutable state |
| Strategy | A function type such as `func(a, b T) int` passes an algorithm over any `T` |
| Factory Method | A constructor parameter (`new () => T`, a factory function) instead of reflection |

The anti-patterns carry over too. A generic `Repository<T>` is speculative
generality with type parameters, and a generic `Visitor<R>` over a class hierarchy is
still the heavier choice next to a union with an exhaustive `switch`.

## Review checklist

1. **Can a type parameter be deleted** and replaced by its constraint, with callers
   still compiling? Delete it.
2. **Does it appear only in the result,** with nothing at runtime checking it? It is
   a cast; take a value that checks.
3. **Does the body inspect the type** (type switch, `typeof`, reflection)? Split the
   function or use an interface.
4. **Is the constraint stronger than the body needs?** Loosen it; a function
   parameter (a comparator, a key function) is often better than a method
   constraint.
5. **Do callers have to spell the type arguments?** Reorder the parameters so they
   are inferred, or reconsider the design.
6. **Is only one type ever used?** Make it concrete until a second one arrives.
