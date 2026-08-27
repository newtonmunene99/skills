# The metrics

What each metric actually measures, what question it answers, and where it lies.

## Contents

- [Which metric answers which question](#which-metric-answers-which-question)
- [Cyclomatic complexity](#cyclomatic-complexity)
- [Where cyclomatic complexity fails](#where-cyclomatic-complexity-fails)
- [Cognitive complexity](#cognitive-complexity)
- [Nesting depth](#nesting-depth)
- [Essential complexity](#essential-complexity)
- [Size](#size)
- [The empirical record](#the-empirical-record)

## Which metric answers which question

| Question | Metric | Available in |
| -------- | ------ | ------------ |
| How many tests will this need? | **Cyclomatic** | Every ecosystem |
| Will a reader struggle with this? | **Cognitive**, **nesting depth** | JS (SonarJS), Go (gocognit, nestif), Python (PLR1702 for nesting) |
| Is the control flow tangled or merely branchy? | **Essential** | Nothing here — see below |
| Is this function simply too big? | **Length**, statement count, parameter count | Every ecosystem |

Reaching for the wrong one is the most common failure. Most complexity linting is
cyclomatic complexity used to answer the *second* question, which it cannot.

## Cyclomatic complexity

Thomas McCabe, 1976. Counts the **linearly independent paths** through a function's
control-flow graph.

```
M = E − N + 2P        edges, nodes, connected components
M = E − N + P         when every exit is wired back to the entry
```

For a single function `P = 1`, so `M = E − N + 2`. In practice everyone uses the
shortcut: **decision points + 1**.

What counts as a decision point is where tools start to disagree. Compound
predicates count **per condition** — `if (a && b)` is two decision points, not one,
because at machine level it is two nested ifs. Some tools implement that, some don't.

### What it is genuinely good for

**Sizing test effort.** The real relationship is a sandwich:

```
branch coverage  ≤  cyclomatic complexity  ≤  number of paths
```

CC is an *upper* bound on the tests needed for full branch coverage and a *lower*
bound on the number of paths. "CC equals the number of tests you need" is wrong in
both directions; it is a practical middle target, not an identity.

The strongest evidence for it is NIST's blackjack experiment (SP 500-235, Appendix
B). Testing to a basis set of CC paths detected a planted bug in **97 of 100** trials
versus branch coverage's 85. Restricted to only the tests that increased coverage,
basis-path testing held at **96** while branch coverage collapsed to **53** — so the
criterion itself was doing the work, not merely the extra test count.

There is a second, subtler use: **CC is predictable under change.** Add four
decisions and it goes up by exactly four. That makes it a reasonable trend line on a
function's history, which is different from a threshold.

## Where cyclomatic complexity fails

Two counterexamples settle it. Both come from CQSE's
["McCabe's Cyclomatic Complexity and Why We Don't Use It"](https://www.cqse.eu/en/news/blog/mccabe-cyclomatic-complexity/).

### A dispatch table scores high and reads fine

```java
String getMonthName(int month) {
  switch (month) {
    case 0: return "January";
    // ... ten more
    case 11: return "December";
    default: throw new IllegalArgumentException();
  }
}
```

**Cyclomatic complexity 14**, far past any normal threshold. It also needs no
thought to read or change. Every branch is independent, uniform, and verifiable at a
glance. The score is honest about testing — you really would want a case per month —
and says nothing true about difficulty.

### Two functions score the same and are nothing alike

```java
// Cyclomatic complexity 5
String getWeight(int i) {
  if (i <= 0)  return "no weight";
  if (i < 10)  return "light";
  if (i < 20)  return "medium";
  if (i < 30)  return "heavy";
  return "very heavy";
}

// Cyclomatic complexity 5
int sumOfNonPrimes(int limit) {
  int sum = 0;
  OUTER: for (int i = 0; i < limit; ++i) {
    if (i <= 2) continue;
    for (int j = 2; j < i; ++j) {
      if (i % j == 0) continue OUTER;
    }
    sum += i;
  }
  return sum;
}
```

Identical scores. A flat guard-clause ladder read top to bottom, versus a nested loop
with a labelled `continue` jumping out of an inner scope. Cyclomatic complexity
cannot tell them apart because it counts branches and is blind to **nesting** — and
nesting is most of what makes code hard to hold in your head.

## Cognitive complexity

SonarSource designed cognitive complexity specifically to fix the failure above. It
keeps the idea of counting control flow but adds two things CC lacks:

- **Nesting penalties.** A construct costs more the deeper it sits.
- **Shorthand credit.** Structures that collapse many branches into one readable
  shape — a `switch` — cost +1 total rather than +1 per case.

That second rule alone resolves `getMonthName`: cognitive complexity **1**, against
cyclomatic **14**.

### The worked comparison

From [gocognit](https://github.com/uudashr/gocognit)'s README, the same
labelled-`continue` shape as CQSE's counterexample:

```go
func SumOfPrimes(max int) int {
    var total int
OUT:
    for i := 1; i < max; i++ {          // +1
        for j := 2; j < i; j++ {        // +2  (nesting = 1)
            if i%j == 0 {               // +3  (nesting = 2)
                continue OUT            // +1
            }
        }
        total += i
    }
    return total
}
// Cyclomatic complexity = 4
// Cognitive complexity  = 7
```

Cyclomatic says 4 — less than the flat if-ladder above. Cognitive says 7, and ranks
it as the harder function, which matches every reader's intuition. This is the metric
to reach for when the question is "will someone struggle with this?"

### The scoring rules

Increments for: `if` / `else if` / `else`; `switch`; loops; a labelled `break`,
`continue` or `goto`; each *sequence* of binary logical operators; and each method
in a recursion cycle. Nesting level is incremented by conditionals, switches, loops,
and function literals or lambdas — and conditionals, switches and loops receive an
increment proportional to how deep they already sit.

Note what is **not** penalised: an `else if` chain costs +1 each rather than nesting,
and a sequence of `&&` counts once rather than per operator. Both are deliberate —
they read as one decision.

## Nesting depth

The maximum number of control structures nested inside one another. `sumOfNonPrimes`
above has depth 3.

Crude next to cognitive complexity, and worth tracking anyway for one practical
reason CQSE makes well: **it points at a line.** Cyclomatic complexity can only
label an entire function "too complex" and leave the developer to find the part that
matters. Nesting depth identifies the exact statement that is buried, which is
actionable in a way a function-level score is not.

Nesting also expands the context a reader has to hold to change a single line, which
is the mechanism behind why deeply nested code feels hard.

## Essential complexity

NIST SP 500-235 §10. Take the control-flow graph and iteratively collapse every
structured programming primitive — sequence, selection, iteration — from the deepest
nesting outward. Whatever cannot be collapsed is an irreducible knot. Essential
complexity `ev(G)` is the cyclomatic complexity of what remains.

- **`ev(G) = 1`** for any well-structured function, no matter how branchy.
- **`ev(G) > 1`** means genuinely unstructured control flow.
- **`ev(G)` can never equal 2.** After sequential nodes collapse, the only graphs
  with CC 2 are structured primitives, which then reduce to 1. If a tool ever reports
  2, the tool is wrong — a free correctness check on any implementation.

It is computed from the flow graph rather than the syntax, so a `goto` costs nothing
unless it is actually used to build something unstructured.

### Why it matters more than it gets used

Cyclomatic complexity grows **predictably**: four new decisions, four more points.
Essential complexity can **explode in one edit**. NIST's example replaces a single
statement with a `goto` and takes a function from `ev(G) = 1` to `ev(G) = 12` — from
perfectly structured to completely tangled, in a diff that looks like a one-line
change. It will not be obvious to the author or the reviewer.

That makes essential complexity the right thing to gate *maintenance changes* on,
where cyclomatic complexity is the right thing to gate *size* on.

**Nothing in the JS, Go, or Python tooling covered here implements it.** Say so
rather than implying it is available. Cognitive complexity is the closest practical
substitute, since it also penalises the jump-based control flow that drives `ev(G)`
above 1 — but it is not the same measurement, and it will not catch every case.

## Size

The metrics nobody respects and everybody should track:

- **Lines per function** — crude, but the least gameable signal that a function is
  doing too much.
- **Statement count** — length without the comment and blank-line noise.
- **Parameter count** — a proxy for how much context the function needs to work.
- **Local variable count** — a proxy for how much state a reader has to track.

They earn their place because the alternative interpretation of a high complexity
score is often just "this function is long," and it is worth knowing which one you
are looking at.

## The empirical record

Read honestly, because the evidence is weaker than the metric's reputation.

**Where the correlation looks strong.** Henry, Kafura and Harris found a **.96**
correlation between CC and error count on UNIX. Ward, at HP, found **.8** against
error density and concluded complexity limitation was a significant quality factor.

**Where it looks thin.** Walsh's AEGIS study, 276 modules, found error rates of
**4.6 versus 5.6 per 100 source statements** on either side of CC 10 — a real
difference, but a slim one to hang a hard gate on. Digital Equipment found the
correlation held **only above CC 12**, with little or none below it, suggesting other
factors dominate when complexity is low.

**The problem underneath all of it.** Complexity correlates strongly with **lines of
code**. Les Hatton claims it has the same predictive power as LOC and nothing more;
Fenton and Neil question the metric's usefulness on the same grounds. Studies that
control for size are inconclusive.

This tension is visible *inside* the primary source. NIST §3.1 insists complexity and
size are independent, citing a 282-line function with CC 1 and a 30-line function
with CC 28. But its own Appendix A carries Gill & Kemerer — 150,000 lines, 834
modules — confirming the high CC↔LOC correlation, which is exactly what motivated
their **cyclomatic density** (CC divided by non-comment lines) as a way to factor
size back out. Density was found to be a statistically significant predictor of
maintenance productivity where raw CC was not.

**What follows for practice.** Reducing cyclomatic complexity is **not proven** to
reduce defects. Treat a high score as a prompt to look at the function, not as
evidence that it is broken — and when a score is high mostly because the function is
long, say that rather than dressing it up as a complexity finding.

Safety-critical work is the exception on process grounds rather than evidential ones:
ISO 26262 requires coding guidelines that monitor and aim to reduce complexity, with
extra verification where it is high.
