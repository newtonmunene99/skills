# Open Knowledge Format (OKF)

Authoring knowledge documents in [OKF v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

OKF is a fourth artifact, distinct from comments, symbol docs, and READMEs. Those
describe *code*. OKF describes **knowledge** — the metadata, context, and curated
insight around data and systems: what a table means, how a metric is defined, what
to do when an alert fires. It is a directory of markdown files with YAML
frontmatter, readable with `cat` and shippable with `git clone`.

## Contents

- [Before you write anything](#before-you-write-anything)
- [Bundle structure](#bundle-structure)
- [Concept documents](#concept-documents)
- [Provenance, trust, and lifecycle](#provenance-trust-and-lifecycle)
- [Never forge a verification](#never-forge-a-verification)
- [Actors](#actors)
- [Cross-linking](#cross-linking)
- [index.md and log.md](#indexmd-and-logmd)
- [Attested Computation](#attested-computation)
- [Conformance](#conformance)
- [Legacy v0.1 documents](#legacy-v01-documents)
- [Common mistakes](#common-mistakes)

## Before you write anything

**Creating OKF documents is a scope decision, not a formatting one.** A knowledge
bundle is a new artifact in someone's repository with its own conventions and its
own maintenance burden. Writing one uninvited is the documentation equivalent of
adding a new top-level directory nobody asked for.

So: **when it is not clear whether OKF documents are wanted, ask.**

Proceed without asking only when the intent is unmistakable:

- The user named the format — "OKF", "knowledge bundle", "concept doc".
- The repository already contains a bundle (a directory of `.md` files with `type:`
  frontmatter, usually alongside an `index.md`) **and** the request is plainly about
  extending it.
- A project guideline or `CONTRIBUTING.md` says knowledge lives in OKF.

Ask when any of these hold:

- The request is "document X" in a repo that has both code and a bundle. Godoc for
  the package and an OKF concept for the dataset it serves are different jobs with
  different readers, and "document it" does not pick one.
- A bundle exists but the request concerns code the bundle does not cover.
- Nothing OKF-shaped exists yet and the user has not named the format. Standing up
  a bundle is a decision about how a team stores knowledge — theirs to make.

A good question is short and offers the concrete options, for example: *"You've got
a `knowledge/` bundle and an undocumented Go package here. Do you want godoc on the
package, an OKF concept describing the dataset, or both?"* One question, options as
a short list — not a questionnaire.

When the answer is "both", they are still separate passes with separate rules. Do
not let OKF frontmatter leak into source files or godoc conventions leak into
concept bodies.

## Bundle structure

A bundle is a directory tree. The layout is domain-independent; organize concepts
however suits the knowledge being captured.

```
path/to/bundle/
  index.md                  # Optional. Directory listing, for progressive disclosure.
  log.md                    # Optional. Chronological update history.
  <concept>.md              # A concept at the bundle root.
  <subdirectory>/
    index.md
    <concept>.md
```

**`index.md` and `log.md` are reserved** at every level and must never be used as
concept documents. Every other `.md` file is a concept.

A concept's **ID** is its path within the bundle with `.md` removed.

Bundles ship as a git repository (recommended — history, attribution, and diffs come
free), a tarball, or a subdirectory of a larger repo.

## Concept documents

Every concept is UTF-8 markdown: a YAML frontmatter block delimited by `---`, then a
markdown body.

### Frontmatter

```yaml
---
type: BigQuery Table                # REQUIRED — the only always-required key
title: Customer Orders              # Recommended
description: One row per completed customer order across all channels.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, orders, revenue]
---
```

- **`type`** — a short string naming the kind of concept. Consumers route, filter,
  and present on it. Examples: `BigQuery Table`, `API Endpoint`, `Metric`,
  `Playbook`, `Reference`, `Attested Computation`. **Types are not registered
  anywhere.** Pick something descriptive and self-explanatory; consumers are
  required to tolerate types they do not recognise.
- **`title`** — human-readable display name. Without it, consumers fall back to the
  filename, which is usually worse.
- **`description`** — one sentence. This is what lands in `index.md` entries, search
  snippets, and previews, so it does more work than its length suggests.
- **`resource`** — a URI identifying the underlying asset. Omit for concepts about
  abstract ideas rather than physical resources.
- **`tags`** — a YAML list of short strings for cross-cutting grouping.

Producers may add any other keys. Consumers must not reject unknown ones, and
should preserve them when round-tripping.

### Body

Standard markdown. **Favor structural markdown** — headings, lists, tables, fenced
code blocks — over freeform prose, because structure serves both a human skimming
and an agent retrieving.

No section is required. Three headings carry conventional meaning:

| Heading         | Purpose                                              |
| --------------- | ---------------------------------------------------- |
| `# Schema`      | Structured description of an asset's columns/fields  |
| `# Examples`    | Concrete usage examples, usually fenced code blocks  |
| `# Computation` | The sanctioned computation of an Attested Computation |

### Worked example

```markdown
---
type: BigQuery Table
title: Customer Orders
description: One row per completed customer order across all channels.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, orders, revenue]
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-08-27T14:30:00Z }
---

# Schema

| Column        | Type      | Description                                         |
| ------------- | --------- | --------------------------------------------------- |
| `order_id`    | STRING    | Globally unique order identifier.                   |
| `customer_id` | STRING    | Foreign key into [customers](/tables/customers.md). |
| `total_usd`   | NUMERIC   | Order total in US dollars.                          |
| `placed_at`   | TIMESTAMP | When the customer submitted the order.              |

# Joins

Joined with [customers](/tables/customers.md) on `customer_id`.
```

## Provenance, trust, and lifecycle

All optional, and **their absence carries meaning** rather than being an error: an
unverified concept is distinguishable from a verified one but is never rejected.

Every timestamp is ISO 8601 with an explicit UTC offset — `2026-08-27T14:00:00Z`.

### `sources` — where it came from

```yaml
sources:
  - id: ga4-schema
    resource: https://developers.google.com/analytics/bigquery/export-schema
    title: GA4 BigQuery Export schema
    author: team:ga4-docs
    usage_count: 5000
    last_modified: 2026-05-30T00:00:00Z
usage_window: { from: 2026-08-01T00:00:00Z, to: 2026-08-31T00:00:00Z }
```

`resource` is required within each entry. It names either something a consumer can
follow (a URL, a bundle-relative path, a path into `references/`) or a scope
descriptor it cannot (`all queries in BigQuery project X`).

`id` is optional but should be present whenever the body cites the source.

The three **credibility signals** are per-source facts, not verdicts:

| Signal          | What it tells a reader                                    |
| --------------- | --------------------------------------------------------- |
| `author`        | Authority — who produced it, in the actor convention       |
| `usage_count`   | Liveness and adoption over `usage_window`                  |
| `last_modified` | Recency of the *source*, distinct from `generated.at`      |

OKF deliberately stores no credibility *score*. A score is subjective, unportable
between consumers, and goes stale; the signals do not. Read `usage_count` as
alive-versus-dead and order-of-magnitude, never as a precise ranking — a scheduled
query's executions and a human's deliberate dashboard views are not comparable
units.

### Per-claim attribution

Attribute an individual claim with a markdown footnote whose label is a
`sources[].id`:

```markdown
The `events_` table is sharded daily as `events_YYYYMMDD`.[^ga4-schema]

[^ga4-schema]: GA4 BigQuery Export schema
```

The label is the join key into `sources`; consumers resolve attribution through the
matching entry rather than by parsing the footnote text. Labels are keyed rather
than positional precisely because agents rewrite these documents constantly — a
`sources[0]` index misattributes silently the moment the list is reordered, while a
stable `id` survives it.

### `generated` and `verified`

```yaml
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-08-27T22:53:05Z }
verified:
  - { by: human:ahormati, at: 2026-08-25T09:00:00Z }
  - { by: process:finance-nightly, at: 2026-08-26T02:00:00Z }
```

`generated` records how the current content was produced; `by` is required within
it, and `at` marks the last meaningful content change. `verified` records who or
what confirmed the content against its sources. They are separate because **whoever
wrote a concept need not be whoever confirmed it**, and content can change without
re-confirmation just as facts can be re-confirmed without regeneration.

A single verifier may be written as a bare mapping without the list dash; consumers
must treat that as a one-element list.

### Trust tiers

Derived from `verified`, never stored:

| `verified`                       | Tier                 |
| -------------------------------- | -------------------- |
| absent                           | **unverified**       |
| non-`human:` actors only         | **machine-confirmed** |
| includes a `human:<id>` actor    | **human-reviewed**   |

Tiers are advisory signals, not access control.

### `status` and `stale_after`

```yaml
status: stable                       # draft | stable | deprecated
stale_after: 2026-12-31T00:00:00Z    # stale once now >= this instant
```

`draft` is not yet reviewed and possibly incomplete. `stable` is the default when
`status` is absent. `deprecated` is kept for links and history but is no longer
current.

`stale_after` is an **absolute instant, not a relative TTL**, which keeps staleness
a plain comparison that does not depend on when the document was read.

## Never forge a verification

`verified` is the field consumers key trust off. Writing
`verified: { by: human:someone }` asserts that a named person reviewed and confirmed
the content. If no such review happened, that is a fabricated sign-off attached to a
real person's identity, and it survives in git history and propagates to every
consumer that reads the bundle.

So:

- **Never write a `human:` verification** unless the user has explicitly told you
  that person reviewed it. If they say they reviewed it themselves, ask for the
  identifier to use rather than guessing at one.
- **Never write a `process:` verification** for a process that did not run.
- **`generated.by` should name what actually produced the content.** If you wrote
  it, that is an agent actor, not a human one.
- Leaving `verified` off entirely is correct and conformant. Unverified is an
  honest state; a fake verification is not.

The same care applies to `sources`: cite what the content was actually derived from.
An invented `usage_count` or a source URL nobody read makes a document look
better-grounded than it is, which is worse than a document that looks thin.

## Actors

One convention across `generated.by`, `verified[].by`, and `sources[].author`:

| Form                    | For                | Example                          |
| ----------------------- | ------------------ | -------------------------------- |
| `<producer>/<version>`  | Agents and tools   | `reference_agent/gemini-2.5-pro` |
| `human:<id>`            | A person           | `human:ahormati`                 |
| `process:<id>`          | Automated process  | `process:finance-nightly`        |

Trust classification keys off the `human:` prefix, so it must be used for
hand-authored or human-confirmed content — and must not be used for anything else.

## Cross-linking

Standard markdown links. Two forms:

- **Bundle-absolute**, beginning with `/`, resolved from the bundle root. **Prefer
  this** — it survives a document being moved within its subdirectory, which
  relative links do not.

  ```markdown
  See the [customers table](/tables/customers.md) for the join key.
  ```

- **Relative** — `./other.md`, `../computations/revenue.md`.

A link asserts a relationship; the *kind* of relationship lives in the surrounding
prose, not in the link. Consumers building a graph treat every link as a directed
edge of an untyped relationship.

**Broken links are not errors.** A link to a document that does not exist yet
represents knowledge not yet written, and consumers are required to tolerate it.
Do not delete a forward-looking link just because its target is missing.

The path-valued fields — `resource`, `sources[].resource`, `computation`,
`executor.resource`, `attester.resource` — accept an absolute URL, a bundle-relative
path beginning with `/`, or a relative path.

A **`references/`** subdirectory conventionally holds external material, run
instructions, and code as first-class bundle members. It is a convention, not a
requirement.

## index.md and log.md

### `index.md`

Enumerates a directory's contents so a reader or agent can see what exists before
opening anything — progressive disclosure.

**`index.md` carries no frontmatter**, with exactly one exception: a bundle-root
`index.md` may carry `okf_version`. Getting this wrong is the most common structural
mistake, because every other file in the bundle requires frontmatter.

```markdown
# Tables

* [Customer Orders](orders.md) - One row per completed customer order across all channels.
* [Customers](customers.md) - One row per customer account.

# Playbooks

* [Incident response](playbooks/) - Triage runbooks for on-call.
```

Entries should reuse the `description` from the linked concept's frontmatter, which
is why writing a good `description` pays off twice.

### `log.md`

A flat list of date-grouped entries, newest first, recording changes at that level:

```markdown
# Directory Update Log

## 2026-08-27
* **Update**: Added a BigQuery table reference for [Customer Orders](/tables/orders.md).
* **Creation**: Established the [Dataplex Playbook](/playbooks/dataplex.md).

## 2026-08-15
* **Initialization**: Created foundational directory structure.
```

Date headings must use `YYYY-MM-DD`. The leading bold word (`**Update**`,
`**Creation**`, `**Deprecation**`) is convention, not requirement.

## Attested Computation

A concept of `type: Attested Computation` carries not just what a value means but a
sanctioned way to *compute* it, so a consumer can confirm the blessed computation
ran rather than something an agent improvised. Provenance answers "where did this
claim come from"; attestation answers "was this number produced the way we said it
must be."

A sanctioned computation is **its own concept**, linked to from whatever needs the
value. Three reasons: `runtime` defines what `parameters` mean, so they belong in
one frontmatter; one computation often backs several consumers; and trust state
(`verified`, `stale_after`, `attester`) describes one computation, so revenue,
profit, and margin are three concepts rather than three entries in one.

### Contract fields

| Field         | Notes                                                                       |
| ------------- | --------------------------------------------------------------------------- |
| `runtime`     | **Required for this type.** `bigquery`, `postgres`, `dbt`, `python`, `Looker` |
| `parameters`  | List of `{ name, type, required }`; binding semantics follow `runtime`       |
| `computation` | Optional path to the computation file; absent ⇒ the body `# Computation` fence is it |
| `executor`    | `resource` names run instructions or code; `receipt` lists the fields a run must return |
| `attester`    | `resource` names deterministic, no-LLM code that reads a receipt and returns a verdict |

```markdown
---
type: Attested Computation
title: Revenue for fiscal year
description: Recognized revenue for a fiscal year, per Finance's definition.
status: stable
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/revenue.py
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-08-20T22:53:05Z }
stale_after: 2026-12-31T00:00:00Z
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: Revenue recognition policy
---

# Computation

    SELECT SUM(amount) AS revenue
    FROM finance.recognized_revenue
    WHERE fiscal_year = @year

The computation binds only the declared `parameters`, per the recognition
policy.[^rev-policy]

[^rev-policy]: Revenue recognition policy
```

Supply the computation either **inline** as a single fenced block under
`# Computation` — best when it is short enough to review alongside the contract — or
as a **file** via `computation`, best when it is long, generated, or already shared
with non-OKF tooling. Do not do both.

### The rule that makes attestation work

**An agent may supply only *values* for the declared `parameters`. It must never
author or edit the computation itself.** Because the attester compares the expanded,
compiled artifact the receipt carries against an independently re-derived binding, a
rewritten query, a swapped computation file, or a mutated dependency all fail the
check. A typed, parameter-only surface is what turns "did the sanctioned thing run"
into a mechanical comparison instead of a judgement call.

When documenting an Attested Computation, this cuts directly: describe and structure
the computation, never "improve" it.

### `verified` versus attestation

Both exist and they are not the same. `verified` confirms the *definition* still
matches policy — document-level, slow, stored in the bundle. Attestation confirms a
single *run* produced its value the sanctioned way — per-call, runtime, and never
stored in the bundle. A stale definition can still attest cleanly, and a
freshly-verified definition still needs attestation on every run.

## Conformance

A bundle conforms to v0.2 when:

1. Every non-reserved `.md` file has a parseable YAML frontmatter block.
2. Every frontmatter block has a non-empty `type`.
3. Every `index.md` and `log.md` present follows its structure.

That is the whole bar. Consumers **must not** reject a bundle for missing optional
frontmatter, unknown `type` values, unknown extra keys, broken cross-links, or
missing `index.md` files.

Auditing an existing bundle, this ordering matters: a missing `type` is a real
conformance failure worth fixing, while a missing `stale_after` is a normal,
conformant state. Do not report optional-field absence as an error.

Declare the target version with `okf_version: "0.2"` in the bundle-root `index.md`
frontmatter — the only place frontmatter is permitted in an index file.

## Legacy v0.1 documents

Two v0.1 constructs were superseded. When updating an older bundle, migrate them
rather than leaving both forms in place:

| v0.1                     | v0.2                | Note                                        |
| ------------------------ | ------------------- | ------------------------------------------- |
| `timestamp:`             | `generated: { by, at }` | Consumers may fall back to `timestamp` |
| Body `# Citations` list  | `sources` frontmatter   | Provenance moved into frontmatter      |

Everything else in v0.1 carries forward unchanged.

## Common mistakes

- **Putting frontmatter in `index.md`.** Only a bundle-root index may have any, and
  only `okf_version`.
- **Omitting `type`.** It is the one required key, and its absence is the only
  frontmatter-level conformance failure.
- **Using `index.md` or `log.md` as a concept name.** Both are reserved at every level.
- **Relative links where bundle-absolute would do.** Relative links break when a
  document moves; `/tables/orders.md` does not.
- **Positional citations.** Footnote labels must key into `sources[].id`, not an
  index into the list.
- **Naked timestamps.** Every OKF datetime carries an explicit UTC offset.
- **Inventing a credibility score.** OKF stores signals; the verdict is the
  consumer's to infer.
- **Fabricating `verified`.** See [Never forge a verification](#never-forge-a-verification).
- **Editing a sanctioned computation.** Fill parameters; never rewrite the query.
- **Creating a bundle nobody asked for.** See
  [Before you write anything](#before-you-write-anything).
