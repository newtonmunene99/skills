---
name: git-code-review
description: >-
  Reviews code changes in any git repository and reports specific, actionable
  findings. Handles the working tree, staged files, a single commit, a commit
  range, the last N commits, author- and time-filtered history, branch-vs-base
  diffs, and hosted merge/pull requests. Git is the source of truth, so this
  works on private git servers, self-hosted GitLab and Gitea just as well as
  GitHub — platform CLIs are optional extras, never requirements. Use when
  asked to review changes, a branch, a commit, a range, someone's recent work,
  or an MR/PR, and whenever the user wants feedback on changes before pushing
  or merging, even without the word "review": "look over my diff",
  "sanity-check this before I push", "what do you think of these changes", "is
  this ready to merge". Owns the review workflow and the report; language
  skills (go-engineering, python-engineering, protocol-buffers) supply idiom
  checks and design-patterns supplies design findings.
disable-model-invocation: false
compatibility: >-
  Requires git. Platform CLIs (gh, glab) are optional extras — reviews fall
  back to git diff on any host. Judgement-heavy: most of the value is in the
  findings it declines to make, so it benefits from a high-reasoning model.
model: best
effort: xhigh
---

# Git Code Review

## Overview

**Git is the source of truth.** Platform CLIs (`gh`, `glab`) add metadata — title,
description, draft state — and can post comments, but they are never required. If a
CLI is missing, the remote is a private server, or auth fails, fall back to
`git diff` and continue the review. Stopping to demand GitHub is the most common way
this task fails, and it fails on exactly the repositories that most need reviewing.

Every git command should answer a question the review actually needs. Exploratory
digging costs context and rarely changes a finding.

## Review modes

| Mode             | Trigger                                      | Signal level                           |
| ---------------- | -------------------------------------------- | -------------------------------------- |
| **Working tree** | Default; unstaged and staged changes         | Full — Critical, Warnings, Suggestions |
| **History**      | Commits, ranges, last N, author/time filters | Full                                   |
| **Merge review** | Branch vs base, MR/PR, "review before merge" | **High signal only**                   |

Merge reviews get a stricter bar because their findings block someone. A nit posted
on a PR costs a round trip, a re-review, and some goodwill; the same nit on a working
tree costs nothing. Match the bar to the cost.

**Read [references/reporting.md](references/reporting.md) before writing the report,
in every mode.** It defines the headings, the `file:line` format for each finding, and
the only verdicts allowed. A report written from memory drifts: invented verdicts
("Not mergeable yet"), missing headings, findings with no location, and praise
numbered alongside defects. Each of those makes the review harder to act on.

## The signal bar

This is the merge-review bar, and the Critical tier everywhere else. Working-tree
and history reviews also report Warnings and Suggestions, per
[references/reporting.md](references/reporting.md). The exclusions below for
pre-existing issues, linter-catchable findings, and silenced rules apply in every
mode.

**Flag an issue only when one of these holds:**

- The code will fail to compile or parse — syntax, types, missing imports,
  unresolved references.
- The code will **definitely** produce wrong results. A clear logic error, not a
  suspicion.
- A project guideline is unambiguously violated. Quote the exact rule.
- There is a definite security flaw in the changed code — a hardcoded secret, an
  injection in a new code path.

**Do not flag:**

- **Pre-existing issues** on lines this change did not touch. The exception is a
  breakage caused by this change's dependency bump: if a bumped version stops
  untouched code from building, that is this change's issue even though no source
  line moved.
- **Code that looks wrong but is actually correct.** Read it again before writing it up.
- **Pedantic nitpicks** a senior engineer would skip.
- **Anything a linter or formatter will catch.** Do not run the linter to check, either.
- **General quality concerns**, unless a project guideline requires them.
- **Rules explicitly silenced in code** — `eslint-disable`, `nolint`, `# noqa`. The
  author already made that call.
- **Speculative issues** that depend on runtime state you cannot verify.
- **Style that is not codified** in the project's own guidelines.

**Builds and typechecks are allowed; linters and formatters are not.** When the diff
touches a dependency manifest, a lockfile, or build config, or when a compile failure
is otherwise plausible, run the project's build or typecheck once — `go build ./...`,
`tsc --noEmit`, `cargo check`. That is how "will fail to compile" gets confirmed rather
than guessed. Do not run `go vet`, eslint, ruff, or any formatter: what they report is
out of scope anyway. Running the tests is optional. Lockfile or tidy drift
(`go mod tidy -diff`, a lockfile out of step with its manifest) is not a standalone
finding; fold the fix into the finding it relates to.

**In a merge review, if you are not certain an issue is real, do not flag it.** A
review with three confirmed findings is worth more than one with three findings
and nine maybes, because the maybes teach the reader to skim. In a working-tree or
history review, report the maybe as a Warning or Suggestion and say how sure you
are, rather than dropping it.

## Neighbours

This skill owns the review of a diff, commit, branch or MR/PR: the scope, the signal
bar and the report. When the change is in Go, Python or `.proto` files, use
go-engineering, python-engineering or protocol-buffers as the checklist for
language idiom, and design-patterns for pattern and abstraction findings. Their
findings still go through this skill's signal bar and land in this skill's report,
so one review never ships as two reports with two verdicts.

## When to Read Which Reference

- **Working out _what_ to review from what the user said — git command tables for
  every scope, relative history ("last 5 commits"), author and time filters,
  resolving "me", multi-commit handling** → Read
  [references/scope-resolution.md](references/scope-resolution.md)
- **The merge-review workflow — resolving the diff, pre-flight stops, loading
  path-scoped project guidelines, validating findings, and posting review comments
  to a host** → Read [references/merge-review.md](references/merge-review.md)
- **Every review, before writing the report — output templates for each mode, the
  review checklist, and the allowed verdicts** → Read
  [references/reporting.md](references/reporting.md). This one is not optional.

## Constraints

- **Review only the requested scope.** Do not refactor unrelated code.
- **No destructive git.** Never `reset --hard`, `clean -fd`, or force push.
- **Do not commit, push, or modify files** unless explicitly asked.
- **Prove a fix in a scratch copy, never the user's working tree.** To check that a
  proposed fix builds or passes, use `git worktree add <tmp> HEAD`, or
  `git archive HEAD | tar -x -C <tmp>`, then copy in the working-tree changes under
  review and apply the fix there. Remove the scratch copy when done.
- **Review AI- and automation-authored changes** the same as any other. Being
  machine-written is not a reason to skip or to nitpick.
- **Large diffs (>500 lines):** summarize by file or module first, then deep-dive
  the highest-risk areas rather than reading linearly.
- **Commit ranges:** focus on the net diff, and note when an intermediate commit
  introduced a bug that a later one already fixed — flagging it as live is a
  false positive.
