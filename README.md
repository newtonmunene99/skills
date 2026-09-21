# skills

A collection of [Agent Skills](https://skills.sh/) for AI coding agents.

[![skills.sh](https://skills.sh/newtonmunene99/skills)](https://skills.sh/newtonmunene99/skills)

## Install

```bash
npx skills add newtonmunene99/skills
```

Install a specific skill:

```bash
npx skills add newtonmunene99/skills --skill code-complexity
npx skills add newtonmunene99/skills --skill code-documentation
npx skills add newtonmunene99/skills --skill design-patterns
npx skills add newtonmunene99/skills --skill git-code-review
npx skills add newtonmunene99/skills --skill go-engineering
npx skills add newtonmunene99/skills --skill protocol-buffers
npx skills add newtonmunene99/skills --skill python-engineering
```

### Scope

| Scope   | Flag      | Location                                  | Use case                     |
| ------- | --------- | ----------------------------------------- | ---------------------------- |
| Project | (default) | `./.agents/skills/` or agent-specific dir | Share with the whole team    |
| Global  | `-g`      | `~/.cursor/skills/` etc.                  | Use across all your projects |

Supported agents include **Cursor**, **Codex**, **Claude Code**, **OpenCode**, **Windsurf**, and [others](https://github.com/vercel-labs/skills#supported-agents).

## Skills

| Skill                  | Directory                              | Description                                                                                                                                                                                                                                  |
| ---------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **code-complexity**    | `skills/engineering/code-complexity/`    | Cyclomatic, cognitive, nesting and size metrics — what each is valid for, what threshold to set, how to configure ESLint, oxlint, gocyclo/cyclop/gocognit and ruff, plus a throwaway HTML findings report |
| **code-documentation** | `skills/engineering/code-documentation/` | Comments, API/symbol docs, READMEs, and [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) knowledge docs — per-language conventions (godoc, TSDoc, docstrings, dartdoc, proto) without touching behavior |
| **design-patterns**    | `skills/engineering/design-patterns/`    | SOLID plus the creational, structural and behavioral patterns, in idiomatic Go, Python and TypeScript. Starts from the problem the code must handle, and says when no pattern is the right answer |
| **git-code-review**    | `skills/engineering/git-code-review/`    | Reviewing diffs, commits, branches, and MR/PRs on any git host — GitHub not required. High-signal findings only                                                                                                                              |
| **go-engineering**     | `skills/engineering/go-engineering/`     | Performance optimization and idiomatic style for Go, from [goperf.dev](https://goperf.dev) and the [Google Go Style Guide](https://google.github.io/styleguide/go)                                                                           |
| **protocol-buffers**   | `skills/engineering/protocol-buffers/`   | Protocol buffer design and resource-oriented API conventions, from [google.aip.dev](https://google.aip.dev/)                                                                                                                                 |
| **python-engineering** | `skills/engineering/python-engineering/` | Modern Python (3.11+) best practices — typing, dataclasses, pydantic v2, asyncio, pytest, ruff, uv — plus the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)                                                  |

## Repository structure

```
skills/
├── README.md
├── LICENSE
├── .gitignore
├── scripts/
│   ├── list-skills.sh
│   ├── skill-info.sh
│   └── validate-skills.sh
└── skills/
    └── engineering/
        ├── code-complexity/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── LICENSE
        │   ├── agents/
        │   ├── assets/
        │   │   └── report-template.html
        │   ├── evals/
        │   └── references/
        │       ├── metrics.md
        │       ├── thresholds.md
        │       ├── javascript.md
        │       ├── go.md
        │       ├── python.md
        │       └── report.md
        ├── code-documentation/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── LICENSE
        │   ├── agents/
        │   ├── evals/
        │   └── references/
        │       ├── comments.md
        │       ├── api-docs.md
        │       ├── readmes.md
        │       └── okf.md
        ├── design-patterns/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── LICENSE
        │   ├── agents/
        │   ├── evals/
        │   └── references/
        │       ├── solid.md
        │       ├── creational.md
        │       ├── structural.md
        │       ├── behavioral.md
        │       ├── go.md
        │       ├── python.md
        │       └── typescript.md
        ├── git-code-review/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── LICENSE
        │   ├── agents/
        │   ├── evals/
        │   └── references/
        │       ├── scope-resolution.md
        │       ├── merge-review.md
        │       └── reporting.md
        ├── go-engineering/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── LICENSE
        │   ├── agents/
        │   ├── evals/
        │   └── references/
        │       ├── performance/
        │       └── styleguide/
        ├── protocol-buffers/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── LICENSE
        │   ├── agents/
        │   ├── evals/
        │   └── references/
        │       └── aip/
        └── python-engineering/
            ├── SKILL.md
            ├── README.md
            ├── LICENSE
            ├── agents/
            ├── evals/
            └── references/
                ├── pyguide/
                └── modern/
```

Skills are grouped by category under `skills/`. Each skill directory contains a `SKILL.md` (the agent-readable skill definition) and optional reference files, evals, and agent-specific config.

## License

Apache-2.0. See [LICENSE](LICENSE).
