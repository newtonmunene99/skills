# protocol-buffers

An [Agent Skill](https://skills.sh/) for designing and working with protocol buffers and resource-oriented APIs, based on [Google API Improvement Proposals (AIPs)](https://google.aip.dev/).

Previously published as [newtonmunene99/aip-protocol-buffers-skill](https://skills.sh/newtonmunene99/aip-protocol-buffers-skill), now part of [newtonmunene99/skills](https://skills.sh/newtonmunene99/skills).

## What it covers

### AIP Guidelines (google.aip.dev)

- **Proto structure** — Package and file layout, imports, API-specific vs common protos
- **Services & resources** — Service naming, resource-oriented design, resource names, types, annotations
- **RPCs & methods** — HTTP transcoding, standard methods (Get, List, Create, Update, Delete), custom methods, long-running operations
- **Messages & fields** — Message naming, field naming conventions, field behavior annotations, standard fields, pagination, errors
- **Naming** — Naming conventions table and standard methods reference

## Install

```bash
npx skills add newtonmunene99/skills
```

### Scope

| Scope   | Flag      | Location                                  | Use case                     |
| ------- | --------- | ----------------------------------------- | ---------------------------- |
| Project | (default) | `./.agents/skills/` or agent-specific dir | Share with the whole team    |
| Global  | `-g`      | `~/.cursor/skills/` etc.                  | Use across all your projects |

Supported agents include **Cursor**, **Codex**, **Claude Code**, **OpenCode**, **Windsurf**, and [others](https://github.com/vercel-labs/skills#supported-agents).

## Skill structure

- **SKILL.md** — When to use the skill, workflow, reference routing, and quick cues
- **references/aip/proto-structure.md** — Package and file layout, common protos
- **references/aip/resources-and-services.md** — Services, resource design, resource names and annotations
- **references/aip/rpcs-and-methods.md** — HTTP transcoding, standard methods, custom methods, LRO
- **references/aip/messages-and-fields.md** — Message and field naming, field behavior, standard fields, pagination, errors
- **references/aip/full-example.md** — Full minimal CRUD proto example
- **references/aip/naming-and-methods.md** — Naming conventions and standard methods tables

## License

Apache-2.0. See [LICENSE](../../LICENSE).
