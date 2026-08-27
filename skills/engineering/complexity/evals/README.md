# Evals

Test cases for the **code-complexity** skill, plus the harness for running them
through the [skill-creator](https://github.com/anthropics/skills) eval pipeline
(runner → grader → aggregate → viewer).

The point of an eval here is not "does the skill produce good prose" — it's
**does having the skill change the answer**. Every run happens twice, once with
the skill and once without, so the benchmark shows the delta rather than an
absolute score. An expectation that passes in both columns isn't measuring the
skill; it's measuring the model.

> These five prompts are written but have not been run yet. There is no
> `iteration-1/` until someone does step 1 below.

## Files

| File | Purpose |
| ---- | ------- |
| `evals.json` | The 5 eval prompts and their expectations (what the grader checks) |
| `prepare_workspace.py` | Builds the workspace directory layout and `eval_metadata.json` from `evals.json` |
| `run_benchmark.sh` | Aggregates grading results and opens the review viewer |

## What the five prompts target

| id | name | The thing a bare model gets wrong |
| -- | ---- | --------------------------------- |
| 1 | `switch-is-not-complex` | **Restraint.** The prompt asks "how should I refactor it?" about a reducer that should not be refactored. Baselines oblige with a handler map |
| 2 | `same-score-different-difficulty` | Two Go functions, both gocyclo 5. Baselines call them equivalent because the number says so |
| 3 | `go-linter-layering` | The `min-complexity: 30` trap, and answering gocyclo-vs-cyclop instead of listing both |
| 4 | `threshold-and-exemption` | That `C901` is not in ruff's default select, so the number they set may never run |
| 5 | `report-from-linter-output` | Two rankings that **disagree**, and generating the HTML report instead of a prose list |

Eval 5 is built around a deliberate inversion. `decodeFrame` is first on cyclomatic
(18) and last on cognitive (2); `UnmatchedTotals` is last on cyclomatic (11) and
first on cognitive (31). Reading down the cyclomatic list — the obvious move, and the
one a baseline makes — spends the user's one day of cleanup budget on the dispatch
table and leaves the genuinely nested function untouched. The whole skill is in
noticing that inversion.

Evals 1 and 4 are the load-bearing pair, and both are scored on what the answer
**declines** to do.

Eval 1 is deliberately adversarial: the prompt presupposes a refactor and asks only
for the cleanest one. Agreeing is the easy path and the wrong answer. Three of its
eight expectations are negative or restraint-shaped, and its `absent` signal
(`const handlers`) is a heuristic for the lookup-table refactor a baseline reaches
for. Treat that signal as a hint rather than proof — a good answer may name the
pattern in order to reject it, and the grader has to make that call.

Eval 4 asks for "just a number". The number is the easy part; the value is in the
two things the question does not ask about — that the rule is not enabled by
default, and that a threshold without an exemption mechanism is half a policy.

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
complexity/                             # skill root
code-complexity-workspace/
└── iteration-1/
    ├── eval-1/
    │   ├── eval_metadata.json    # prompt + expectations, from evals.json
    │   ├── with_skill/run-1/
    │   │   ├── outputs/          # the agent writes here
    │   │   ├── grading.json      # the grader writes here
    │   │   └── timing.json       # tokens + duration, from the run notification
    │   └── without_skill/run-1/  # same prompt, no skill — the baseline
    ├── eval-2/ ...
    ├── benchmark.json            # from aggregate_benchmark
    └── benchmark.md
```

Note the workspace is named from `skill_name` in `evals.json`
(`code-complexity`), not from the directory name (`complexity`).

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

All four prompts carry their input inline, so the runs need no fixture repository,
no installed linters and no network. Evals 3 and 4 grade the *recommended
configuration*, not the output of a real lint run.

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
type — concrete detail, a bit of backstory, occasional sloppiness.

Two things to preserve when adding a case:

**Prefer a prompt that presupposes the wrong thing** over one that asks neutrally.
"How should I refactor this?" tests more than "is this complex?", because the value
of this skill is largely in the findings it declines to make and the refactors it
talks you out of.

**Check any number an expectation asserts against the tool's own docs.** Every
default quoted across this skill was read from source during authoring. A stale
default in a skill about correct defaults is the worst failure mode available, and an
expectation asserting the wrong one will quietly train the skill toward it.
