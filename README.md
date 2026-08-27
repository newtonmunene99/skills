# skills

A collection of [Agent Skills](https://skills.sh/) for AI coding agents.

[![skills.sh](https://skills.sh/newtonmunene99/skills)](https://skills.sh/newtonmunene99/skills)

## Install

```bash
npx skills add newtonmunene99/skills
```

Install a specific skill:

```bash
npx skills add newtonmunene99/skills --skill code-documentation
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

| Skill                  | Directory                              | Description                                                                                                                                                                                 |
| ---------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **code-documentation** | `skills/engineering/documentation/`    | Comments, API/symbol docs, READMEs, and [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) knowledge docs — per-language conventions (godoc, TSDoc, docstrings, dartdoc, proto) without touching behavior |
| **git-code-review**    | `skills/engineering/code-review/`      | Reviewing diffs, commits, branches, and MR/PRs on any git host — GitHub not required. High-signal findings only                                                                             |
| **go-engineering**     | `skills/engineering/go/`               | Performance optimization and idiomatic style for Go, from [goperf.dev](https://goperf.dev) and the [Google Go Style Guide](https://google.github.io/styleguide/go)                          |
| **protocol-buffers**   | `skills/engineering/protocol-buffers/` | Protocol buffer design and resource-oriented API conventions, from [google.aip.dev](https://google.aip.dev/)                                                                                |
| **python-engineering** | `skills/engineering/python/`           | Modern Python (3.11+) best practices — typing, dataclasses, pydantic v2, asyncio, pytest, ruff, uv — plus the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) |

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
        ├── code-review/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── LICENSE
        │   ├── agents/
        │   ├── evals/
        │   └── references/
        │       ├── scope-resolution.md
        │       ├── merge-review.md
        │       └── reporting.md
        ├── documentation/
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
        ├── go/
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
        └── python/
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

## Previous repositories

These skills were previously published as standalone repos:

- [newtonmunene99/goperf-skill](https://skills.sh/newtonmunene99/goperf-skill) (now `go-engineering`)
- [newtonmunene99/aip-protocol-buffers-skill](https://skills.sh/newtonmunene99/aip-protocol-buffers-skill) (now `protocol-buffers`)

## License

Apache-2.0. See [LICENSE](LICENSE).
