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
  or an MR/PR, and before merging.
disable-model-invocation: false
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

## The signal bar

This is the part that decides whether a review is useful or just noise, so it stays
in context for every review.

**Flag an issue only when one of these holds:**

- The code will fail to compile or parse — syntax, types, missing imports,
  unresolved references.
- The code will **definitely** produce wrong results. A clear logic error, not a
  suspicion.
- A project guideline is unambiguously violated. Quote the exact rule.
- There is a definite security flaw in the changed code — a hardcoded secret, an
  injection in a new code path.

**Do not flag:**

- **Pre-existing issues** on lines this change did not touch.
- **Code that looks wrong but is actually correct.** Read it again before writing it up.
- **Pedantic nitpicks** a senior engineer would skip.
- **Anything a linter or formatter will catch.** Do not run the linter to check, either.
- **General quality concerns**, unless a project guideline requires them.
- **Rules explicitly silenced in code** — `eslint-disable`, `nolint`, `# noqa`. The
  author already made that call.
- **Speculative issues** that depend on runtime state you cannot verify.
- **Style that is not codified** in the project's own guidelines.

**If you are not certain an issue is real, do not flag it.** A review with three
confirmed findings is worth more than one with three findings and nine maybes,
because the maybes teach the reader to skim.

## When to Read Which Reference

- **Working out _what_ to review from what the user said — git command tables for
  every scope, relative history ("last 5 commits"), author and time filters,
  resolving "me", multi-commit handling** → Read
  [references/scope-resolution.md](references/scope-resolution.md)
- **The merge-review workflow — resolving the diff, pre-flight stops, loading
  path-scoped project guidelines, validating findings, and posting review comments
  to a host** → Read [references/merge-review.md](references/merge-review.md)
- **Output templates for each mode, the review checklist, and verdicts** → Read
  [references/reporting.md](references/reporting.md)

## Constraints

- **Review only the requested scope.** Do not refactor unrelated code.
- **No destructive git.** Never `reset --hard`, `clean -fd`, or force push.
- **Do not commit, push, or modify files** unless explicitly asked.
- **Review AI- and automation-authored changes** the same as any other. Being
  machine-written is not a reason to skip or to nitpick.
- **Large diffs (>500 lines):** summarize by file or module first, then deep-dive
  the highest-risk areas rather than reading linearly.
- **Commit ranges:** focus on the net diff, and note when an intermediate commit
  introduced a bug that a later one already fixed — flagging it as live is a
  false positive.
