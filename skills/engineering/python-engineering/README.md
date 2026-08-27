# python-engineering

An [Agent Skill](https://skills.sh/) for writing idiomatic, well-typed, and maintainable **modern Python (3.11+)**, based on the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) and current community best practices.

## What it covers

### Google Python Style Guide (pyguide)

- **Language rules** — imports, exceptions, mutable defaults, comprehensions, decorators, threading, power features
- **Style rules** — line length, indentation, whitespace, strings, statements, `main`, function length
- **Docstrings** — module, function, class, generator, and overridden-method docstrings in Google format
- **Naming** — modules, classes, functions, constants, protected/private, `TypeVar` conventions
- **Type annotations** — general rules, line breaking, forward refs, `NoneType`, aliases, generics, string types, typing imports

### Modern Python (3.11+)

- **Advanced typing** — `Protocol`, `TypeVar`, `ParamSpec`, `Self`, `override`, `@overload`, `TypeGuard`, PEP 695 generics
- **Data modeling** — when to use `@dataclass`, `pydantic` v2, `TypedDict`, `NamedTuple`, `Protocol`
- **Async** — `asyncio.run`, `TaskGroup`, cancellation, timeouts, sync/async boundaries
- **Errors** — custom exception design, chaining, `ExceptionGroup`, `try`/`except`/`else`/`finally` layout
- **Logging** — stdlib `logging`, structured logs, `%`-style args, per-module loggers, config
- **Testing** — pytest fixtures, parametrize, mocking, coverage, async tests
- **Tooling & packaging** — `pyproject.toml`, `uv`, `ruff`, `mypy`/`pyright`, src layout, entry points
- **Concurrency** — choosing between `asyncio`, threads, and `ProcessPoolExecutor`

### Not covered

Security review and performance optimization are deliberately out of scope — this skill is about correctness, typing, and style. Reach for a dedicated security or profiling skill for those.

## Install

```bash
npx skills add newtonmunene99/skills --skill python-engineering
```

### Scope

| Scope   | Flag      | Location                                  | Use case                     |
| ------- | --------- | ----------------------------------------- | ---------------------------- |
| Project | (default) | `./.agents/skills/` or agent-specific dir | Share with the whole team    |
| Global  | `-g`      | `~/.cursor/skills/` etc.                  | Use across all your projects |

Supported agents include **Cursor**, **Codex**, **Claude Code**, **OpenCode**, **Windsurf**, and [others](https://github.com/vercel-labs/skills#supported-agents).

## Skill structure

- **SKILL.md** — When to use the skill, workflow, reference routing, quick cues, and anti-patterns
- **references/pyguide/language-rules.md** — pyguide §2 (Python language rules)
- **references/pyguide/style-rules.md** — pyguide §3.1–3.7, 3.10–3.18 (formatting, strings, statements)
- **references/pyguide/docstrings.md** — pyguide §3.8 (Google-style docstrings)
- **references/pyguide/naming.md** — pyguide §3.16 (naming conventions)
- **references/pyguide/type-annotations.md** — pyguide §3.19 (type annotation rules)
- **references/modern/typing.md** — Advanced typing patterns (Protocol, TypeVar, Self, overloads, PEP 695)
- **references/modern/data-modeling.md** — Choosing between dataclass, pydantic v2, TypedDict, NamedTuple
- **references/modern/async.md** — asyncio patterns, `TaskGroup`, cancellation, timeouts
- **references/modern/errors.md** — Exception design, chaining, `ExceptionGroup`
- **references/modern/logging.md** — stdlib `logging` best practices
- **references/modern/testing.md** — pytest patterns
- **references/modern/tooling.md** — `pyproject.toml`, `uv`, `ruff`, `mypy`/`pyright`
- **agents/openai.yaml** — optional Codex/Copilot display metadata (not read by the model)
- **evals/** — 4 eval prompts with expectations, plus `lint-snippets.sh`, which checks every code sample against the skill's own ruff config

## License

Apache-2.0. See [LICENSE](LICENSE).
