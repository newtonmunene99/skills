---
name: design-patterns
description: >-
  Applies SOLID principles and the classic design patterns in the idiomatic form
  for Go, Python and TypeScript, and pushes back when a pattern is not earned.
  Covers creational (Factory Method, Abstract Factory, Builder, Prototype,
  Singleton), structural (Adapter, Bridge, Composite, Decorator, Facade,
  Flyweight, Proxy) and behavioral patterns (Chain of Responsibility, Command,
  Interpreter, Iterator, Mediator, Memento, Observer, State, Strategy, Template
  Method, Visitor). Use when choosing a pattern for a design problem, asking
  which pattern fits, refactoring a growing switch or if/else chain, reviewing
  code for SOLID violations or over-engineering, deciding whether an
  abstraction is worth it, or writing a given pattern idiomatically in Go,
  Python or TypeScript rather than as a Java class diagram.
disable-model-invocation: false
compatibility: >-
  Needs no tooling. The language references target Go 1.23+, Python 3.11+ and
  TypeScript 5+; the catalog and the SOLID guidance apply to any language.
---

# Design Patterns

## Overview

> **A pattern is a named answer to a named problem. No problem, no pattern.**

The Gang of Four catalog (1994) was written for C++ and Smalltalk, and many of its
patterns exist to work around features those languages lacked: first-class
functions, closures, generators, structural typing, modules. Peter Norvig found 16
of the 23 had a qualitatively simpler form in a dynamic language. In Go, Python and
TypeScript the same holds. Strategy is a function parameter, Iterator is a `for`
loop over a generator, Singleton is a module-level value or, better, an argument.

So the catalog is a vocabulary, not a parts bin. This skill does three things with
it:

1. **Names the force first.** The force is the change or variation the code has to
   absorb, stated concretely: "a new payment provider every month", "the vendor SDK
   does not match our interface", "users need undo". A pattern without a force is
   cost with no benefit.
2. **Translates to the language.** The per-language reference, not the class
   diagram, decides what the code looks like.
3. **Says no when the force is missing.** Declining to add a pattern is a valid,
   often the best, answer. Say it plainly and show the simpler code.

SOLID gets the same treatment. Each principle is a smell detector for a specific
kind of change that will hurt. It is not a rubric to score code against, and a
finding that cannot name the change it would make painful is not a finding.

## Workflow

1. **Name the force.** One sentence: what varies, or what must change without
   rippling. It must exist today, in the code or the requirements in front of you.
   "We might need another database someday" is not a force. If there is none, the
   answer is the simplest code that works; say so and stop.
2. **Pick a candidate** from the selector below. When several fit, prefer the one
   that adds the fewest new types and the least indirection.
3. **Translate.** Read the language reference before writing code. Outside Java and
   C#, the textbook shape (abstract base class, interface per role, factory class) is
   almost never right.
4. **Check the cost.** Every pattern in the catalog references lists when not to use
   it. One implementation, one caller, and no test seam needed usually means the
   cost wins.
5. **Deliver.**
   - **Design question:** the force, the recommended pattern in its idiomatic form,
     a short code sketch, and what you rejected and why.
   - **Review:** findings named by principle or pattern, each with the concrete
     change that would hurt today, and the smallest fix. Where the design is fine,
     say so; do not invent design findings to fill a checklist. That restraint is
     about design only: real correctness bugs you notice on the way (money in
     floats, unescaped output, a denylist that should be an allowlist) still get
     reported, in a short list of their own after the design findings.
   - **Refactor request that presupposes a pattern** ("make this a Strategy"):
     check the force first. If it is missing, say so before doing the work, and offer
     the simpler alternative.
   - **Any refactor you deliver keeps behavior and signatures identical.** A latent
     bug you notice along the way (a silent default branch, a missing case) is a
     separate finding: name it, show the fix, and let the user opt in. Do not fold an
     error return or a new failure mode into a change that was asked to be a
     refactor.

## Problem to pattern selector

| The force | Pattern | Usually simpler in Go / Python / TS |
| --- | --- | --- |
| Many optional parameters, or objects that must never exist half-built | Builder | Functional options / keyword args + dataclass / options object |
| Caller should not know which concrete type it gets | Factory Method | A constructor function that returns an interface or protocol |
| A family of related objects that must match each other | Abstract Factory | A struct or record of constructor functions |
| Copying a configured object beats building one | Prototype | Value copy / `dataclasses.replace` / spread, with care for nested data |
| Exactly one shared instance | Singleton | Build it once in `main` and pass it in |
| A type you do not own has the wrong interface | Adapter | A small wrapper type, or a function type like `http.HandlerFunc` |
| Two dimensions vary independently (what × how) | Bridge | An interface-typed field; composition |
| A tree where one item and a group are handled alike | Composite | A recursive type with one shared method |
| Add behavior around a call without editing it (log, retry, cache) | Decorator | Middleware: a function that wraps a function |
| Callers need one simple entry point into a messy subsystem | Facade | A package or module with a small public API |
| Millions of near-identical objects, memory-bound | Flyweight | Interning: Go `unique`, `sys.intern`, a shared `Map` |
| Control access: lazy, remote, cached, permission-checked | Proxy | A wrapper with the same interface as the real thing |
| A request passes through handlers that may each stop it | Chain of Responsibility | A slice of middleware |
| Actions as values: queue, log, retry, undo | Command | A closure; a struct only when undo or serialization needs data |
| Evaluate a small language or rule set | Interpreter | An AST plus one `eval` function, or an existing expression library |
| Walk a collection without exposing its layout | Iterator | `iter.Seq` / a generator / `Symbol.iterator` |
| Many components talk to each other, coupling grows N×N | Mediator | One coordinator, or an event bus |
| Save and restore state (undo, rollback) | Memento | Immutable values; keep the old one |
| Dependents react to changes | Observer | Callbacks, channels, `EventTarget`, signals |
| Behavior depends on state and the transitions multiply | State | Enum + transition table; a state interface when states carry behavior |
| Swap an algorithm at runtime | Strategy | Pass a function |
| A fixed series of steps where some steps vary | Template Method | A function that takes the varying steps as arguments |
| Many operations over a fixed set of node types | Visitor | A type switch / `match` / discriminated union with an exhaustive check |

