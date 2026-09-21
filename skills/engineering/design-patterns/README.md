# design-patterns

An [Agent Skill](https://skills.sh/) for applying SOLID and the classic design
patterns in the idiomatic form for Go, Python and TypeScript, and for knowing when
not to apply them at all.

## What it covers

- **SOLID.** Each principle as a smell detector: what change it protects against,
  how to spot it, the common misreading, and how it reads in languages without
  inheritance
- **Creational patterns.** Factory Method, Abstract Factory, Builder, Prototype,
  Singleton, plus dependency injection and object pools
- **Structural patterns.** Adapter, Bridge, Composite, Decorator, Facade, Flyweight,
  Proxy, and how to tell the four wrappers apart
- **Behavioral patterns.** Chain of Responsibility, Command, Interpreter, Iterator,
  Mediator, Memento, Observer, State, Strategy, Template Method, Visitor
- **Go, Python and TypeScript.** The idiomatic form of every pattern, with code that
  compiles, and the Java habits to catch in review

## The premise

> **A pattern is a named answer to a named problem. No problem, no pattern.**

The Gang of Four catalog was written in 1994 for C++ and Smalltalk. Many of its
patterns work around features those languages lacked, such as first-class
functions, closures, generators and structural typing. In Go, Python and TypeScript
they shrink: Strategy is a function parameter, Iterator is a generator, and Visitor
is a type switch or `match`.

So the skill leads with the *force*, the concrete change or variation the code has
to absorb, and treats "no pattern" as a valid and often correct answer. The
language reference, not the class diagram, decides what the code looks like.

## Install

```bash
npx skills add newtonmunene99/skills --skill design-patterns
```

### Scope

| Scope   | Flag      | Location                                  | Use case                     |
| ------- | --------- | ----------------------------------------- | ---------------------------- |
| Project | (default) | `./.agents/skills/` or agent-specific dir | Share with the whole team    |
| Global  | `-g`      | `~/.cursor/skills/` etc.                  | Use across all your projects |

Supported agents include **Cursor**, **Codex**, **Claude Code**, **OpenCode**,
**Windsurf**, and [others](https://github.com/vercel-labs/skills#supported-agents).

## Skill structure

- **SKILL.md.** Workflow (name the force, pick, translate, check the cost), the
  problem-to-pattern selector, SOLID quick cues, and anti-patterns
- **references/solid.md.** The five principles in depth
- **references/creational.md**, **structural.md**, **behavioral.md.** The
  language-neutral catalog: intent, force, shape, cost and neighbors per pattern
- **references/go.md**, **python.md**, **typescript.md.** The idiomatic code for
  every pattern in each language

## Related skills

- **go-engineering** and **python-engineering** cover language style and
  performance, and point here for design patterns.
- **code-complexity** judges whether a branchy function actually needs a refactor;
  this skill picks the refactor's shape once it does.

## Evals

Test cases and the benchmark workflow are in **[evals/](evals/)**. See
[evals/README.md](evals/README.md) for what each prompt targets and how to run them.

## License

Apache-2.0. See [LICENSE](LICENSE).
