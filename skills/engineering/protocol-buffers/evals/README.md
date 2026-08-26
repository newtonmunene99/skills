# Evals

Test cases for the **protocol-buffers** skill, plus the harness for running them
through the [skill-creator](https://github.com/anthropics/skills) eval pipeline
(runner → grader → aggregate → viewer).

The point of an eval here is not "does the skill produce good prose" — it's
**does having the skill change the answer**. Every run happens twice, once with
the skill and once without, so the benchmark shows the delta rather than an
absolute score. An expectation that passes in both columns isn't measuring the
skill; it's measuring the model. Those are worth rewriting.

## Files

| File | Purpose |
| ---- | ------- |
| `evals.json` | The 3 eval prompts and their expectations (what the grader checks) |
| `prepare_workspace.py` | Builds the workspace directory layout and `eval_metadata.json` from `evals.json` |
| `run_benchmark.sh` | Aggregates grading results and opens the review viewer |

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
protocol-buffers/                       # skill root
protocol-buffers-workspace/
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
