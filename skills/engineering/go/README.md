# go-engineering

An [Agent Skill](https://skills.sh/) for writing performant, idiomatic, and readable Go code, based on the [Go Optimization Guide](https://goperf.dev) and the [Google Go Style Guide](https://google.github.io/styleguide/go).

Previously published as [newtonmunene99/goperf-skill](https://skills.sh/newtonmunene99/goperf-skill), now part of [newtonmunene99/skills](https://skills.sh/newtonmunene99/skills).

## What it covers

### Performance (goperf.dev)

- **Memory & GC** — Object pooling, preallocation, struct alignment, interface boxing, zero-copy, escape analysis, GOGC/GOMEMLIMIT
- **Concurrency** — Worker pools, atomics, `sync.Once`, immutable data, context and timeouts
- **I/O** — Buffered I/O, batching
- **Compiler** — Build flags, escape analysis
- **Networking** — `net/http` and Transport tuning, connection reuse, 10k+ connections, TLS/DNS, load shedding, backpressure, TCP/HTTP/2/gRPC/QUIC

### Style Guide (Google Go Style Guide)

- **Style & Idioms** — Naming, formatting, simplicity, maintainability, code readability, and Google Go Style Guide conventions

The skill is measurement-first: it steers the agent to establish baselines and identify bottlenecks before applying patterns. All guidance is self-contained in the skill; [goperf.dev](https://goperf.dev) has extended articles and examples.

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

- **SKILL.md** — When to use the skill, workflow (baseline → bottleneck → patterns), and quick cues
- **references/performance/common-patterns.md** — Memory, concurrency, I/O, compiler patterns
- **references/performance/networking.md** — HTTP, Transport, scaling, resilience, TLS/DNS, protocols
- **references/styleguide/** — Google Go Style Guide files (guide.md, best-practices.md, decisions.md, index.md)

## Evals

Test cases and the benchmark workflow (run evals, grade, aggregate, view results) are in **[evals/](evals/)**. See [evals/README.md](evals/README.md) for how to prepare the workspace, run evals with the skill-creator runner/grader/viewer, and open the review UI.

## License

Apache-2.0. See [LICENSE](LICENSE).
