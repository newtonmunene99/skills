# git-code-review

An [Agent Skill](https://skills.sh/) for reviewing code changes in any git
repository — working tree, commits, ranges, branch-vs-base, or a hosted MR/PR.

## What it covers

- **Any git host** — git is the source of truth, so private git servers, self-hosted
  GitLab and Gitea work exactly as well as GitHub. `gh` and `glab` add metadata and
  can post comments, but the review never depends on them
- **Every scope** — unstaged and staged changes, a single commit, a range, the last N
  commits, author- and time-filtered history ("my commits from last week"),
  branch-vs-base, and MR/PR numbers or URLs
- **Merge review workflow** — resolving the diff, pre-flight stops (empty, draft,
  already reviewed), loading path-scoped project guidelines, validating findings,
  and posting inline comments with committable suggestions
- **Reporting** — output templates per mode, an 8-point review checklist, and
  Approve / Approve with nits / Request changes verdicts

The core of the skill is the **signal bar**: merge reviews flag compile failures,
definite logic errors, quoted guideline violations, and real security flaws — and
explicitly nothing else. No pre-existing issues, no pedantic nitpicks, nothing a
linter would catch, nothing speculative. *If you are not certain an issue is real,
do not flag it.* Three confirmed findings beat three findings and nine maybes,
because the maybes teach the reader to skim.

## Install

```bash
npx skills add newtonmunene99/skills --skill git-code-review
```

### Scope

| Scope   | Flag      | Location                                  | Use case                     |
| ------- | --------- | ----------------------------------------- | ---------------------------- |
| Project | (default) | `./.agents/skills/` or agent-specific dir | Share with the whole team    |
| Global  | `-g`      | `~/.cursor/skills/` etc.                  | Use across all your projects |

Supported agents include **Cursor**, **Codex**, **Claude Code**, **OpenCode**,
**Windsurf**, and [others](https://github.com/vercel-labs/skills#supported-agents).

## Skill structure

- **SKILL.md** — review modes, the signal bar, reference routing, and constraints
- **references/scope-resolution.md** — git command tables for every scope, relative
  and filtered history, resolving "me", two-dot vs three-dot diffs
- **references/merge-review.md** — the 7-step merge workflow, platform CLI table,
  comment posting and inline suggestions
- **references/reporting.md** — review checklist, output templates, verdicts
- **agents/openai.yaml** — optional Codex/Copilot display metadata (not read by the model)
- **evals/** — 3 eval prompts with expectations, and the harness to run them

## License

Apache-2.0. See [LICENSE](LICENSE).
