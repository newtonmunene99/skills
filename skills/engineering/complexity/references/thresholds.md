# Thresholds and policy

Picking a number, and — more importantly — deciding what happens when it is exceeded.

## Contents

- [Thresholds are not portable](#thresholds-are-not-portable)
- [What the numbers actually are](#what-the-numbers-actually-are)
- [The policy is not the number](#the-policy-is-not-the-number)
- [The multiway-decision exemption](#the-multiway-decision-exemption)
- [Recommended starting points](#recommended-starting-points)
- [What it costs to reduce complexity](#what-it-costs-to-reduce-complexity)
- [Reviewing an existing threshold](#reviewing-an-existing-threshold)

## Thresholds are not portable

Start here, because it invalidates most threshold advice on the internet.

This snippet was measured by three tools:

```java
int foo(int a, int b) {
  if (a > 17 && b < 42 && a + b < 55) {
    return 1;
  }
  return 2;
}
```

**Eclipse Metrics said 2. GMetrics said 4. SonarQube said 5.** McCabe's original
paper implies 4, since compound predicates count per condition. Nobody is
misconfigured; they simply build the control-flow graph differently.

The consequences:

- **Never quote a threshold without naming the tool it belongs to.** "Keep it under
  10" is meaningless on its own.
- **Never copy a number between tools**, including between two linters in the same
  repository. Moving from one to another means re-deriving the threshold, not
  transplanting it.
- **Never compare scores across languages.** ESLint counts optional chaining,
  default parameters and destructuring defaults; Go tooling has no equivalent
  constructs to count. Idiomatic modern TypeScript scores higher than equivalent Go
  for reasons that have nothing to do with difficulty.

## What the numbers actually are

Every commonly cited threshold, and what the study behind it actually measured:

| Number | Source | What it was |
| ------ | ------ | ----------- |
| **10** | McCabe, 1976 | The original recommendation. NIST later reported "substantial corroborating evidence" |
| **15** | NIST SP 500-235 §2.5 | Permitted **only** with experienced staff, formal design, a modern language, structured programming, code walkthroughs and a comprehensive test plan. Not a general-purpose relaxation |
| **3** | Schneidewind validation study | The threshold that best *discriminated* buggy from clean procedures — 75 of 81 clean and 21 of 31 buggy correctly classified. NIST notes this is "much less than those in common usage" |
| **12** | Digital Equipment case study | Below this, complexity showed little or no correlation with defect corrections. Above it, a definite one |
| **5–15** | Caldiera & Basili | A **band**, for identifying reusable components. Too-low complexity means reuse does not repay its cost; too-high means poor quality |

Two things worth taking from this table. First, the spread is 3 to 15, so anyone
quoting a single canonical number is oversimplifying. Second, **the band idea is
underrated** — thresholds are usually written as a ceiling, but Caldiera & Basili
needed a floor too.

## The policy is not the number

NIST's actual recommendation, verbatim, is not a threshold at all:

> "For each module, either limit cyclomatic complexity to 10 (as discussed earlier,
> an organization can substitute a similar number), **or provide a written
> explanation of why the limit was exceeded**."

The escape hatch is part of the rule. That matters because a gate with no exemption
mechanism produces one of two failures: people refactor working code into worse
shapes to satisfy it, or they disable the rule entirely and lose the signal.

A good exemption is **in the code, next to the function, and says why**:

| Ecosystem | Mechanism |
| --------- | --------- |
| Go, gocyclo | `//gocyclo:ignore` above the function |
| Go, golangci-lint | `//nolint:gocyclo // reason` |
| JS/TS | `// eslint-disable-next-line complexity -- reason` |
| Python, ruff | `# noqa: C901  # reason` |

Prefer these to raising the global threshold. Raising the ceiling silently exempts
every function; a directive exempts one and leaves a note explaining it.

When recommending a threshold, always recommend the exemption mechanism alongside it.
A bare number is half an answer.

## The multiway-decision exemption

A function that is a **single dispatch `switch`** should be exempt from the limit.
Its score is high, its branches are independent and readable in isolation, and
splitting it across a module boundary would violate ordinary design sense.

McCabe made this exemption in the original paper, with one condition worth keeping:
**it stops applying if the branches contain real complexity of their own.** A switch
of one-line returns is exempt; a switch whose cases each hold a nested loop is not.

### Do not fix this by changing the metric

NIST records what happens when someone tries. A developer, wanting multiway
decisions handled "uniformly", reported a *modified* complexity that divided
cyclomatic complexity by the number of switch branches. The result:

> the developer could take a module with complexity 90 and reduce it to "modified"
> complexity 10 simply by adding a ten-branch multiway decision statement to it that
> did nothing.

Exempt the case. Never redefine the measurement. A metric you can game by adding dead
code is worse than no metric.

The legitimate config-level version of this is ESLint's `variant: "modified"`, which
counts a whole `switch` as +1 while leaving every other construct alone. That is the
exemption expressed as a rule option rather than an arithmetic hack — see
[javascript.md](javascript.md).

## Recommended starting points

Defensible defaults, each tied to its tool. Treat them as a place to begin measuring
from, not as findings.

| Tool | Setting | Suggested | Tool default | Note |
| ---- | ------- | --------- | ------------ | ---- |
| ESLint | `complexity` `max` | **10–15** | `20` | Default is double McCabe |
| ESLint | `max-depth` | **4** | `4` | Default is already sensible |
| ESLint | `sonarjs/cognitive-complexity` | **15** | `15` | The readability gate |
| oxlint | `eslint/complexity` `max` | **10–15** | `20` | Restriction category, opt in |
| Go | `gocyclo` `min-complexity` | **10–15** | `30` | Default gates nothing |
| Go | `gocognit` `min-complexity` | **15–20** | `30` | Default gates nothing |
| Go | `nestif` `min-complexity` | **4–5** | `5` | Default is sensible |
| Python | `lint.mccabe.max-complexity` | **10** | `10` | Default is already McCabe's number |
| Python | `lint.pylint.max-nested-blocks` | **4–5** | `5` | The nesting gate |

**Introduce a gate on new code first.** Turning a threshold on across an existing
repository produces a wall of findings that gets the rule disabled within a week.
Gate the diff, let the existing violations sit behind an ignore list, and burn them
down deliberately.

## What it costs to reduce complexity

NIST §9.3 is unusually honest about this, and it is the section people skip.

**Removing a control dependency can introduce unstructured logic.** Their worked
example takes a well-structured function with CC 4 and rewrites it to CC 3 — but the
new version has a loop with two exit points. On the numbers it improved. Structurally
it got worse. For a small function most people would still take the trade; for a
larger one the original is the better code, and the metric cannot tell you that.

**Splitting a function can destroy cohesion.** Extracting a piece to satisfy a
threshold risks introducing control coupling between the halves. Their test for
whether a split is legitimate is memorable: if the extracted function needs local
variables passed by reference, and the only name you can think of for it is
`more_printwords`, the split is not justified.

**Some complexity is not reducible at all.** A function's *realizable* complexity —
the number of paths any input can actually exercise — can be lower than its
cyclomatic complexity, because data dependencies between decisions make some paths
impossible. Computing it in general reduces to the halting problem. When a basis set
cannot be exercised, the answer is to document the dependency, not to keep
refactoring.

The practical upshot: **a refactor should be justified by the code reading better,
with the score as corroboration.** A refactor justified only by the score moving is
how complexity limits earn their bad reputation.

## Reviewing an existing threshold

When a project already has one configured, ask in this order:

1. **Which tool is it, and does the number match that tool's counting?** A `max: 20`
   copied from a blog post about a different linter is not a considered decision.
2. **Is it doing anything?** golangci-lint's `min-complexity: 30` and ESLint's
   `max: 20` both pass almost everything. A gate that never fires reads as
   compliance without providing any.
3. **Is there an exemption mechanism, and is it used with reasons?** Bare `nolint`
   with no comment is the same as no gate, minus the honesty.
4. **Is anything measuring readability?** If cyclomatic complexity is the only metric
   configured, the project is gating test effort and calling it maintainability.