## SOLID quick cues

- **Single Responsibility.** "One reason to change" means one *actor*, the person or
  team who asks for changes. It does not mean one method or one verb. Smell: two
  unrelated requesters (billing and reporting) keep editing the same type.
- **Open/Closed.** Add new cases without editing old code, *where cases actually get
  added*. Smell: the same `switch` on kind repeated in several files, so a new kind
  means editing all of them. One `switch` in one place is fine.
- **Liskov Substitution.** A subtype must keep the contract: same preconditions or
  looser, same guarantees or stronger, no new surprise errors. Smells: callers
  type-checking for a specific implementation, methods that throw "not supported",
  the classic `Square` that breaks `Rectangle.setWidth`.
- **Interface Segregation.** Callers should not depend on methods they do not use.
  Smell: a test fake implementing twelve methods to exercise one. In Go the fix is
  structural: the consumer declares the one- or two-method interface it needs.
- **Dependency Inversion.** Business rules depend on abstractions they own, and the
  database or HTTP code plugs into them. Smell: domain code importing a SQL driver or
  an SDK. It does *not* mean every type needs an interface.

## When to Read Which Reference

- **SOLID in depth.** What each principle protects against, the smell, a
  counter-example, and how it reads in languages without inheritance →
  [references/solid.md](references/solid.md)
- **Creational patterns.** Factory Method, Abstract Factory, Builder, Prototype,
  Singleton, plus object pools and dependency injection →
  [references/creational.md](references/creational.md)
- **Structural patterns.** Adapter, Bridge, Composite, Decorator, Facade, Flyweight,
  Proxy → [references/structural.md](references/structural.md)
- **Behavioral patterns.** Chain of Responsibility, Command, Interpreter, Iterator,
  Mediator, Memento, Observer, State, Strategy, Template Method, Visitor →
  [references/behavioral.md](references/behavioral.md)
- **Go.** Implicit interfaces, embedding, functional options, `iter.Seq`, channels,
  `sync.OnceValue`, and which patterns vanish → [references/go.md](references/go.md)
- **Python.** Protocols, first-class functions, generators, decorators, context
  managers, modules as singletons → [references/python.md](references/python.md)
- **TypeScript / JavaScript.** Structural typing, discriminated unions, closures,
  options objects, `Symbol.iterator`, `EventTarget`, `using` →
  [references/typescript.md](references/typescript.md)

The catalog files are language-neutral: intent, the force, the cost, when not to use
it. The language files are the source of truth for what the code looks like. Read
one of each. For another language, use the closest one: Rust and Swift read like Go
(no class inheritance, enums with `match`); Kotlin, Java and C# are close to the
textbook; Ruby and PHP read like Python.

## Quick Cues

- **Singleton is the pattern to push back on most.** A global hides a dependency,
  couples every test to shared state, and makes order of initialization matter.
  Build the object once where the program starts and pass it in. If lazy creation is
  truly needed, Go has `sync.OnceValue`, Python has a module-level value or
  `functools.cache`, and TypeScript has a module export.
- **A Strategy with one strategy is indirection.** So is a Factory with one product
  and an interface with one implementation and no test that needs a fake. Wait for
  the second real case, and extract on the third.
- **Adapter, Decorator and Proxy look identical: a wrapper.** Name them by intent.
  Adapter changes the interface, Decorator adds behavior behind the same interface,
  Proxy controls access behind the same interface.
- **Visitor versus type switch.** Visitor makes new *operations* cheap and new
  *types* expensive. A closed union with an exhaustive check (TypeScript `never`,
  Python `match` + `assert_never`, a Go type switch checked by `gochecksumtype`)
  gets the same result with far less code, and is usually the better choice.
- **Every subscribe needs an unsubscribe.** Observer's classic bug is the leak: a
  listener outliving its owner. In Go, a channel-based observer also needs a policy
  for slow subscribers: block, drop, or buffer.
- **Template Method needs inheritance.** In Go, and in any code that prefers
  composition, pass the varying steps as functions instead.
- **In Go, accept interfaces and return concrete types.** An interface declared next
  to its only implementation is Java written in Go. Declare it where it is consumed.

## Anti-patterns

- **Pattern-first design.** Picking a pattern, then looking for somewhere to use it.
- **Speculative generality.** Abstractions for a second implementation nobody has
  asked for. The cost is paid on every read of the code; the benefit may never come.
- **Translating Java literally.** Abstract base classes, getter/setter pairs,
  `FooFactoryImpl`, factories of factories, and `I`-prefixed interfaces in Go,
  Python or TypeScript.
- **Pattern names in type names where a domain name would do.** `PaymentStrategy` is
  weaker than `Pricer`; `NotificationObserverManager` says nothing about the domain.
- **Inheritance for code reuse.** Deep Template Method chains, where understanding one
  method means reading four classes. Compose instead.
- **SOLID as a scoring rubric.** Citing a principle without naming the concrete change
  it makes painful. "Violates SRP" with no second actor is an opinion, not a finding.
- **Interfaces "for testability" on every type.** Add the seam where a test actually
  needs a fake, at the consumer, when that test is written.
