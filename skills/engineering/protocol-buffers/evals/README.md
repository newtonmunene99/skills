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
| `evals.json` | The 6 eval prompts, their expectations (what the grader checks) and regex signals |
| `files/<eval-name>/` | Fixture projects for evals that work on a proto on disk (4 and 6) |
| `prepare_workspace.py` | Builds the workspace directory layout and `eval_metadata.json` from `evals.json`, and copies each eval's fixtures into its runs |
| `grade_signals.py` | Scans run outputs for the `signals` regexes and prints the with-skill vs baseline delta |
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
    │   │   ├── project/          # fixture copy, the agent's working directory (evals with files)
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
**without** it, saving to the matching `outputs/` directory. When the eval
lists `files`, start the agent in that run's `project/` directory so the paths
in the prompt resolve; each run has its own copy, so edits don't leak between
the two configurations. An agent following
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

### Signals catch text; expectations carry judgement

Iteration 1 scored 100% in both columns: the first three evals test what the
model already knows about AIP, and every signal fired on both sides. They stay
as a floor. What the skill changes shows up elsewhere, so evals 4-6 and the
extra expectations on 1 and 2 aim at the edges a baseline answer gets wrong or
a with-skill answer used to copy from a broken reference:

- the imports a file needs (`client.proto` for `method_signature`), which the
  old worked example left out and with-skill answers copied;
- `field_behavior` on every request field, not just `name` and `parent`;
- validating with api-linter instead of stopping at a green `buf build`, and
  reporting only findings on changed lines in a file that already has some;
- extending an existing message: the next free number past `reserved` and a
  97-99 block, proto3 `optional` where zero and unset differ, no prepositions,
  and listing each deviation from the file's convention instead of silently
  choosing;
- judging breaking changes per edit, including the ones that keep the wire
  format (`optional`, a `oneof`, a rename).

Most of that sharpening is **not** expressible as a regex. "States the
consequence rather than sidestepping it", "judged breaking even though the wire
format holds", "judged separately from the package-version finding" — those
need a grader reading the answer. `grade_signals.py` only ever catches the
textually-detectable subset. Against the iteration-1 answers, the new
`client.proto` signal on evals 1 and 2 splits the columns the wrong way
(baseline yes, with skill no), which is the defect the fixed example is meant
to remove; the rest stay flat.

So read a flat signal delta as "no *textual* difference", never as "no
difference". The grader is where the judgement lives; the scanner just keeps the
mechanical half honest and reproducible.
