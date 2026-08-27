# Reporting

The review checklist, the output template for each mode, and the verdicts.

## Contents

- [Review checklist](#review-checklist)
- [Merge review output](#merge-review-output)
- [Working tree and history output](#working-tree-and-history-output)
- [Verdicts](#verdicts)

## Review checklist

What to look for, in rough order of how much a miss costs:

- **Correctness** — logic errors, off-by-one, races, nil/null handling, edge cases.
- **Security** — injection, auth gaps, hardcoded secrets, unsafe deserialization.
- **Error handling** — errors propagated rather than swallowed.
- **API and contracts** — breaking changes, backward compatibility.
- **Tests** — new behavior covered; no flaky patterns (sleeps, real clocks, ordering
  assumptions on unordered collections).
- **Readability and consistency** — naming and patterns matching the surrounding repo.
- **Performance** — obvious N+1 queries, unbounded loops or allocations.
- **Guidelines** — `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.cursor/rules/`,
  scoped to the changed paths.

The checklist is a prompt for where to look, not a list of headings to fill in. A
section with nothing real under it is padding, and padding is what makes reviews go
unread.

## Merge review output

```
## Code review — <branch or MR/PR ref>: <title or summary>

<1-3 sentence summary and verdict>

Base: <base> → Head: <head> (<N> commits)

### Issues
- <file>:<line> — <description> (<reason: bug | guideline | security>)
```

When there is nothing to report:

```
No issues found. Checked for bugs and project guideline compliance.
```

The `Base → Head` line matters more than it looks. It is how the author confirms you
reviewed the change they meant, and it is the first thing to check when a review and
an author disagree about what the change contains.

## Working tree and history output

Working-tree and history reviews get **full** feedback, since findings cost the
reader nothing but a glance. False positives and pre-existing issues are still out
of bounds.

```
### Summary

<1-3 sentences: what changed and the overall assessment>

### Critical (must fix)

<Bugs, security holes, broken contracts, definite guideline violations>

### Warnings (should fix)

<Likely problems, missing tests, poor error handling>

### Suggestions (consider)

<Style, naming, minor refactors>

### Positive notes

<Good patterns worth calling out>
```

For each finding give **file:line**, the **issue**, and the **fix** — with a snippet
where it helps. A finding without a fix leaves the reader to do the thinking twice.

Drop any heading with nothing under it. "Positive notes" in particular should name
something specific or not appear; generic praise reads as filler and devalues the
rest of the review.

When reviewing more than one commit, list the commits included in the header so the
scope is unambiguous.

## Verdicts

Every review ends with one of:

- **Approve** — nothing blocking.
- **Approve with nits** — nothing blocking, some suggestions the author can take or
  leave.
- **Request changes** — at least one Critical finding.

If the user wants the findings fixed, address Critical and Warning items first.
