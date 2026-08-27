# API and symbol documentation

Use the **canonical convention for each language**. Never invent a custom format —
a bespoke doc style breaks every tool the ecosystem already has (`go doc`, IDE
hovers, generated API sites) and gives the reader nothing in return.

## Contents

- [Convention per language](#convention-per-language)
- [General rules across languages](#general-rules-across-languages)
- [Protocol Buffers](#protocol-buffers)

## Convention per language

| Language          | Convention            | Placement                                                                     |
| ----------------- | --------------------- | ----------------------------------------------------------------------------- |
| Go                | godoc                 | Package overview in `doc.go`; exported symbol docs begin with the symbol name  |
| TypeScript / JS   | JSDoc / TSDoc         | Above the declaration; `@param`, `@returns`, `@throws`, `@example`             |
| Python            | Docstrings            | First statement in the module, class, or function; Google or NumPy style       |
| Dart / Flutter    | dartdoc               | `///`; `{@template}` / `{@macro}` for shared blurbs, `[Symbol]` for references |
| Rust              | rustdoc               | `///` on items, `//!` for module/crate-level; `# Examples`, `# Errors`, `# Panics` |
| Java / Kotlin     | Javadoc / KDoc        | Above the declaration; `@param`, `@return`, `@throws`                          |
| Protobuf (`.proto`) | Leading `//` comments | On every service, RPC, message, field, enum, and enum value — see below      |

Languages not listed follow the same principle: use the ecosystem's canonical
convention and apply the general rules below.

For Python docstring mechanics — `Args:` / `Returns:` / `Raises:` sections and
hanging-indent layout — the sibling `python-engineering` skill carries the full
Google Python Style Guide treatment.

## General rules across languages

**Document unexported and private symbols too.** Exported docs serve API consumers;
unexported docs serve maintainers. Maintainers usually need *more* context than
consumers, not less — they are the people who will have to change this code, often
years later with none of the original context. The "what not to comment" exceptions
still apply at every visibility level: genuinely self-evident code stays bare.

**Lead with one summary sentence in active voice.** Add detail only when it earns
its place. In Go this sentence must begin with the symbol name (`// Parse reads…`)
because `go doc` extracts it verbatim.

**Document errors, panics, and edge cases.** A signature says a function returns an
error; it cannot say *which* errors, when, or whether the caller can retry. That
gap is the single most valuable thing symbol documentation fills.

**State units, formats, and constraints.** `timeout int` is ambiguous; "timeout in
milliseconds; values below 100 are clamped" is not.

**A runnable example beats prose.** Go's `Example` functions, JSDoc `@example`,
Python doctests, and rustdoc code blocks all compile or run as part of the test
suite, so they cannot silently rot the way prose does.

**Say what the zero value or default means** wherever it is not obvious — an empty
string, a nil slice, an unset optional.

## Protocol Buffers

Protobuf has more structural elements needing comments than most languages, and its
`//` comments **propagate into generated code** — Go struct field docs, TypeScript
type comments, Python docstrings. That makes the `.proto` file the single source of
truth for the API contract: a comment written once here reaches every consumer in
every language. A field left bare here is bare everywhere.

Comments are always **leading**, never trailing or inline.

### Services

Explain the domain the service owns and its scope.

> *Manages user authentication for the public API.*

### RPCs

Explain what the call does semantically, plus side effects, idempotency, and the
common error codes.

> *Returns the user matching a valid session token. Returns NOT_FOUND if the token
> is unknown or expired. Idempotent.*

### Messages

Describe the entity or payload in domain terms, not structural ones.

> *Represents a customer's billing address as it appears on receipts.*

### Fields

Cover meaning, units for numerics, format (RFC3339 timestamps, ULID identifiers),
constraints, and what the zero value means in proto3 — proto3 cannot distinguish
"unset" from "set to zero" for scalars, so the reader genuinely cannot infer it.

> *Customer ID in the canonical `cus_<ulid>` format. Required.*

### Enums

Say what the enum classifies, and state explicitly what the zero value (the
`*_UNSPECIFIED` default) means.

### Enum values

Describe when each value applies. Restating the name in prose form
(`ACTIVE` → "the active state") adds nothing.

### Related

Doc comments are this skill's concern. For AIP naming conventions, resource-oriented
design, standard methods, and field behavior annotations, use the sibling
`protocol-buffers` skill — it covers the contract design that these comments describe.
