# skills

A collection of [Agent Skills](https://skills.sh/) for AI coding agents.

[![skills.sh](https://skills.sh/newtonmunene99/skills)](https://skills.sh/newtonmunene99/skills)

## Install

```bash
npx skills add newtonmunene99/skills
```

Install a specific skill:

```bash
npx skills add newtonmunene99/skills --skill go-engineering
npx skills add newtonmunene99/skills --skill protocol-buffers
```

### Scope

| Scope   | Flag      | Location                                  | Use case                     |
| ------- | --------- | ----------------------------------------- | ---------------------------- |
| Project | (default) | `./.agents/skills/` or agent-specific dir | Share with the whole team    |
| Global  | `-g`      | `~/.cursor/skills/` etc.                  | Use across all your projects |

Supported agents include **Cursor**, **Codex**, **Claude Code**, **OpenCode**, **Windsurf**, and [others](https://github.com/vercel-labs/skills#supported-agents).

## Skills

| Skill | Directory | Description |
| ----- | --------- | ----------- |
| **go-engineering** | `skills/engineering/go/` | Performance optimization and idiomatic style for Go, from [goperf.dev](https://goperf.dev) and the [Google Go Style Guide](https://google.github.io/styleguide/go) |
| **protocol-buffers** | `skills/engineering/protocol-buffers/` | Protocol buffer design and resource-oriented API conventions, from [google.aip.dev](https://google.aip.dev/) |

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
        ├── go/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── agents/
        │   ├── evals/
        │   └── references/
        │       ├── performance/
        │       └── styleguide/
        └── protocol-buffers/
            ├── SKILL.md
            ├── README.md
            └── references/
                └── aip/
```

Skills are grouped by category under `skills/`. Each skill directory contains a `SKILL.md` (the agent-readable skill definition) and optional reference files, evals, and agent-specific config.

## Previous repositories

These skills were previously published as standalone repos:

- [newtonmunene99/goperf-skill](https://skills.sh/newtonmunene99/goperf-skill) (now `go-engineering`)
- [newtonmunene99/aip-protocol-buffers-skill](https://skills.sh/newtonmunene99/aip-protocol-buffers-skill) (now `protocol-buffers`)

## License

Apache-2.0. See [LICENSE](LICENSE).
