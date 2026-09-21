# Behavioral patterns

Patterns about how objects share work and responsibility. This file is
language-neutral: for each pattern it gives the intent, the force that earns it,
the shape, the cost, and its neighbors. For what the code looks like, read the same
section in [go.md](go.md), [python.md](python.md) or [typescript.md](typescript.md).

In languages with first-class functions, several of these (Strategy, Command,
Template Method, Chain of Responsibility) collapse to "pass a function". The
catalog entry still matters: it tells you when the function parameter is earned and
what can go wrong.

## Contents

- [Chain of Responsibility](#chain-of-responsibility)
- [Command](#command)
- [Interpreter](#interpreter)
- [Iterator](#iterator)
- [Mediator](#mediator)
- [Memento](#memento)
- [Observer](#observer)
- [State](#state)
- [Strategy](#strategy)
- [Template Method](#template-method)
- [Visitor](#visitor)
- [Commonly confused pairs](#commonly-confused-pairs)
- [Beyond the catalog](#beyond-the-catalog)

## Chain of Responsibility

**Intent.** Pass a request along a chain of handlers, so the sender does not need to
know which one deals with it.

**Two variants.** Say which one you mean.

- **First match wins** (the GoF form). Each handler either handles the request or
  passes it on, and exactly one acts. UI event bubbling, exception handler lookup,
  support-ticket escalation.
- **Pipeline** (the middleware form). Every handler runs in order and any of them may
  stop the request early. HTTP middleware, gRPC interceptors, servlet filters.

**The force.** Ordered, configurable processing where handlers are added, removed or
reordered without editing the others, and the sender should not know who acts.

**Shape.** A handler interface, typically `handle(request, next)`. The chain is a list
composed at startup.

**Cost.**

- A request can fall off the end unhandled. Decide on a default: an error, a 404, a
  fallback handler.
- Order-dependent bugs, and the full flow is hard to see from any one handler.
- Long chains cost a call per link on every request.

**Neighbors.** Decorator (the middleware form is structurally identical; a decorator
always delegates, a chain link may stop); Command (requests in the chain are often
commands); Composite (event bubbling walks up a composite tree).

## Command

**Intent.** Turn a request into a value, so it can be passed around, queued, logged,
retried or undone.

**The force.** Actions that must be treated as data: job queues, undo and redo, macro
recording, audit logs, scheduling, retries, remote execution. Also decoupling the
thing that triggers an action (a button, a menu, a CLI flag) from the code that
performs it.

**Shape.** An interface with `execute()`, and `undo()` if needed. Each concrete
command holds its receiver and parameters. In function-first languages, a closure is
a command.

**When a closure is not enough.** Serialization (to a queue or a log) needs data, a
name and arguments, not a closure. Undo needs the previous state or an inverse
operation. Those two needs are what justify a command *type*.

**Cost.**

- A type per action is boilerplate when closures would do.
- Undo is the hard part: each command must capture enough to reverse itself, and
  commands that touch the outside world (sending an email) cannot be undone at all.

**Neighbors.** Memento (holds the state an undo restores); Strategy (Strategy is *how*
to do something, Command is *what* to do); Composite (a macro is a composite
command); Chain of Responsibility. The "command" in CQRS is a related but separate
idea: a request to change state, as opposed to a query.

## Interpreter

**Intent.** Represent a small language's grammar as types, and evaluate sentences in
it.

**The force.** A small, stable language that is evaluated often: filter expressions,
pricing or eligibility rules, feature-flag targeting, search query syntax, a
configuration DSL.

**Shape.** One type per grammar rule, forming an abstract syntax tree (a Composite),
each with an `evaluate(context)`. Parsing is separate; GoF leaves it out entirely.

**Cost and when not to use it.**

- It scales badly: every grammar rule is another type, and performance lags a
  compiled approach.
- If users write the rules, you now own a security boundary: sandboxing, resource
  limits, and denial of service through deeply nested expressions.
- **Try an existing embeddable language first.** CEL (Common Expression Language),
  expression libraries, JSON Logic, JSONPath or `jq`-style queries, or a
  parameterized SQL `WHERE`. Write your own only when none fit.

**Neighbors.** Composite (the AST); Visitor (operations over the AST other than
evaluation: printing, type checking, optimizing); Iterator.

## Iterator

**Intent.** Give sequential access to a collection's elements without exposing how
it is stored.

**The force.** Collections that callers should loop over uniformly but that are not
plain arrays: trees, paginated APIs, database cursors, streams, generated or infinite
sequences. Hiding pagination behind an iterator is one of the most useful cases.

**Two styles.**

- **External:** the caller pulls (`next()`, `hasNext()`). The caller controls the
  pace and can stop, interleave or zip.
- **Internal:** the collection pushes each element to a callback (`forEach`, Go's
  range-over-func). Simpler to write, especially for recursive structures.

Generators give you both at low cost, and every language in this skill has them or
an equivalent.

**Cost.**

- **Cleanup on early exit.** A loop that breaks out halfway must still close the
  cursor or file. Each language has a mechanism (see the language files); use it.
- **Errors mid-stream.** Decide how a failure on element 500 reaches the caller: a
  paired error value, an exception, or an `err()` method checked after the loop.
- **Mutation during iteration** is undefined or an error in most runtimes.

**When not to use it.** A small collection that is already in memory: return the
list.

**Neighbors.** Composite (the structure being walked); Visitor (applies an operation
to each element, often driven by an iterator); Memento (can capture iteration
state).

## Mediator

**Intent.** Put the rules for how a set of objects interact into one object, so the
objects do not refer to each other.

**The force.** Many-to-many interaction among peers, where each peer knowing the
others makes coupling grow N × N: form fields that enable and disable each other, a
chat room, dialog components, a workflow orchestrator coordinating several services.

**Shape.** Peers know only the mediator and report to it. The mediator holds the
coordination rules and tells peers what to do.

**Cost.**

- **The mediator becomes a god object** holding all the logic that used to be
  spread across the peers.
- **Indirection hides causality.** An event bus is a loose mediator: very decoupled,
  and very hard to answer "what happens when X is published?"

**In distributed systems** this is the orchestration-versus-choreography choice. An
orchestrator is a mediator. Choreography (services react to each other's events) is
the observer-based alternative.

**Neighbors.** Observer (the mechanism a mediator often uses); Facade (one-way
simplification; Mediator coordinates both ways). Libraries called "mediator" that
dispatch requests to handlers (MediatR in .NET, for example) are closer to Command
dispatch than to this pattern.

## Memento

**Intent.** Capture an object's state so it can be restored later, without exposing
its internals.

**The force.** Undo and redo, checkpoints, rolling back a failed multi-step change,
save games, draft recovery.

**Shape.** The *originator* produces an opaque snapshot. A *caretaker* stores
snapshots without reading them. Only the originator can restore from one.

**Cost.**

- **Memory.** Full snapshots of large state add up. Store diffs or inverse commands,
  or use persistent data structures that share unchanged parts.
- **External state cannot be snapshotted.** Files written, emails sent and rows in
  another service are not undone by restoring a memento.
- Encapsulation of the snapshot is only as strong as the language allows: package
  privacy in Go, convention in Python, `#private` fields in TypeScript.

**The modern shortcut.** With immutable state, the memento is simply the previous
value. Keep it. This is how Redux-style time travel works.

**Neighbors.** Command (undo by inverse operation, versus by snapshot; often
combined); Prototype (copying is how snapshots are made); Iterator.

## Observer

**Intent.** When one object changes, notify the objects that depend on it, without it
knowing who they are.

**The force.** Dependents that vary or are unknown to the source: views updating from
a model, domain events triggering emails and analytics, cache invalidation, config
reloads.

**Shape.** The subject keeps a list of subscribers. `subscribe` returns a way to
unsubscribe. On change, the subject notifies each subscriber.

**Decisions to make explicitly.** Most Observer bugs come from leaving one of these
implicit.

- **Push or pull.** Send the new data, or send "something changed" and let
  subscribers read it.
- **Sync or async delivery.** Synchronous is simpler to reason about; asynchronous
  keeps a slow subscriber from blocking the subject.
- **Errors.** Does one failing subscriber stop the rest?
- **Reentrancy.** A subscriber that subscribes or unsubscribes during notification.
  Iterate over a snapshot of the list.
- **Slow subscribers.** With queues or channels, block, drop or buffer? Each is a
  real choice with a real cost.
- **Lifetime.** Who unsubscribes, and when?

**Cost.**

- **The lapsed-listener leak.** A subscriber that is never unsubscribed keeps itself,
  and everything it references, alive. This is the classic Observer bug.
- **Notifying mid-change.** Notify only once the subject's state is consistent again,
  and for persisted state, only after the transaction commits.
- **In-process events are not durable.** If the process dies between the change and
  the notification, the event is gone. For side effects that must happen (stock
  updates, customer emails, billing), write the event to a queue or an outbox table
  in the same transaction as the change, and deliver it from there.
- **Cascades and cycles.** Updates triggering updates, sometimes forever.
- **Control flow that is hard to follow** from reading the code.

**Neighbors.** Mediator (often built on observers); publish-subscribe (observer with a
broker in the middle, decoupled in time and place); reactive streams and signals
(observer with composition operators and automatic dependency tracking).

## State

**Intent.** Let an object change its behavior when its internal state changes.

**The force.** Behavior that branches on a status field across many methods (`if
status == draft ... elif submitted ...` in `submit`, `approve`, `cancel` and
`edit`), plus rules about which transitions are allowed.

**Two shapes.** Choose deliberately.

- **Transition table.** An enum of states and a table from (state, event) to the next
  state. The whole machine is visible in one place, easy to test, draw and persist.
  **Prefer this by default,** especially when most of the logic is "is this
  transition allowed?".
- **State objects** (the GoF form). Each state is a type that implements the
  operations and returns the next state. Worth it when each state carries a lot of
  distinct behavior.

**Cost.**

- State objects scatter the transition graph across many types; nobody can see the
  whole machine.
- Tables can grow a large `switch` when states carry behavior.
- Decide what an illegal transition does: an error, a no-op, or a panic.
- Stored state is an enum in the database either way; state objects need mapping
  back and forth.

**Neighbors.** Strategy (identical structure; a strategy is chosen by the client and
rarely changes, a state replaces itself as events arrive); Flyweight (stateless state
objects can be shared); Memento.

## Strategy

**Intent.** Define a family of interchangeable algorithms and choose one at runtime.

**The force.** An algorithm that really varies by configuration, customer or input,
with at least two real variants: pricing rules per plan, retry and backoff policies,
compression codecs, sort orders, routing modes.

**Shape.** An interface with one method, or simply a function type. The context holds
one and calls it.

**Cost and when not to use it.**

- **One strategy is pure indirection.** Wait for the second variant.
- **The `switch` moves, it does not disappear.** Something still picks the strategy.
  The win is that the choice happens once, at the edge (config, a registry, `main`),
  instead of inside the algorithm on every call.

**Neighbors.** State (same structure, different intent); Template Method (the
inheritance-based version of the same idea); Command; Bridge; Decorator (changes the
skin, where Strategy changes the guts).

## Template Method

**Intent.** Define the skeleton of an algorithm once and let variants fill in some
steps.

**The force.** Several variants that share an invariant sequence and differ in a few
steps, where the order must be enforced: open, validate, process, close; test
set-up and tear-down; framework lifecycle hooks. This is the Hollywood principle:
"don't call us, we'll call you".

**Shape.** In the GoF form, a base class with a final method that calls abstract or
hook methods which subclasses override. In composition-first code, a function that
takes the varying steps as arguments, or a struct of step functions.

**Cost.**

- **Inheritance coupling.** Changes to the base class break subclasses in ways
  neither side can see (the fragile base class problem).
- **The yo-yo problem.** Understanding one run means reading up and down the class
  hierarchy.
- Hooks multiply until the skeleton is mostly hooks.

**Prefer the composition form** unless you are writing a framework whose users expect
to subclass.

**Neighbors.** Strategy (the composition version: pass the steps in); Factory Method
(often one of the steps).

## Visitor

**Intent.** Add operations over a fixed set of element types without changing those
types.

**The force.** A stable set of node types (an AST, a document model, an intermediate
representation) with a growing set of operations over it: type checking, pretty
printing, optimizing, code generation, linting.

**Shape.** Each element has `accept(visitor)`, which calls the visitor's method for
its own type (`visitNumber`, `visitAdd`). This is double dispatch: the operation
chosen depends on both the visitor and the element.

**Cost.**

- **Adding an element type means updating every visitor.** Visitor trades cheap new
  operations for expensive new types: the expression problem again (see Open/Closed
  in [solid.md](solid.md#openclosed)).
- Boilerplate: an `accept` per element and a method per element per visitor.
- Visitors often need access to element internals, which weakens encapsulation.

**The modern alternative.** In languages with closed unions and pattern matching
(TypeScript discriminated unions, Python `match`, Rust enums, Go type switches with a
checker), an exhaustive match *is* a visitor, without `accept`. Use the match unless
the language cannot check exhaustiveness and the node set is large.

**Neighbors.** Composite (the structure visited); Interpreter (evaluation is one
visitor among many); Iterator (walks elements; Visitor acts on each).

## Commonly confused pairs

| Pair | The difference |
| --- | --- |
| Strategy and State | Same shape. The client picks a strategy; a state replaces itself as events arrive. |
| Strategy and Template Method | Both vary steps of an algorithm. Strategy by composition, Template Method by inheritance. |
| Strategy and Command | Strategy is *how* to do a thing; Command is *which* thing to do, as a value. |
| Chain of Responsibility and Decorator | Same middleware shape. A decorator always delegates; a chain link may stop. |
| Observer and Mediator | Observer broadcasts to unknown listeners; Mediator coordinates known peers through one hub. |

## Beyond the catalog

**Null Object.** An implementation that does nothing, safely: a no-op logger, an empty
discount. It removes `if x != nil` checks from every caller. Use it when "absent"
genuinely means "do nothing"; not when absence is an error the caller should see.

**Specification.** Business rules as composable predicates (`isOverdue.and(isHighValue)`)
that can be evaluated in memory or translated to a query. Earned when the same rules
must run in more than one place; otherwise a plain function is clearer.

**Pipes and filters.** A pipeline of independent stages connected by streams or
channels. It is the data-processing sibling of Chain of Responsibility, and in Go it
is the natural shape for concurrent work.
