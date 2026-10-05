# Inline comments

Comment style rules, what deserves a comment, and what does not.

## Contents

- [Style rules](#style-rules)
- [Why, not what](#why-not-what)
  - [What a good doc carries](#what-a-good-doc-carries)
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
surrounding file has an established convention that differs. This is a rule for
text you write; it is no reason to touch an existing comment that lacks a period.

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

### What a good doc carries

How the code works is the smallest part of a good comment or doc. This checklist
applies to declaration docs and inline comments alike. Write the items that are
true and that the reader cannot get from the code; most docs need two or three of
them, and a trivial declaration needs none beyond its one line. State each fact
once, in the doc of the symbol that owns it, and link to it from the others
instead of restating it; copies drift apart the first time one is edited. The owner
is wherever the logic lives. A thin wrapper that only delegates links
(`// Reserve implements [Store.Reserve] by calling reserve under mu.`), while the
function that does the work keeps its full contract, preconditions and failure
modes in its own doc, exported or not, because that is where a maintainer
changing it will look.

- **Why it is done this way.** The reason the code exists in this shape, and the
  deviation from the obvious implementation, with why the obvious one was rejected.
- **Trade-offs.** What the design buys and what it costs: "O(1) lookups at the
  price of holding every key in memory", "simpler than a queue, but a crash loses
  in-flight work".
- **Pitfalls for callers.** Misuse that compiles and then breaks: "not safe to
  copy after first use", "do not call inside a transaction, it opens its own",
  "the returned slice aliases the buffer".
- **Invariants the compiler cannot express** — "callers must hold `mu`", "this
  slice is always sorted by `CreatedAt`".
- **Units and formats** that the type does not carry — is that timeout in seconds
  or milliseconds?
- **Relations to other code.** What this pairs with, depends on, mirrors or must
  stay in sync with, in this package, another package, a library or a service.
  Link symbols with the language's doc-link syntax (godoc `[pkg.Symbol]`, TSDoc
  `{@link}`, Sphinx roles) so the link survives renames and is clickable.
- **Workarounds.** Name the upstream bug, issue or version being worked around, so a
  future reader knows when the workaround can be deleted.
- **Blockers and known limits.** What is deliberately unsupported or not done yet,
  and what it waits on, with an issue link rather than a bare `TODO`: "parent
  scoping is unsupported until the key encoding change (#412) lands".

## What not to comment

- **Getters, setters, and other trivially-named methods**, beyond their one-line
  declaration doc, unless they have a non-obvious side effect. `GetName()` returning
  `n.name` needs `// GetName returns the node's name.` and nothing inside it.
- **Short, fully self-explanatory code.** If a reader gets it at a glance, a comment
  only slows them down.
- **Imports, closing braces, and other syntax noise.** `} // end for` is clutter;
  if a block is long enough to need it, the block is the problem.
- **Commented-out code.** Delete it. Version control already remembers.

## Auditing existing comments

When reviewing rather than writing, the highest-value finds are comments that are
actively *wrong* — they describe behavior the code no longer has. Those mislead in a
way that missing comments do not, so fix them first.

After that, every undocumented declaration is a gap, test functions aside. Give the
most words to the undocumented complexity: the function with the non-obvious
algorithm, the field whose units are ambiguous, the error path nobody explained.

A comment that is merely differently-styled from your preference is not a finding.
Leave it. Rewriting acceptable comments turns a small reviewable diff into a large
unreviewable one, and buries the changes that actually mattered.
