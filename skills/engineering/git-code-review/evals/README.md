# Evals

Test cases for the **git-code-review** skill, plus the harness for running them
through the [skill-creator](https://github.com/anthropics/skills) eval pipeline
(runner → grader → aggregate → viewer).

The point of an eval here is not "does the skill produce good prose" — it's
**does having the skill change the answer**. Every run happens twice, once with
the skill and once without, so the benchmark shows the delta rather than an
absolute score. An expectation that passes in both columns isn't measuring the
skill; it's measuring the model. Those are worth rewriting.

> **Iteration 1 (2026-08-27, evals 1-3, 3 runs each) did not discriminate:** 100%
> pass rate with and without the skill, at +5.7k tokens for the skill. Several
> signals matched words the prompt itself supplied, and the baselines held back on
> the eval 1 decoys as well as the skill did. Evals 4-7 and the reworked signals
> target what a baseline does not do on its own; iteration 2 has not been run yet.

## Files

| File | Purpose |
| ---- | ------- |
| `evals.json` | The 7 eval prompts and their expectations (what the grader checks) |
| `prepare_workspace.py` | Builds the workspace directory layout and `eval_metadata.json` from `evals.json`, and a git repo per run for evals with a fixture |
| `files/<eval-name>/` | Fixture repos as plain files: `base/` is committed on `main`, `change/` is laid on top |
| `run_benchmark.sh` | Aggregates grading results and opens the review viewer |

## What the prompts target

| id | name | The thing a bare model gets wrong |
| -- | ---- | --------------------------------- |
| 1 | `merge-review-high-signal` | **Restraint.** The diff carries one real data race and four decoys. Iteration 1 baselines resisted the decoys too, so the discriminating checks are now the template ones: the `Base → Head` line and the `**Verdict:**` line |
| 2 | `no-github-fallback` | Self-hosted GitLab, no `glab`, can't install it. Baselines stall or reach for `gh` instead of falling back to `git diff` |
| 3 | `scope-resolution-author-and-time` | "Everything i've pushed this week." Baselines ask who you are instead of reading `git config user.email` |
| 4 | `working-tree-confirmed-trap` | Uncommitted Go change with a real map race and a loop-variable capture that is correct under `go 1.22`. Baselines flag the capture, skip the exact working-tree headings, and invent a verdict |
| 5 | `go-dependency-bump` | Vendored bump breaks an untouched file. Baselines either miss it (it is not in the diff) or bury it under gofmt, vet, a pre-existing ignored error and the stale `go.sum` |
| 6 | `comment-request-no-cli` | "Drop your comments on the PR" on Gitea with no CLI or token. Baselines script `curl` against the API or ask for a token instead of handing back paste-ready comments |
| 7 | `clean-merge-approve` | Nothing to flag. Baselines pad with optional suggestions and answer "Approve with nits", which a merge review never uses |

Evals 1, 4, 5 and 7 are scored as much on what is **absent** as
on what is present. In eval 1, half the expectations are negative — does NOT flag the spacing,
does NOT flag the loop style, does NOT flag the unchanged `LegacyTotal`. Finding the
race is the easy half; a review that finds the race and buries it under four nits
has still failed the high-signal bar. The `absent` signals check the structural half
of the same thing: a merge review must use the merge template, so `### Suggestions`
appearing at all means the wrong output format was used. Evals 4-7 add the
decoys iteration 1 lacked: a correct line that looks like a classic bug (eval 4),
tool output and drift that are not findings (eval 5), and a clean diff where the
right answer is a bare Approve (eval 7).

The diff also plants a pre-existing-code trap. `LegacyTotal` shows up in the diff
only because the new `Total` signature forced a mechanical call-site update, so
flagging anything about it is a false positive.

## Prerequisites

The **skill-creator** skill must be installed — its `scripts/` and
`eval-viewer/` do the aggregation and review UI. Common locations:

```bash
export SKILL_CREATOR_PATH="$HOME/.claude/skills/skill-creator"
# or  .agents/skills/skill-creator  at the repo root
```

`run_benchmark.sh` checks both of those automatically, so you usually don't
need to set anything.

## Workspace layout

The workspace is a **sibling** of the skill directory and is gitignored
(`*-workspace/`), so runs never end up in a commit:

```
git-code-review/                            # skill root
git-code-review-workspace/
└── iteration-1/
    ├── eval-1/
    │   ├── eval_metadata.json    # prompt + expectations, from evals.json
    │   ├── with_skill/run-1/
    │   │   ├── outputs/          # the agent writes here
    │   │   ├── repo/             # evals 4-5 only: the fixture repo to run in
    │   │   ├── grading.json      # the grader writes here
    │   │   └── timing.json       # tokens + duration, from the run notification
    │   └── without_skill/run-1/  # same prompt, no skill — the baseline
    ├── eval-2/ ...
    ├── benchmark.json            # from aggregate_benchmark
    └── benchmark.md
```

The workspace directory is named from `skill_name` in `evals.json`, which
matches the skill directory name (`git-code-review`).

## Workflow

### 1. Prepare

```bash
python evals/prepare_workspace.py              # iteration 1
python evals/prepare_workspace.py --iteration 2
```

### 2. Run each prompt twice

For every eval in `evals.json`, run the prompt **with** the skill and
**without** it, saving to the matching `outputs/` directory. An agent following
the skill-creator SKILL.md will spawn these as parallel subagents; launch the
with-skill and baseline runs in the same batch so they finish together.

Save `timing.json` (`total_tokens`, `duration_ms`) when each run completes —
that data arrives in the run notification and isn't recoverable afterwards.

Evals 1-3, 6 and 7 carry their input inline — the diff, the log, the situation —
so they need no repository and no network. Evals 2 and 3 therefore grade the
*approach and commands*, not a finished review. Evals 4 and 5 run against a real
repo that `prepare_workspace.py` builds at `<config>/run-1/repo/`; start those runs
in that directory. Eval 5's dependency is vendored, so `go build ./...` works
offline and fails in `internal/fx/convert.go`.

### 3. Grade

Run skill-creator's grader (`agents/grader.md`) over each run directory. It
reads `eval_metadata.json` and `outputs/`, then writes `grading.json`.

The viewer depends on exact field names: `expectations[]` entries must use
`text`, `passed` and `evidence` — not `name`/`met`/`details`.

Expectations that can be checked mechanically are better checked with a script
than by eye — it's faster and it stays honest across iterations.

### 4. Aggregate and review

```bash
./evals/run_benchmark.sh 1
```

This produces `benchmark.json`/`benchmark.md` and opens the viewer (usually
http://localhost:3117). The **Outputs** tab steps through each case for
qualitative feedback; the **Benchmark** tab shows pass rate, time and tokens per
configuration. Feedback is saved to `iteration-1/feedback.json`.

For iteration 2+, `run_benchmark.sh` passes `--previous-workspace`
automatically so the viewer can show the previous output alongside the new one.

### 5. Iterate

Improve the skill from the feedback, then rerun from step 1 into a new
iteration. Stop when the feedback comes back empty or the delta stops moving.

## Editing the evals

Add or change prompts in `evals.json`, then re-run `prepare_workspace.py` to
refresh `eval_metadata.json`. Keep prompts in the register a real user would
type — concrete detail, a bit of backstory, occasional sloppiness. A prompt that
reads like a spec tests the grader, not the skill.

If you add a case, prefer one with a **planted decoy** over one with more real bugs.
This skill's value is the findings it declines to make, and that only shows up in a
benchmark when there is something tempting to decline.
