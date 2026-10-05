# code-documentation

An [Agent Skill](https://skills.sh/) for writing, auditing, and improving inline code
comments, API/symbol documentation, README files, and Open Knowledge Format
knowledge documents — without touching behavior.

## What it covers

- **Comments** — leading-only placement, explaining *why* rather than restating
  *what*, plain language, and an explicit list of what not to comment
- **API & symbol docs** — the canonical convention per language (godoc, JSDoc/TSDoc,
  Python docstrings, dartdoc, rustdoc, Javadoc/KDoc), documenting errors and edge
  cases, and why unexported symbols deserve docs too
- **Protocol Buffers** — comments on services, RPCs, messages, fields, enums and
  enum values, which propagate into generated code in every target language
- **READMEs** — the required spine (Title → tagline → About → Installation → Usage →
  License), per-section conventions, and what to link rather than inline
- **[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
  (v0.2)** — bundle layout and reserved filenames, concept frontmatter, the
  provenance/trust/lifecycle families, the actor convention, cross-linking,
  `index.md` and `log.md`, and Attested Computation

The rule the skill leans hardest on: **leave acceptable documentation alone**. A
documentation pass that rewrites everything it touches buries the real change in
noise, so churn is treated as a failure mode rather than thoroughness.

Two OKF-specific guardrails sit alongside it. **Creating a knowledge bundle is a
scope decision** — when it is unclear whether OKF documents are wanted, the skill
asks rather than assuming. And it **never fabricates a `verified:` entry**, since
that field asserts a named person or process signed off on the content and it
propagates to every consumer that reads the bundle.

## Install

```bash
npx skills add newtonmunene99/skills --skill code-documentation
```

### Scope

| Scope   | Flag      | Location                                  | Use case                     |
| ------- | --------- | ----------------------------------------- | ---------------------------- |
| Project | (default) | `./.agents/skills/` or agent-specific dir | Share with the whole team    |
| Global  | `-g`      | `~/.cursor/skills/` etc.                  | Use across all your projects |

Supported agents include **Cursor**, **Codex**, **Claude Code**, **OpenCode**,
**Windsurf**, and [others](https://github.com/vercel-labs/skills#supported-agents).

## Skill structure

- **SKILL.md** — scope, workflow, reference routing, quick cues, and anti-patterns
- **references/comments.md** — comment style rules, before/after examples, what not to comment
- **references/api-docs.md** — per-language doc conventions and the full protobuf commenting rules
- **references/readmes.md** — README spine, section conventions, structural conventions
- **references/okf.md** — OKF v0.2 bundles, concept frontmatter, trust and provenance families, Attested Computation
- **scripts/py_same_code.py** — checks that two Python files differ only in comments and docstrings
- **agents/openai.yaml** — optional Codex/Copilot display metadata (not read by the model)
- **evals/** — 9 eval prompts with expectations, fixture projects, and the harness to run them

## Related skills

- **protocol-buffers** — AIP naming, resource design, and standard methods. This
  skill covers the doc comments; that one covers the contract they describe.
- **go-engineering**, **python-engineering** — the code itself. This skill owns doc
  comment wording and coverage; `python-engineering` keeps the Google-style
  docstring mechanics (`Args:` / `Returns:` / `Raises:`).
- **git-code-review** — reviewing a diff, branch or PR as a whole. This skill
  supplies the documentation findings.

## License

Apache-2.0. See [LICENSE](LICENSE).
