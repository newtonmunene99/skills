---
name: code-documentation
description: >-
  Writes, audits, and improves inline code comments, API/symbol documentation,
  README files, and Open Knowledge Format (OKF) knowledge documents, without
  changing any behavior. Covers comment style (leading only, why not what), the
  canonical doc convention per language — godoc, JSDoc/TSDoc, dartdoc, Python
  docstrings, protobuf leading comments — README structure, and OKF v0.2
  concept documents with their bundle layout, frontmatter, provenance and trust
  fields. Use when writing or reviewing comments and docstrings, documenting a
  package or public API, commenting a .proto file, auditing documentation
  coverage, writing a README, authoring or auditing an OKF knowledge bundle or
  concept doc, and after modifying code to check that its documentation is
  still complete and accurate.
disable-model-invocation: false
---

# Code Documentation

## Overview

Documentation work is editing the words *about* the code, never the code itself.
Four artifacts are in scope: **inline comments**, **API/symbol documentation**,
**README files**, and **OKF knowledge documents**. Refactoring, renaming symbols,
adding tests, or changing behavior are all out of scope even when the code obviously
needs them — mention them, don't do them. Mixing a rename into a documentation pass
makes the diff unreviewable.

The first three describe *code*. OKF describes **knowledge** — what a table means,
how a metric is defined, what to do when an alert fires — as a bundle of markdown
files with YAML frontmatter. It is a different artifact for a different reader.

## Scope check before writing OKF

Creating OKF documents is a scope decision, not a formatting one: a knowledge bundle
is a new artifact with its own conventions and its own maintenance burden. **When it
is not clear whether OKF documents are wanted, ask.**

Go ahead without asking only when the intent is unmistakable — the user named the
format, or a bundle already exists and the request plainly extends it, or a project
guideline says knowledge lives in OKF. Ask when "document X" lands in a repo holding
both code and a bundle, or when nothing OKF-shaped exists yet and the user has not
named the format. Keep it to one question with the concrete options as a short list,
then proceed on the answer.

## Workflow

1. **Detect the existing style.** Match what the project already does when it is
   consistent and reasonable. If the style is inconsistent, propose a single house
   style before making sweeping changes rather than silently picking one.
2. **Find what is actually missing**, not everything that *could* be documented.
   Self-evident code does not need a comment; adding one costs a reader attention
   and returns nothing.
3. **Leave acceptable documentation alone.** If a symbol already covers the why,
   the errors, and the edge cases at reasonable depth, do not reformat or rewrite
   it to match a style preference. This is the rule most worth holding on to: a
   documentation pass that rewrites everything it touches buries the real change
   in noise and makes the diff impossible to review. Churn is a failure mode.
4. **Edit in place.** Never produce shadow files or running commentary beside the
   code. Do *create* a missing canonical companion file — `doc.go` for a Go package
   without one, `README.md` for a project without one, the language equivalent
   otherwise. Leave unrelated files alone.
5. **Scope to the change.** When documenting after a code change, stay within the
   files that changed and their immediate package or module context (the package's
   `doc.go`, the nearest `README.md`). Sweep the whole repo only when asked for an
   audit.
6. **Report what changed** in the response: files touched, what was added, and any
   judgment calls made — the docstring style chosen when the project was ambiguous,
   for instance. That belongs in the reply, never spliced into source files.

## When to Read Which Reference

- **Comment style, what to comment, what to leave alone, worked before/after examples**
  → Read [references/comments.md](references/comments.md)
- **Per-language doc conventions — godoc, JSDoc/TSDoc, dartdoc, docstrings — and the
  full protobuf commenting rules for services, RPCs, messages, fields, and enums**
  → Read [references/api-docs.md](references/api-docs.md)
- **README structure — the required spine, section-by-section conventions, what to
  link rather than inline** → Read [references/readmes.md](references/readmes.md)
- **OKF knowledge documents — bundle layout and reserved filenames, concept
  frontmatter, provenance/trust/lifecycle fields, cross-linking, `index.md` and
  `log.md`, Attested Computation** → Read [references/okf.md](references/okf.md)

## Quick Cues

- **Leading comments only.** Never inline, never trailing. A trailing comment
  fights the code for the same line and loses on every reformat.
- **Explain why and what for, never what.** `// increment` next to `i++` is noise.
  What the reader cannot recover from the code is the reason it exists and what
  breaks if it changes.
- **Document unexported symbols too.** Exported docs serve API consumers; unexported
  docs serve maintainers, who usually need *more* context, not less — they are the
  ones who will have to change this code later.
- **Document errors, panics, and edge cases.** These are exactly what a reader
  cannot infer from a signature.
- **A runnable example beats prose** wherever one is possible.
- **Skip the trivia.** Getters, setters, imports, closing braces, and short
  self-explanatory code need nothing — unless there is a non-obvious side effect.
- **README spine, in order:** Title → one-line tagline → About → Installation →
  Usage → License. Everything else is optional and only earns a heading when there
  is real content for it.
- **OKF: `type` is the only required frontmatter key.** Missing optional fields are
  a conformant state, not a defect — don't report them as errors.
- **OKF: `index.md` and `log.md` are reserved** at every level, and index files
  carry no frontmatter (except `okf_version` on a bundle-root index).
- **OKF: never write a `verified:` entry for a review that did not happen.** It is a
  sign-off attached to a real identity. Unverified is honest; fabricated is not.

## Anti-patterns

- **Refactoring, renaming, or changing behavior** during a documentation pass.
- **Adding tests, CI config, or build files.** Not documentation.
- **Marketing copy, blog posts, or release notes.** Not documentation either.
- **Speculative docs** for code that does not exist yet.
- **Writing CHANGELOG entries.** Authors describe their own changes; link to
  `CHANGELOG.md` from the README instead of writing into it.
- **Empty headings.** A README section with a placeholder under it is worse than no
  section at all.
- **Standing up an OKF bundle nobody asked for**, or letting OKF frontmatter leak
  into source files when a request covers both code docs and knowledge docs.
- **Editing a sanctioned computation** in an OKF Attested Computation. Describe and
  structure it; filling declared parameters is the only permitted change.

## Defaults

- If the language is not detectable from context, ask rather than guess.
- If the language supports more than one doc style and the project has not picked
  one, choose one, apply it consistently, and say which you chose and why.
- A project style guide — `CONTRIBUTING.md`, `STYLE.md`, `.editorconfig`, lint
  config — overrides everything above. Defer to it and quote it when it applies.
