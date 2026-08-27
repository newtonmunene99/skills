---
name: code-complexity
description: >-
  Measures and interprets code complexity, then recommends the right linter and
  threshold for the language. Covers cyclomatic complexity, cognitive
  complexity, nesting depth, essential complexity and size metrics, plus the
  concrete tooling — ESLint and oxlint for JS/TS, gocyclo, cyclop, gocognit and
  golangci-lint for Go, ruff for Python. Use when asked to review complexity,
  find complex or hard-to-maintain functions, choose or configure a complexity
  linter, decide what threshold to set, interpret a complexity report, or judge
  whether a high-scoring function actually needs refactoring.
disable-model-invocation: false
compatibility: >-
  Runs the project's own linters when installed (ESLint or oxlint, gocyclo,
  gocognit, golangci-lint, ruff) and recommends configuration when not.
  Judgement-heavy: the value is in classifying findings rather than counting
  them, so it benefits from a high-reasoning model.
model: best
effort: xhigh
---

# Code Complexity

## Overview

The single most useful thing to know about cyclomatic complexity is what it is
**not** for:

> **Cyclomatic complexity is a good estimator of test effort and a poor proxy for
> readability.**

Both the metric's own authors and its sharpest critics agree on the first half. The
second half is where most complexity linting goes wrong — a single CC threshold
wired to CI and treated as a readability gate. A twelve-case dispatch `switch` scores
14 and is trivially readable; two functions can score 5 apiece and be wildly
different to understand.

So this skill reads more than one number. **Cyclomatic** complexity sizes testing.
**Cognitive** complexity and **nesting depth** speak to readability. **Length** is
crude but honest. Together they say something CC alone cannot.

This skill reports and recommends. It **does not edit source files or write linter
config** — proposing a threshold is the deliverable; applying it is a separate
request. The one file it does write is a throwaway HTML report of its own findings,
covered in step 5.

## Workflow

1. **Detect what is already there.** Look for `eslint.config.js` / `.eslintrc*`,
   `.oxlintrc.json`, `.golangci.yml`, `pyproject.toml` / `ruff.toml`. An existing
   threshold is a decision someone made; understand it before proposing another.
2. **Run the tool if it is installed**, scoped to the code in question. Real numbers
   beat estimates, and every tool counts differently enough that guessing is unsafe.
   If nothing is installed, say what you would run rather than eyeballing a score.
3. **Interpret, don't just report.** A number is a prompt to look, not a verdict. Ask
   what kind of complexity it is: a flat dispatch table, deep nesting, or a genuine
   tangle. Only the last two are worth acting on.
4. **Recommend** a tool, a threshold tied to that tool, and an exemption mechanism.
   Never a bare number.
5. **Write the report.** Whenever a tool actually ran and there are per-function
   scores, generate `./complexity-report.html` from `assets/report-template.html` —
   a single self-contained page with live threshold sliders and findings grouped by
   verdict. Keep the terminal reply short and point at it. Skip the page for purely
   conceptual questions where nothing was measured. See
   [references/report.md](references/report.md).

## When to Read Which Reference

- **What each metric measures and what it is valid for — cyclomatic, cognitive,
  nesting depth, essential complexity, size; the empirical record and its caveats**
  → Read [references/metrics.md](references/metrics.md)
- **Choosing a threshold, the exemption policy, the multiway-decision exemption, and
  what it costs to reduce complexity** → Read
  [references/thresholds.md](references/thresholds.md)
- **JavaScript / TypeScript — ESLint `complexity` and companions, oxlint, SonarJS
  cognitive complexity** → Read [references/javascript.md](references/javascript.md)
- **Go — gocyclo, cyclop, gocognit, nestif, funlen, maintidx, and the golangci-lint
  layering recipe** → Read [references/go.md](references/go.md)
- **Python — ruff `C901` and the `PLR` refactor family** → Read
  [references/python.md](references/python.md)
- **Generating the HTML findings report — when, where it goes, the data shape, and
  the verdict taxonomy** → Read [references/report.md](references/report.md)

## Quick Cues

- **Never quote a threshold without naming the tool.** One three-condition `if`
  scores 2, 4, or 5 depending on who counts it. Thresholds are not portable between
  tools, and copying one across is how a team ends up with a gate they never chose.
- **ESLint's `complexity` defaults to `max: 20`** — double McCabe's recommendation.
  Enabling the rule and leaving it alone gates at twice what the team probably meant.
- **golangci-lint's `gocyclo` and `gocognit` default to `min-complexity: 30`** —
  triple McCabe. Turning them on out of the box catches almost nothing, so teams
  believe they have a complexity gate when they do not. `cyclop` in the same file
  defaults to `10`.
- **ESLint's `variant: "modified"` is the switch exemption as a config flag.** It
  counts a whole `switch` as +1 regardless of case count. Few people know it exists,
  and it is the direct fix for a dispatch table tripping the rule.
- **The policy is not the number.** The original recommendation was _"limit to 10, or
  provide a written explanation of why the limit was exceeded"_ — the escape hatch
  is part of the rule, not a loophole in it.
- **Nesting depth beats CC for readability feedback** because it points at the
  offending line rather than labelling a whole function "too complex."
- **The report's value is the verdict, not the table.** Classifying each finding as
  needing attention, expected, or merely long is the part a linter cannot do — and a
  report where everything needs attention is one nobody acts on.

## Anti-patterns

- **Gating on cyclomatic complexity alone** and calling it a maintainability check.
  It measures branching, which is not the same thing.
- **Reporting a pure dispatch `switch` as a defect.** Its score is expected and its
  branches are readable in isolation. Exempt the case; do not manufacture a refactor.
- **Modifying the metric to make multiway decisions score lower.** Dividing by branch
  count lets a complexity-90 function report as 10 by adding a do-nothing switch.
  Exempt the case instead.
- **Refactoring purely to lower a number.** Removing a control dependency can
  introduce unstructured logic — a loop with two exits — and sometimes the
  higher-scoring version is genuinely the better code.
- **Splitting a function to satisfy a threshold when the halves are not cohesive.**
  If the extracted function needs locals passed by reference and the only name that
  fits is `doMoreOfTheSameThing`, the split is making things worse.
- **Treating a complexity report as a work queue.** Rank by what the number is
  telling you, not by the number.
