# READMEs

These rules apply to `README.md` specifically. Other markdown docs
(`CONTRIBUTING.md`, `SECURITY.md`, `docs/*.md`) have their own conventions and
should not be forced into this shape.

## Contents

- [The spine](#the-spine)
- [Section conventions](#section-conventions)
- [Structural conventions](#structural-conventions)

## The spine

Always present, always in this order:

> Title → one-line tagline → About → Installation → Usage → License

Everything else is optional. Add a section only when there is real content for it.
An empty heading is worse than a missing one: it promises the reader something and
then wastes the scroll.

## Section conventions

**Tagline.** One sentence, under 25 words, written for the reader rather than about
the project: *"if you need X, this does Y."*

**About.** Two to four short paragraphs — what it is, the problem it solves, who it
is for, and how it differs from the alternatives. That last part is the one people
skip and the one readers most need.

**Features.** Three to seven bullets of *current* capabilities. Anything not built
yet belongs in Roadmap, not here. Listing planned work as a feature is how READMEs
lose their readers' trust.

**Quick Start.** The 60-second hello world: copy-pasteable, produces visible output,
minimal. Resist adding configuration to it.

**Usage.** Real examples grouped by **use case**, not by API surface. The reader
arrives asking "how do I do X?", not "what does function Y do?" — API-surface
ordering answers a question nobody asked.

**Configuration.** A table, not prose, whenever there are environment variables,
flags, or config keys. Prose configuration is unscannable and always goes stale in
a way tables do not.

**Architecture.** A short overview here; the deep dive goes in `docs/architecture.md`.

**Contributing / Code of Conduct / Security / Changelog.** Link to the companion
files. Do not inline their content — duplicated policy text drifts out of sync and
then nobody knows which copy is authoritative.

**Badges.** Only ones reporting something true and useful: build status, version,
license, coverage, package registry. Skip vanity badges.

**FAQ / Roadmap.** Only when real recurring questions or real upcoming work exist.
Do not pre-invent either; an invented FAQ is a confession that nobody has used the
project yet.

## Structural conventions

**Lead with the reader's need**, not the project's self-description.

**Quick Start and Usage stay separate.** Merging them produces a first example
weighed down by options, which defeats the point of a quick start.

**Link companion docs rather than expanding them inline.** This keeps the README
skimmable and pushes detail to where it belongs.

**In templates, use HTML comments** (`<!-- ... -->`) for authoring guidance. They
disappear from the rendered output once the placeholders are filled in, so a
half-finished README still looks intentional.

**Mark optional sections `[Optional]` in templates** so a future author knows what
can safely be deleted rather than dutifully filling in a section they do not need.
