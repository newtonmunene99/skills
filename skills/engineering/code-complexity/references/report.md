# The HTML report

A complexity review produces numbers, and numbers in terminal scrollback are close to
useless — they cannot be sorted, shared, or explored. So a review that ran a real
tool and has real per-function scores also writes a **single self-contained HTML
page**: throwaway, double-clickable, and readable by someone who is never going to
open a terminal.

## Contents

- [When to generate one](#when-to-generate-one)
- [Where it goes](#where-it-goes)
- [Using the template](#using-the-template)
- [Every section is optional](#every-section-is-optional)
- [The data shape](#the-data-shape)
- [Verdicts are the point](#verdicts-are-the-point)
- [The ratio column](#the-ratio-column)
- [Score attribution](#score-attribution)
- [Deep dives](#deep-dives)
- [The backlog](#the-backlog)
- [Picking the initial thresholds](#picking-the-initial-thresholds)
- [Writing good notes](#writing-good-notes)
- [Rules](#rules)

## When to generate one

**Whenever the review has real findings** — meaning a tool actually ran and produced
per-function scores. That is the trigger; no need to ask first.

Skip it when there is nothing to put in it:

- The question was conceptual ("what threshold should we set?", "what does cognitive
  complexity measure?") and no code was scanned.
- No linter is installed and none could be run, so the numbers would be guesses.
- The review covered a handful of functions the user is already looking at.

When you do write one, **keep the terminal answer short** and point at the page. The
page carries the table; the reply carries the verdict and the recommendation. Saying
it twice wastes the reader's attention.

## Where it goes

The file is always named `complexity-report.html`. Where it lands is the question,
and the answer is wherever the reader will go looking for it. Resolve in this order
and stop at the first match:

1. **A path the user named.** Explicit beats inferred. Keep the filename they gave,
   if they gave one.
2. **The root of what was scanned**, when that is a single directory and it is not
   the working directory. Asked to review `~/work/other-repo`, or `packages/api`
   inside the current one, the report belongs at the top of that scope — next to the
   code it describes.
3. **The working directory.** The default: the scan covered the cwd itself, or spread
   across several directories with no single root to sit at the top of.

The trap is rule 2 sliding into "the enclosing repository root". It does not. A scan
of `packages/api` writes to `packages/api/`, not to the repo root three levels up.
The repo root is only ever right when it *is* the scanned root or *is* the working
directory — never because it is the repo root.

Once resolved, write it with a relative path where you can (`./complexity-report.html`
in the common case) rather than an absolute one you assembled by hand.

Say where it went in the reply, as a path the user can click.

If the report lands inside a git repository, check `.gitignore`. If
`complexity-report.html` is not covered, **tell the user to add it** — do not edit
`.gitignore` yourself, since this skill does not modify project files. One line in
the reply is enough:

> Wrote `complexity-report.html`. Worth adding to `.gitignore` — it's throwaway and
> regenerating is cheap.

Regenerate it in place on a later review rather than accumulating timestamped copies.

## Using the template

Do not author the HTML from scratch. `assets/report-template.html` is a complete,
working page: one file, no framework, no CDN, no server, dark and light themes, and
live threshold sliders. Read it, build the data object, and substitute.

```
1. Read assets/report-template.html
2. Replace the single placeholder __FINDINGS_JSON__ with your JSON
3. Write the result to complexity-report.html, at the location resolved above
```

The placeholder sits inside `<script type="application/json" id="data">`. Emit
compact JSON. If any string could contain `</script>` — vanishingly unlikely for file
paths and function names — escape the forward slash as `<\/script>`.

Nothing else in the template needs changing. If a report seems to need a structural
change, that is a signal to improve the template in the skill rather than to hand-roll
a one-off page.

## Every section is optional

The template renders eleven sections, and **each one disappears when its data is
absent**. That is deliberate: the same file serves a two-minute triage and a full
repo audit.

| Data present | Section rendered |
| ------------ | ---------------- |
| always | masthead, footer |
| `grade` | grade badge |
| `stats` | four-cell summary strip |
| `distribution` | histogram |
| `insight` | "read this first" callout |
| `explainers` | two-numbers explainer |
| `specimens` | paired code examples |
| `bands` | bands-and-verdicts table |
| `metrics` + `findings` | threshold sliders + hot spots table |
| `deepDives` | per-function deep dives |
| `backlog` | prioritised work queue |

Scale the report to what you actually know:

- **Quick triage** — masthead, `metrics`, `findings`. Nothing else.
- **Standard review** — add `stats`, `insight`, `bands`.
- **Full audit** — everything, including one or two `deepDives`.

Do not pad. A histogram over six functions or a backlog of one item is worse than
omitting the section, because it implies a breadth of analysis that did not happen.

**Repo-wide sections need repo-wide data.** `stats` and `distribution` describe every
function, not just the flagged ones — so they require running the tool *without* an
`-over` filter and aggregating. If you only have the over-threshold list, omit both
rather than computing a median of the outliers.

## The data shape

Only `metrics` and `findings` are needed for a usable page. Everything else is additive.

```json
{
  "repo": "orchard-api",
  "ref": "main@4f2ae91",
  "eyebrow": "Code health · sprint 34",
  "headline": "Where orchard-api is hardest to read",
  "lede": "84 files, 660 functions… Thirty-nine sit past the refactor line.",
  "grade": { "letter": "C+", "caption": "Grade" },
  "tools": [{ "name": "gocyclo", "setting": "-over 10" }],

  "stats": [
    { "label": "Cyclomatic", "value": "4,812", "sub": "med 4 · p95 18" },
    { "label": "Needs attention", "value": "39", "sub": "5.9% of functions", "tone": "attention" }
  ],

  "distribution": {
    "title": "Functions by cognitive complexity",
    "caption": "The long tail is short.",
    "buckets": [
      { "label": "0–5", "count": 412 },
      { "label": "26–40", "count": 9, "tone": "attention" }
    ]
  },

  "insight": { "label": "Read this first", "lead": "…", "body": "…" },

  "explainers": [
    { "term": "cyclomatic", "body": "Counts the independent paths…",
      "answers": "how many tests does this need?" }
  ],

  "specimens": [
    { "verdict": "expected", "label": "high cyc, low cog", "code": "switch ev.Kind {…",
      "note": "Sixteen paths, flat as a table. Leave it alone." }
  ],

  "bands": [
    { "verdict": "expected", "cyc": "any", "cog": "≤ 10", "action": "Flat. Exempt." }
  ],
  "bandsNote": "A function takes the worse of its two bands unless…",

  "metrics": [
    { "key": "cyclomatic", "short": "cyc", "label": "Cyclomatic", "threshold": 10, "max": 40, "note": "sizes test effort" },
    { "key": "cognitive",  "short": "cog", "label": "Cognitive",  "threshold": 10, "max": 50, "note": "tracks readability" }
  ],
  "findings": [
    { "file": "billing/reconcile.go", "line": 41, "name": "Reconcile", "lang": "Go",
      "scores": { "cyclomatic": 14, "cognitive": 29 }, "verdict": "attention" }
  ],
  "hotspotsFootnote": "routeRequest is the counter-example worth remembering…",

  "deepDives": [{
    "verdict": "attention", "file": "billing/reconcile.go", "line": 41, "lang": "Go",
    "name": "(*OrderService).Reconcile",
    "deltas": [{ "metric": "cog", "from": 29, "to": 4 }],
    "problem": "One loop body carries four unrelated jobs…",
    "before": { "label": "cog 29", "code": "func …" },
    "after":  { "label": "cog 4",  "code": "func …" },
    "fix": "Give each job its own function…",
    "attribution": {
      "title": "Where the 29 points came from",
      "rows": [
        { "construct": "for _, o := range batch", "depth": 0, "base": 1, "nesting": 0 },
        { "construct": "if o.Status == StatusPaid", "depth": 1, "base": 1, "nesting": 1 }
      ],
      "note": "else if and boolean sequences take no nesting penalty…"
    }
  }],

  "backlog": {
    "note": "Ordered by cognitive points removed per hour of work.",
    "items": [
      { "title": "Split Reconcile into per-order stages", "file": "billing/reconcile.go",
        "effort": "~2h", "caveat": "needs new tests", "from": 29, "to": 4 }
    ]
  }
}
```

Notes on the fields:

- **`headline`** — a thesis, not a label. *"Where orchard-api is hardest to read"*
  tells the reader what they are about to learn; *"Complexity report"* does not.
- **`ref`** — the branch and short SHA. A throwaway report with no provenance is
  impossible to trust a week later.
- **`metrics`** — one entry per metric you actually measured. The **second** metric
  is the sort key for the hot spots table (cognitive, when both are present), because
  reading cost is what the ordering should express. `max` sets the slider range.
- **`tone`** — `attention`, `long` or `expected` on a stat or histogram bucket, to
  colour it. Use sparingly; if everything is toned, nothing reads as urgent.
- **`scores`** — omit a metric rather than writing `0` or `null`. A missing score
  renders an empty cell, which reads correctly as "not measured".
- **`grade`** — see the caution under [Rules](#rules).

## Verdicts are the point

Every finding carries one of four verdicts. **This classification is the whole value
of the report** — without it the page is a prettier version of the linter's own
output, and the linter was already free.

| Verdict | Meaning |
| ------- | ------- |
| `attention` | High on the metrics that track readability. Genuinely worth looking at |
| `expected` | Dispatch tables, table-driven code, exhaustive switches. High score, readable code — exempt rather than refactor |
| `long` | The score is mostly a function of size. Splitting helps only if the pieces are cohesive |
| `ok` | Over the threshold, judged fine for a reason worth recording |

The classification is a judgement call and it is the part a linter cannot do. Resist
putting everything in `attention` — a report where every finding needs attention is a
report nobody acts on, and it is almost never true.

The `bands` table is where the taxonomy gets explained — once, with its numeric
ranges and the action each verdict implies. Include it whenever the report carries
more than a handful of findings, so a reader can audit the classification rather than
taking it on trust.

## The ratio column

The hot spots table computes **cognitive ÷ cyclomatic** for every row. The template
does this itself; do not put it in the data.

| Ratio | Reading |
| ----- | ------- |
| **≥ 1.6** | Nesting is the problem. Few paths, buried deep. Flatten it |
| 0.9 – 1.6 | Branch count and reading cost roughly agree. Ordinary |
| **≤ 0.9** | Wide but flat. A dispatch table or a long guard sequence. Usually exempt |

This single derived number carries the skill's whole thesis per function, and it is
the fastest way for a reader to sort a table they did not generate. High ratios are
tinted with `--attention`, low ones with `--expected`, automatically.

It is also the honest way to surface the counter-example: the function with the
highest cyclomatic score in the repo often has the *lowest* ratio, and saying so in
`hotspotsFootnote` teaches the reader more than the table alone.

## Score attribution

The strongest section in the report, and the one that turns cognitive complexity from
a mystical number into something a reader can argue with. Each row is one scoring
construct:

| Column | Meaning |
| ------ | ------- |
| `construct` | The line, abbreviated — `if o.Ledger == nil` |
| `depth` | Nesting level at that point. `null` renders `—` for constructs that take no nesting penalty |
| `base` | The structural increment, almost always `+1` |
| `nesting` | The nesting penalty, equal to the depth |
| running / load | Computed by the template — do not supply them |

Derive the rows from the cognitive complexity rules in
[metrics.md](metrics.md#the-scoring-rules): increments for conditionals, switches,
loops, labelled jumps and boolean sequences; nesting penalties from conditionals,
switches, loops and function literals. Rows where a construct takes a base point but
no nesting penalty — `else if`, a `&&` sequence — are worth including precisely
because they show the reader what is *cheap*, which is how the penalty structure
becomes intuitive.

Close with a `note` that does the arithmetic in words: *"Ten constructs, ten base
points, nineteen points of nesting penalty."* That sentence is usually the moment the
metric clicks.

## Deep dives

One or two per report, for the functions at the top of the backlog. More than three
and nobody reads them.

Each has a fixed shape, and every part earns its place:

1. **Verdict pill, location, language** — orientation.
2. **`deltas`** — `cog 29 → 4`. The projected outcome, stated before the argument for
   it. A delta of 10 or more is highlighted automatically.
3. **`problem`** — what is actually wrong, in prose. Name the mechanism, not the
   score: *"one loop body carries four unrelated jobs, and each is reached by
   narrowing an if inside the previous one."*
4. **`before` / `after` code** — the two panels side by side, each labelled with its
   score. Keep them genuinely comparable; do not sneak unrelated improvements into
   the "after".
5. **`fix`** — why the refactor works, in one paragraph. The useful sentence is
   usually *"nothing about the logic changes; the nesting penalty disappears because
   every branch now sits at depth one."*
6. **`attribution`** — the table above.

**The `after` code is a proposal, not a change you made.** This skill does not edit
source. Write it as the shape of the fix, and say so if there is any ambiguity.

Be honest about the projected score. If you cannot compute the "after" number with
the same rules you used for the "before", leave the delta out rather than guessing —
a fabricated improvement is the fastest way to lose the reader's trust in the rest of
the page.

## The backlog

The section a reader acts on, so it is ordered by **cognitive points removed per hour
of work** rather than by raw score. A 29-point function that takes two hours outranks
a 27-point one that takes three.

Each item carries a title written as an instruction (*"Invert the session guards and
return early"*, not *"session.go is complex"*), the file, an effort estimate, and a
caveat — whether tests exist, whether behaviour changes.

**The caveat is the most useful field and the easiest to skip.** "No behaviour
change" and "needs new tests" are what let someone pick an item that fits the time
they actually have. Estimates are rough by nature; say `~1h` rather than implying
precision you do not have.

## Picking the initial thresholds

The sliders open at `metrics[].threshold`, and that opening position decides what the
reader sees first.

Set each threshold at **the value that produced these findings** — the project's
configured limit if it has one, or the value you would recommend if it does not. Do
not set it above the scores you are reporting: findings below the slider are filtered
out, and the page opens looking emptier than the data warrants.

If the project has no configured limit and you are recommending one, open the slider
at your recommendation. The reader immediately sees how many functions that number
would flag, which is the argument for or against it made concrete.

## Writing good notes

The `note` on each finding is what turns a row into a finding. One or two sentences,
saying what *kind* of complexity this is:

- **Good:** "Nested loop with a labelled continue. Cyclomatic is modest; cognitive is
  not, and nesting drives most of it."
- **Good:** "Dispatch table, one case per wire format. Score tracks branch count, not
  difficulty."
- **Useless:** "High cyclomatic complexity." The chip already said that.

Where a finding is `expected` or `ok`, the note should say **why it is exempt**,
because that is the sentence the reader will paste into a `//nolint` comment.

## Rules

1. **One file, nothing external.** No CDN, no framework, no bundler, no server, no
   web fonts. It has to survive being emailed and opened by double-click.
2. **Marked throwaway, and actually throwaway.** The template carries the badge.
   Regenerate rather than edit; never commit it.
3. **Never let it be the only output.** A user who reads only the terminal reply
   should still get the verdict and the recommendation.
4. **No CI wiring.** This is a page for a human to look at once, not a quality gate.
   The gate is the linter config; recommend that instead.
5. **Do not edit the project to accommodate it.** No `.gitignore` edits, no npm
   scripts, no Makefile targets. Say what would help and let the user decide.
6. **Do not fabricate scores.** Every number on the page comes from a tool that
   actually ran. If a metric could not be measured, leave it out — a page of
   confident estimates is worse than a smaller honest one. This applies hardest to
   projected "after" scores and effort estimates, which are the easiest to invent.
7. **Scale the report to the analysis.** Omitted sections cost nothing; padded ones
   imply work that did not happen. See
   [Every section is optional](#every-section-is-optional).

### On the grade badge

`grade` puts a single letter at the top of a report whose entire argument is that one
number cannot describe complexity. That tension is real, so use it carefully:

- **Derive it from concentration and the share of functions in the attention band**,
  never from mean cyclomatic complexity. The latter is mostly a measure of how long
  the repo's functions are.
- **Omit it entirely** for a scoped review, a single package, or any report without
  repo-wide data behind it. A grade implies you looked at everything.
- Treat it as a summary for someone who will read no further, sitting directly above
  a report that immediately unpacks it — not as a score to track over time, and never
  as a gate.

When in doubt, leave it out. The stat strip already says how many functions need
attention, which is more useful and less arguable than a letter.
