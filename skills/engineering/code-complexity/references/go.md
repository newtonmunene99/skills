# Go

Four complexity linters, one nesting linter, two size linters — all available
standalone and all available inside golangci-lint.

## Contents

- [The tools](#the-tools)
- [gocyclo vs cyclop](#gocyclo-vs-cyclop)
- [The golangci-lint default trap](#the-golangci-lint-default-trap)
- [Recommended golangci-lint config](#recommended-golangci-lint-config)
- [Standalone CLI usage](#standalone-cli-usage)
- [Exemptions](#exemptions)

## The tools

| Tool | Measures | golangci-lint setting | Default |
| ---- | -------- | --------------------- | ------- |
| [`gocyclo`](https://github.com/fzipp/gocyclo) | Cyclomatic, per function | `gocyclo.min-complexity` | `30` |
| [`cyclop`](https://github.com/bkielbasa/cyclop) | Cyclomatic, per function **and per package average** | `cyclop.max-complexity`, `cyclop.package-average` | `10`, `0.0` |
| [`gocognit`](https://github.com/uudashr/gocognit) | Cognitive | `gocognit.min-complexity` | `30` |
| `nestif` | Nesting depth of `if` statements | `nestif.min-complexity` | `5` |
| `funlen` | Function length | `funlen.lines`, `funlen.statements`, `funlen.ignore-comments` | `60`, `40`, `true` |
| `maintidx` | Maintainability index | `maintidx.under` | `20` |

`maintidx` runs backwards from the others: a **high** index means better
maintainability, so `under: 20` reports functions scoring below 20. Do not read it as
a complexity score.

gocyclo's counting rule is simple and worth knowing, because it explains scores that
look surprising:

```
 1 is the base complexity of a function
+1 for each 'if', 'for', 'case', '&&' or '||'
```

Note `case` counts individually — a type switch over twelve types scores 13. That is
the dispatch-table situation from [thresholds.md](thresholds.md#the-multiway-decision-exemption),
and Go has no `variant: modified` equivalent, so it has to be handled with an
exemption directive rather than a config option.

## gocyclo vs cyclop

Both compute per-function cyclomatic complexity. They are not really competitors, and
the right answer is to **layer them — but not naively.**

**Prefer `gocyclo` as the function-level gate.**

- Actively maintained: ~1,600 stars, last pushed December 2025.
- It has a **`//gocyclo:ignore` directive**, which is the mechanical implementation of
  the "or provide a written explanation" policy. Neither of the others offers a
  per-function opt-out of its own.
- Better CLI ergonomics for reports: `-over`, `-top`, `-avg`, `-ignore`.

**Add `cyclop` only for what nothing else gives you: `package-average`.**

- The package average is its stated differentiator and it is genuinely useful — it
  catches the case where no single function trips the gate but the package as a whole
  has drifted.
- Caveat worth stating when recommending it: ~56 stars, last pushed October 2024. It
  is lightly maintained relative to the others.

**Critical:** if you enable both, set `cyclop.max-complexity` **high** (say 100) so
cyclop does not re-report every function gocyclo already flagged. You want cyclop's
package-average check and nothing else from it. Two linters reporting the same
function is how a complexity gate becomes noise.

**Add `gocognit` regardless.** Neither cyclomatic tool says anything about
readability, and cognitive complexity is the only metric here that does.

## The golangci-lint default trap

Worth checking on any repo that claims to have complexity linting:

```yaml
# What you get if you enable them and configure nothing
gocyclo:  { min-complexity: 30 }   # 3x McCabe's recommendation
gocognit: { min-complexity: 30 }   # 3x
cyclop:   { max-complexity: 10 }   # 1x
```

`gocyclo` and `gocognit` default to **30**. Almost nothing in an ordinary codebase
scores above 30, so enabling them without configuration produces a clean report and
the belief that complexity is under control. Meanwhile `cyclop` in the same file
defaults to `10`. Three linters, one config, thresholds differing by 3×.

Always set these explicitly. A default that silently gates nothing is worse than no
gate, because it stops anyone looking.

## Recommended golangci-lint config

```yaml
linters:
  enable:
    - gocyclo      # cyclomatic, per function
    - gocognit     # cognitive — the readability signal
    - nestif       # nesting depth, points at the line
    - funlen       # size
    - cyclop       # package average ONLY
  settings:
    gocyclo:
      min-complexity: 15
    gocognit:
      min-complexity: 20
    nestif:
      min-complexity: 4
    funlen:
      lines: 80
      statements: 50
      ignore-comments: true
    cyclop:
      max-complexity: 100    # deliberately inert; gocyclo owns the per-function gate
      package-average: 10.0
```

Adjust the numbers to the codebase rather than adopting them wholesale — see
[thresholds.md](thresholds.md#recommended-starting-points). Confirm the settings
block shape against your golangci-lint version; the key path moved between v1 and v2.

Exclude generated code and tests from complexity linting. Table-driven Go tests trip
`funlen` constantly and refactoring them makes them worse:

```yaml
linters:
  exclusions:
    rules:
      - path: _test\.go
        linters: [funlen, gocyclo, gocognit]
```

## Standalone CLI usage

Useful for a one-off report, or when golangci-lint is not set up.

```bash
# Cyclomatic: worst offenders, ignoring tests and vendor
gocyclo -top 20 -ignore "_test|vendor/" .

# Everything over a threshold; exits 1 if the set is non-empty (CI-friendly)
gocyclo -over 15 .

# The average, as a trend line to track over time
gocyclo -avg .
```

Output is `<complexity> <package> <function> <file:line:column>`, one per line, which
pipes into `sort`/`awk` cleanly.

```bash
# Cognitive complexity, same flag vocabulary, plus JSON
gocognit -over 20 -ignore "_test" .
gocognit -json -over 20 .        # for scripting

# Package-average cyclomatic
cyclop -packageAverage 10 -skipTests ./...
```

`cyclop`'s own CLI defaults differ from its golangci-lint defaults: `-maxComplexity`
is `10`, `-packageAverage` is `0` (off), `-skipTests` is `false`.

## Exemptions

Prefer a per-function exemption with a reason to raising the global threshold.

```go
// Deliberate dispatch table: one case per supported wire format. Each branch is a
// single call, so the score reflects branch count rather than difficulty.
//gocyclo:ignore
func decode(format string, b []byte) (Message, error) {
	switch format {
	// ...
	}
}
```

Under golangci-lint, use `nolint` with a reason — the linter name is required, and
`nolintlint` can be enabled to enforce that explanations are present:

```go
//nolint:gocyclo // dispatch table; see decode() comment above
```

`gocognit` and `cyclop` have no equivalent directive of their own, which is another
reason to let `gocyclo` own the per-function gate.
