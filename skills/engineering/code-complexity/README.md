# code-complexity

An [Agent Skill](https://skills.sh/) for measuring and interpreting code complexity,
and for choosing the right linter and threshold for the language at hand.

## What it covers

- **The metrics** — cyclomatic, cognitive, nesting depth, essential complexity, and
  size, with what each is valid for and where each lies
- **Thresholds and policy** — where 10, 15, 3 and the 5–15 band each come from, why
  a number is meaningless without naming the tool, and the written-exemption rule
- **JavaScript / TypeScript** — ESLint `complexity` and its companions, the `variant`
  option, oxlint, and SonarJS cognitive complexity
- **Go** — gocyclo, cyclop, gocognit, nestif, funlen and maintidx, plus how to layer
  them in golangci-lint without double-reporting
- **Python** — ruff `C901` and the `PLR` refactor family
- **A throwaway HTML report** — one self-contained page, generated whenever a real
  scan produced real numbers

## The report

Numbers in terminal scrollback cannot be sorted, shared, or explored. So a review
that actually ran a tool also writes `./complexity-report.html`: a single file, no
framework and no server, that opens by double-click and survives being emailed.

It has **live threshold sliders** — drag one and the findings re-filter while the
counts update, so "what should we set this to?" becomes something you can see rather
than argue about. Findings are grouped by **verdict** rather than ranked by score:
*needs attention*, *expected* (dispatch tables, where a high score is honest and
harmless), *long, not complex*, and *judged fine*. That classification is the part a
linter cannot do, and it is the reason the page is worth generating.

The page is throwaway by design, marked as such, and meant to be regenerated rather
than committed.

## The premise

> **Cyclomatic complexity is a good estimator of test effort and a poor proxy for
> readability.**

Both the metric's authors and its critics agree on the first half. Most complexity
linting in the wild acts as though the second half were false: a single threshold
wired to CI and treated as a maintainability gate.

A twelve-case dispatch `switch` scores 14 and is trivially readable. Two functions
can score 5 apiece — a flat guard-clause ladder and a nested loop with a labelled
`continue` — and be nothing alike to read. So the skill reads more than one number,
and knows which number answers which question.

It reports and recommends. It does not edit source files or write linter config.

## Some things it knows that are easy to get wrong

- **ESLint's `complexity` defaults to `max: 20`**, double McCabe's recommendation.
- **golangci-lint's `gocyclo` and `gocognit` default to `min-complexity: 30`**, triple
  it — so enabling them unconfigured produces a clean report and false confidence.
  `cyclop` in the same file defaults to `10`.
- **Ruff's `C901` is not in the default rule set.** A tuned `[tool.ruff.lint.mccabe]`
  block with no matching `extend-select` entry configures a gate that never runs.
- **ESLint's `variant: "modified"`** counts a whole `switch` as +1 — the
  multiway-decision exemption as a config flag, and the fix for dispatch tables
  tripping the rule.
- **The same three-condition `if` scores 2, 4 or 5** depending on the tool, which is
  why thresholds are not portable.

## Install

```bash
npx skills add newtonmunene99/skills --skill code-complexity
```

### Scope

| Scope   | Flag      | Location                                  | Use case                     |
| ------- | --------- | ----------------------------------------- | ---------------------------- |
| Project | (default) | `./.agents/skills/` or agent-specific dir | Share with the whole team    |
| Global  | `-g`      | `~/.cursor/skills/` etc.                  | Use across all your projects |

Supported agents include **Cursor**, **Codex**, **Claude Code**, **OpenCode**,
**Windsurf**, and [others](https://github.com/vercel-labs/skills#supported-agents).

## Skill structure

- **SKILL.md** — the validity envelope, workflow, reference routing, quick cues, anti-patterns
- **references/metrics.md** — what each metric measures, worked counterexamples, the empirical record
- **references/thresholds.md** — the numbers and their provenance, exemption policy, the cost of reducing complexity
- **references/javascript.md** — ESLint, oxlint, SonarJS
- **references/go.md** — gocyclo, cyclop, gocognit, nestif, funlen, maintidx, golangci-lint layering
- **references/python.md** — ruff `C901` and the `PLR` family
- **references/report.md** — when to generate the HTML report, its data shape, and the verdict taxonomy
- **assets/report-template.html** — the self-contained report page, filled in with a JSON blob
- **agents/openai.yaml** — optional Codex/Copilot display metadata (not read by the model)
- **evals/** — 4 eval prompts with expectations, and the harness to run them

## Sources

- Thomas J. McCabe, *A Complexity Measure*, IEEE TSE, 1976
- Arthur H. Watson & Thomas J. McCabe, [*Structured Testing: A Testing Methodology
  Using the Cyclomatic Complexity Metric*](https://www.mccabe.com/pdf/mccabe-nist235r.pdf),
  NIST Special Publication 500-235, 1996
- Benjamin Hummel, [*McCabe's Cyclomatic Complexity and Why We Don't Use
  It*](https://www.cqse.eu/en/news/blog/mccabe-cyclomatic-complexity/), CQSE, 2014
- G. Ann Campbell, [*Cognitive Complexity*](https://www.sonarsource.com/resources/cognitive-complexity/),
  SonarSource

## Related skills

- **git-code-review** — reviews a diff for correctness and guideline violations. This
  skill answers a different question and deliberately stays out of that one's way.
- **go-engineering**, **python-engineering** — idiomatic style and performance for
  those languages, where this one covers only complexity.

## License

Apache-2.0. See [LICENSE](LICENSE).
