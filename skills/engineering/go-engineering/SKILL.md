---
name: go-engineering
description: >-
  Use whenever writing, editing, testing, debugging or reviewing Go code — a
  .go file, a handler or service, a failing go test, a goroutine leak, a go
  vet or golangci-lint complaint, error handling, interfaces, contexts,
  concurrency — not only when optimizing. Best practices for idiomatic, readable and
  performant Go: code style (naming, errors, interfaces, tests, contexts,
  goroutine lifetimes, readability) from the Google Go Style Guide, and
  performance optimization (memory, allocations, GC, networking,
  concurrency) from goperf.dev. Also use when asking about Go naming
  conventions, error wrapping, test doubles, performance patterns, style,
  or readability. When reviewing a whole diff, branch or PR, git-code-review
  runs the review and uses this skill for the Go checklist; doc-comment
  wording and coverage belong to code-documentation, pattern choice to
  design-patterns.
disable-model-invocation: false
compatibility: >-
  Assumes a Go toolchain for the measurement workflow — go test -bench, pprof,
  and go build -gcflags=-m for escape analysis. The style guidance applies
  without them.
---

# Go Engineering

## Overview

Apply measurement-driven performance patterns from the [Go Optimization Guide](https://goperf.dev) and idiomatic style and readability principles from the [Google Go Style Guide](https://google.github.io/styleguide/go). For everyday code, follow the style guide's idioms for errors, interfaces, tests, contexts and concurrency. For performance work, measure first (benchmarks, pprof, escape analysis); then apply targeted patterns. Focus on production workloads: backend services, pipelines, and systems where latency, throughput, and long-term maintainability matter.

## Workflow

### Writing or reviewing code

1. **Find the section for the task** — Use the map below to jump to the matching section of [references/styleguide/best-practices.md](references/styleguide/best-practices.md) (idioms) or [references/styleguide/decisions.md](references/styleguide/decisions.md) (rules and rationale). Grep for the heading rather than reading the whole file.
2. **Follow the project's existing conventions** where they are consistent; the style guide settles what the codebase leaves open.
3. **Run the project's linter and tests before committing** — e.g. `golangci-lint run` and `go test ./...`.

| Task | Where to look |
| --- | --- |
| Interfaces and seams — consumer-owned, avoiding unnecessary ones | best-practices.md → *Interfaces* (*Avoid unnecessary interfaces*, *Interface ownership and visibility*, *Designing effective interfaces*); decisions.md → *Interfaces* |
| Errors — wrapping with `%w`, sentinel vs typed, error structure | best-practices.md → *Error handling* (*Error structure*, *Adding information to errors*, *Placement of %w in errors*, *Logging errors*); decisions.md → *Errors* |
| Tests and test doubles — `t.Error` vs `t.Fatal`, table-driven | best-practices.md → *Tests* (*`t.Error` vs. `t.Fatal`*, *Error handling in test helpers*, *Don't call `t.Fatal` from separate goroutines*) and *Test double and helper packages*; decisions.md → *Table-driven tests*, *Subtests*, *Test helpers* |
| Contexts and deadlines | decisions.md → *Contexts*; best-practices.md → *Documentation* → *Contexts* |
| Naming | best-practices.md → *Naming* (*Function and method names*, *Util packages*); decisions.md → *Naming* |
| Concurrency and goroutine lifetimes | decisions.md → *Goroutine lifetimes*; best-practices.md → *Documentation* → *Concurrency*, and *Variable declarations* → *Channel direction* |
| Options, constructors and argument lists | best-practices.md → *Function argument lists* (*Option structure*, *Variadic options*) |
| Package-level state | best-practices.md → *Global state* |

### Optimizing

1. **Establish a baseline** — Add or run benchmarks; profile under load with pprof (CPU, memory). Optimizing without numbers often targets the wrong place; a baseline makes the impact of changes observable and avoids wasted effort. So hold back pooling, preallocation or GOGC changes until there are benchmark or pprof numbers, and guide the user to get them; without data these add complexity for a bottleneck that may not exist.
2. **Identify the bottleneck** — Allocations/GC, I/O, scheduler, or networking. Use `go build -gcflags="-m" ./pkg` to see what escapes to the heap.
3. **Apply patterns from references** — Use the appropriate reference file below; all recommendations are self-contained in this skill. Each reference is organized by section with tables and code examples; jump to the section that matches the bottleneck. For extended articles, see [goperf.dev](https://goperf.dev).

## When to Read Which Reference

### Performance (goperf.dev)

- **Memory, allocations, GC, concurrency, I/O, compiler flags, escape analysis** → Read [references/performance/common-patterns.md](references/performance/common-patterns.md) (see its table of contents to find the right section).
- **HTTP, Transport tuning, connection reuse, 10k+ connections, TLS, DNS, load shedding, backpressure, TCP/HTTP/2/gRPC/QUIC** → Read [references/performance/networking.md](references/performance/networking.md) (see its table of contents to find the right section).

### Style Guide (Google Go Style Guide)

- **Code style, naming, formatting, readability, simplicity, and idiomatic Go practices** → Use the task map above to jump to a section of [references/styleguide/best-practices.md](references/styleguide/best-practices.md) (idioms) or [references/styleguide/decisions.md](references/styleguide/decisions.md) (rationale); each opens with a contents list. Read [references/styleguide/guide.md](references/styleguide/guide.md) for the core principles; it is short enough to read whole.

### Neighbours

- **SOLID and the GoF patterns (Builder, Strategy, Observer, Visitor, Singleton and the rest) in idiomatic Go** → Use the `design-patterns` skill if it is installed; its Go reference covers functional options, `iter.Seq`, consumer-side interfaces and which patterns vanish in Go.
- **Reviewing a diff, branch, commit or PR as a whole** → `git-code-review` runs the review and owns the report; this skill supplies the Go checks it applies.
- **Doc-comment wording and documentation coverage** (godoc, package docs, READMEs) → `code-documentation`. The *Documentation* sections in the task map stay useful for what a Go doc comment must state, such as context and concurrency behavior.

## Quick Cues

### Writing code

- **Interfaces**: Define an interface in the package that consumes it, holding only the methods that consumer calls; producers return concrete types. Don't add an interface until a second implementation or a test double needs it.
- **Errors**: Wrap with `fmt.Errorf("...: %w", err)` when callers may inspect the cause, and put `%w` at the end, except when wrapping a sentinel, where leading with it names the failure's category first (`fmt.Errorf("%w: order %q", ErrNotFound, id)`). When callers branch on a condition, expose a sentinel (`var ErrNotFound = errors.New(...)`) or a typed error and match with `errors.Is` / `errors.As`, never by string.
- **Tests**: Use `t.Error` to report a failure and keep checking the rest; use `t.Fatal` only when the test cannot meaningfully continue (setup failed, a nil result would panic). Never call `t.Fatal` from a goroutine other than the test's own: it calls `runtime.Goexit`, which stops only that goroutine, not the test: the test function runs on past the failure, and a failure reported after the test has returned panics. In spawned goroutines use `t.Error` and return, and wait for them before the test's final checks.
- **Naming**: Use `MixedCaps` or `mixedCaps` (camel case) rather than underscores (snake case) for multi-word names. Keep names short and contextual without repetition.
- **Contexts**: Take `ctx context.Context` as the first parameter and pass it through to every call that does I/O or may block; don't store it in a struct field.
- **Spelling and lint**: Go's own code uses US spelling (canceled, canceling, marshaling) in identifiers, comments and error strings. The `misspell` linter enforces this only with `linters.settings.misspell.locale: US`; by default it accepts "cancelled" and "marshalling". golangci-lint reports one issue per line, so a second misspelling on a line shows up only once the first is fixed. Run the project's linter (e.g. `golangci-lint run`) before committing.
- **Atomic file writes**: Create the temp file with `os.CreateTemp` in the target's own directory (so the rename stays on one filesystem), write it, `Sync` it so the data is on disk before the rename, `Close` it, then `os.Rename` it over the target. `CreateTemp` makes the file with mode 0600, so `Chmod` it to the target's mode before the rename, or the replaced file silently loses its permissions. On any error, remove the temp file.

### Performance

- **Connection reuse (HTTP)**: Drain response body before closing (e.g. `io.Copy(io.Discard, resp.Body)` then `resp.Body.Close()`); otherwise the client will not reuse connections.
- **Escape analysis**: Run `go build -gcflags="-m" ./path/to/pkg` to see which values move to the heap; reduce escapes on hot paths to lower GC pressure.

## Edge cases and examples

- **Networking**: When suggesting Transport or connection changes, remind to drain response bodies for connection reuse and to tune timeouts and limits to match the workload. The default Transport keeps only 2 idle connections per host (`DefaultMaxIdleConnsPerHost`), so heavy concurrent traffic to one internal API needs `MaxIdleConnsPerHost` raised; otherwise connections may not be reused or may be held too long.
