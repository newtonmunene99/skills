# Inline comments

Comment style rules, what deserves a comment, and what does not.

## Contents

- [Style rules](#style-rules)
- [Why, not what](#why-not-what)
- [What not to comment](#what-not-to-comment)
- [Auditing existing comments](#auditing-existing-comments)

## Style rules

**Leading only.** A comment sits on its own line(s) above the code it describes,
never inline and never trailing. Trailing comments share a line with code, so they
get pushed around by every reformat, truncated by line-length limits, and lost in
diffs when the code beside them changes.

**Plain language.** Someone without deep familiarity with this codebase should be
able to follow the intent. The useful shape is: *this does X because downstream Y
depends on it; if Z changes, this has to change too.*

**Match the file's spacing convention.** If the surrounding file puts a blank line
between the comment block and the code, do the same. If it does not, do not.
Consistency inside a file matters more than any global preference.

**Complete sentences, capitalised, with terminal punctuation** — unless the
surrounding file has an established convention that differs.

## Why, not what

A comment restating the code is worse than no comment. It costs the reader time,
and it silently rots the moment the code changes underneath it while the comment
stays put. The code already says *what*. The comment's job is everything the code
cannot say: the reason, the constraint, the consequence.

### Bad

```go
// run some function
runJob()

i++ // increment
```

Neither line adds anything. The second also violates the leading-only rule.

### Good

```go
// Kick off the nightly reconciliation job. This must run before the
// billing rollup at 02:00 UTC; if it slips, invoices for that day will
// reflect stale usage counts.
runJob()
```

This carries three things the code cannot: the ordering constraint, the deadline,
and what goes wrong when the constraint is violated.

### Other things worth a comment

- **A non-obvious workaround.** Name the upstream bug or version it works around,
  so a future reader knows when it can be deleted.
- **A deliberate deviation** from the obvious implementation, and why the obvious
  one was rejected.
- **An invariant the compiler cannot express** — "callers must hold `mu`", "this
  slice is always sorted by `CreatedAt`".
- **Units and formats** that the type does not carry — is that timeout in seconds
  or milliseconds?

## What not to comment

- **Getters, setters, and other trivially-named methods**, unless they have a
  non-obvious side effect. `GetName()` returning `n.name` needs nothing.
- **Short, fully self-explanatory code.** If a reader gets it at a glance, a comment
  only slows them down.
- **Imports, closing braces, and other syntax noise.** `} // end for` is clutter;
  if a block is long enough to need it, the block is the problem.
- **Commented-out code.** Delete it. Version control already remembers.

## Auditing existing comments

When reviewing rather than writing, the highest-value finds are comments that are
actively *wrong* — they describe behavior the code no longer has. Those mislead in a
way that missing comments do not, so fix them first.

After that, look for genuinely undocumented complexity: the function with the
non-obvious algorithm, the field whose units are ambiguous, the error path nobody
explained.

A comment that is merely differently-styled from your preference is not a finding.
Leave it. Rewriting acceptable comments turns a small reviewable diff into a large
unreviewable one, and buries the changes that actually mattered.
