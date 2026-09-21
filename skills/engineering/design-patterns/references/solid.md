# SOLID

Five principles collected by Robert C. Martin around 2000 and named by Michael
Feathers. Each one protects against a specific kind of change going wrong. Read them
as smell detectors: tools for spotting where the next change will hurt, and for
explaining why. They are not a checklist, and code does not earn points for
satisfying them.

This file is language-neutral. For how each principle shows up in a given language,
see the "SOLID in ..." section of [go.md](go.md), [python.md](python.md) or
[typescript.md](typescript.md).

## Contents

- [Using SOLID in a review](#using-solid-in-a-review)
- [Single Responsibility](#single-responsibility)
- [Open/Closed](#openclosed)
- [Liskov Substitution](#liskov-substitution)
- [Interface Segregation](#interface-segregation)
- [Dependency Inversion](#dependency-inversion)
- [How the principles interact](#how-the-principles-interact)
- [Neighboring principles](#neighboring-principles)

## Using SOLID in a review

A SOLID finding has four parts. If you cannot fill in the second one, drop the
finding.

1. **The principle.** Which one, by name.
2. **The change that hurts.** A concrete change that is likely, or has already
   happened, and what it would cost: "adding a refund type means editing these four
   switches", "the billing team's overtime change breaks the ops report".
3. **The evidence.** File and line, the repeated `switch`, the type check, the
   twelve-method fake.
4. **The smallest fix.** Often not a pattern at all: split a function, move a
   method, narrow a parameter type.

Two rules keep reviews honest:

- **The principles pull against simplicity.** Every fix adds a type, an interface
  or an indirection. When the change is hypothetical, simplicity wins the tie.
- **Code can be fine.** A review that finds nothing to change is a valid result. Do
  not manufacture violations to show the principles were checked.

## Single Responsibility

**Statement.** The original: "A class should have one, and only one, reason to
change." Martin's later wording (*Clean Architecture*, 2017) says what a reason is:
"A module should be responsible to one, and only one, actor." An actor is a person
or group who asks for changes.

**What it protects against.** A change requested by one group breaking behavior that
another group depends on, and two teams colliding in the same file.

**Martin's own example.** An `Employee` type with `calculatePay()` (used by finance),
`reportHours()` (used by operations) and `save()` (owned by the database team). Both
pay and hours share a `regularHours()` helper. Finance changes how overtime counts,
edits the helper, and the operations report is now wrong. Nobody on finance knew it
was used there.

**The textbook example.** A `User` type that holds user data, saves itself to the
database, and sends the welcome email. Split it into `User` (data), a user store
(persistence) and a notifier (email). The split is justified by the three actors
behind it (product, the database owners, whoever writes the emails) and by the side
effects that make `User` untestable without a database and a mail server. It is not
justified by counting verbs.

**Smells.**

- Commits from unrelated features keep landing in the same type or module.
- A helper shared by two methods that serve different people.
- A type whose tests need setup from several unrelated domains.

**The common misreading.** "A class should do one thing." That rule is for functions.
Applied to types it produces dozens of one-method classes and makes code harder to
follow, not easier. A type with fifteen methods that all serve one actor is fine.

**The fix.** Separate by actor. Keep the shared data in a plain struct or record,
put each actor's behavior in its own module, and add a facade if callers still want
one entry point.

## Open/Closed

**Statement.** "Software entities should be open for extension, but closed for
modification" (Bertrand Meyer, 1988; Martin's version uses polymorphism instead of
inheritance).

**What it protects against.** Every new variant forcing edits across working code,
each edit a chance to break something that already passed its tests.

**The textbook example.** A `ShippingCalculator` with a `switch` over Ground, Air and
Sea. Adding Drone means editing the calculator. The fix moves each method behind a
`ShippingMethod` interface with `cost()` (or into a map of cost functions), so Drone
is new code rather than an edit. That fix is earned when carriers really do get
added, or when the same `switch` also appears in the ETA and label code. Three
methods, one `switch`, and no new carrier in two years: the `switch` is the simpler
design, and the review should say so.

**Smells.**

- The same `switch` or `if` chain on a kind or type field, repeated in several
  places. Adding a kind means finding all of them, and missing one is a silent bug.
- A core module that must be edited every time a customer, provider or format is
  added.

**The common misreading.** "Never edit existing code," or "make everything
pluggable up front." Closure is a choice about *which* changes to protect against,
and you can only choose well once you have seen the change. Martin's advice: take
the first bullet, then protect yourself against the next one of the same kind.

**The fix.** Put the variation behind one seam: a Strategy, a registry of handlers,
polymorphism. Then new variants are new code, not edits.

**The other valid answer.** In languages with closed sum types and exhaustive
matching (TypeScript unions, Rust enums, Python `match` with `assert_never`), the
opposite design is also sound: keep one `switch` per operation, and let the compiler
list every site to update when a variant is added. This is the expression problem.
Polymorphism makes new *types* cheap and new *operations* expensive; exhaustive
matching does the reverse. Pick by which axis actually grows.

## Liskov Substitution

**Statement.** From Barbara Liskov and Jeannette Wing (1994), informally: code that
works with a type must keep working, without knowing it, when given any subtype.

**The rules.** A subtype, or any implementation of an interface:

- must not **strengthen preconditions** (demand more of its inputs),
- must not **weaken postconditions** (promise less about its results),
- must **preserve invariants** of the base type,
- must not throw **new kinds of errors** the contract does not allow.

**What it protects against.** Callers that need to know which implementation they
hold, and bugs that appear with one implementation only.

**Smells.**

- Callers downcasting or type-checking for a specific implementation.
- Overrides that throw "not supported" or silently do nothing.
- Documentation that says "do not call X on this one".
- A shared test suite for an interface that one implementation fails.

**Classic examples.**

- `Square` extends `Rectangle`. Setting the width of a square also sets its height,
  so code that sets width 5 and height 4 and expects area 20 breaks. The fix is not
  a smarter `Square`; it is to stop claiming a square is a mutable rectangle.
- `Bird` has `fly()`, and `Penguin` extends `Bird` and throws from it. Any loop over
  birds that calls `fly()` now crashes on penguins. The fix: `Bird` promises only
  what every bird does, and `fly()` moves to a narrower type (`FlyingBird`, or a
  `Flier` interface) that only flying birds implement.

Both break the same rule: the subtype claims a type whose promises it cannot keep.
Real-world inheritance ("a penguin *is a* bird") is not the test; behavior is.

**It applies without inheritance.** Any implementation of an interface, protocol or
structural type is a subtype. A Go `io.Writer` that returns `n < len(p)` with a nil
error breaks the documented contract, and every caller that trusts it breaks too.
The contract is the documentation, not only the method signatures.

**A contract can make an operation optional.** Java's `List.add` is documented as
an optional operation, so `Arrays.asList(...).add(x)` throwing is technically within
contract. It still pushes a check onto every caller. Prefer splitting the interface
(read-only versus mutable) over optional operations.

**The fix.** Split the interface so each implementation can honor all of it, use
composition instead of inheritance, or make the contract explicit and test it
against every implementation.

## Interface Segregation

**Statement.** "Clients should not be forced to depend upon interfaces that they do
not use."

**What it protects against.** Clients rebuilt, redeployed or retested for changes
to methods they never call, and test fakes that cost more than the code under test.

**Smells.**

- An interface with ten or more methods where most implementations stub half.
- Test fakes implementing a large interface to exercise one method.
- A function that takes a whole `Service` or client but calls one method on it.

**The textbook example.** A `Worker` interface with `work()`, `eat()` and `sleep()`.
A `RobotWorker` has to leave `eat()` and `sleep()` empty or throw, which is also a
Liskov smell. Split it into role interfaces (`Worker`, `Eater`, `Sleeper`): humans
satisfy all three, robots only `Worker`, and the scheduler that only assigns work
asks for `Worker`. The Java and C# convention of naming these `IWorkable` does not
carry over to Go, Python or TypeScript.

**The fix.** Role interfaces, declared by the client that needs them. The client
asks for exactly what it uses: `Reader`, not `FileSystem`. In structurally typed
languages (Go, TypeScript, Python protocols) this is cheap, because implementations
satisfy the small interface without declaring it.

**Over-application.** A one-method interface for every call site, or splitting an
interface that every client uses in full. Segregate along real client boundaries.

## Dependency Inversion

**Statement.** "High-level modules should not depend on low-level modules. Both
should depend on abstractions. Abstractions should not depend on details."

**The part people miss: ownership.** The abstraction belongs to the high-level
policy. The domain declares `OrderStore` in its own terms, and the Postgres code
implements it. The source dependency then points *against* the flow of control:
the domain calls the database at runtime, but the database package imports the
domain, not the other way around. That reversal is the inversion.

**What it protects against.** Business rules that cannot be tested without a
database or network, infrastructure swaps that require editing domain code, and
import cycles.

**The textbook example.** A store's `checkout()` constructs a Stripe client directly.
Switching to PayPal, or testing checkout without calling Stripe, means editing the
store. The fix: the store declares the interface it needs, a `PaymentProcessor`
with `charge(amount, source)`, and the program's entry point passes in a Stripe or
PayPal implementation. The interface must speak the store's language (money,
orders), not Stripe's (payment intents, Stripe error codes). An interface that
mirrors one vendor's API is a renamed dependency on that vendor, and swapping
providers still ripples through the store.

**Smells.**

- Domain or business packages importing a SQL driver, an HTTP client or a vendor
  SDK.
- Business rules reading environment variables, globals or the clock directly.
- Services constructing their own dependencies inside methods.

**The fix.** Pass dependencies in through constructors, and wire the program in one
place where it starts, the composition root. Manual wiring is usually clearest; a
DI container starts to pay off only when the object graph is large or has lifecycle
scopes.

**Three terms that get mixed up.**

- **Dependency inversion** is the principle: depend on abstractions you own.
- **Dependency injection** is a technique: pass dependencies in rather than
  constructing them.
- **An IoC container** is a tool that automates injection. It is optional.

**What it does not mean.** An interface for every type. Stable, pure dependencies
(the standard library's string and math functions) need no abstraction. The clock
and randomness are the usual exceptions, because tests need to control them.

## How the principles interact

- **SRP and ISP are one idea at two levels.** Split implementations by who changes
  them, split interfaces by who uses them.
- **OCP depends on LSP.** Extending by substitution only works if the substitutes
  behave.
- **DIP makes OCP work across module boundaries.** New implementations plug in
  without the high-level module importing them.
- **All five add indirection.** Taken to the limit they produce a fog of tiny types
  and interfaces, each easy to read and the whole impossible to follow. John
  Ousterhout's *deep modules* argument (a small interface hiding a lot of
  functionality) is the useful counterweight.

## Neighboring principles

- **Composition over inheritance** (GoF, 1994). Most of the behavioral patterns are
  cleaner built by composing objects or functions than by subclassing.
- **YAGNI and the rule of three.** Build for the cases you have. Extract the
  abstraction when the third concrete case shows what actually varies.
- **The wrong abstraction.** Sandi Metz: "duplication is far cheaper than the wrong
  abstraction." A premature pattern locks in a guess about what varies; undoing it
  later costs more than the duplication it removed.
- **Law of Demeter.** Talk to your direct collaborators, not to their collaborators.
  Chains like `order.customer().address().city()` couple the caller to three
  structures at once.
