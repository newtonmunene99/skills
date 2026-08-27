# Evals

Test cases for the **python-engineering** skill, plus the harness for running them
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
| `evals.json` | The 4 eval prompts and their expectations (what the grader checks) |
| `prepare_workspace.py` | Builds the workspace directory layout and `eval_metadata.json` from `evals.json` |
| `run_benchmark.sh` | Aggregates grading results and opens the review viewer |
| `lint-snippets.sh` | Lints every ```python fence in the skill against the skill's own recommended ruff config |

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
python-engineering/                       # skill root
python-engineering-workspace/
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

## `lint-snippets.sh` — keeping the samples honest

Separate from the prompt evals, and much cheaper to run.

The skill tells agents to run `ruff check --fix`. If a code sample *in the
skill* is something ruff would rewrite, the skill is teaching a style its own
tooling immediately undoes — drift that's invisible on review and obvious to a
linter. This script extracts all 140 ` ```python ` fences and lints them against
the skill's own `select` list:

```bash
./evals/lint-snippets.sh          # pass/fail gate
./evals/lint-snippets.sh --diff   # show what ruff would rewrite
```

Three things keep the signal clean instead of a wall of noise:

- Rules that can't hold for a **fragment** (no imports, elided `...` bodies) are
  turned off — `F821`, `PLE1142`, `I001` and friends.
- Blocks using **PEP 695 syntax** are linted at `py312`, since the skill shows
  them deliberately as a 3.12+ opt-in.
- Fences containing a `# No` **counter-example** are reported separately and
  don't fail the run. Ruff agreeing with the counter-example is the point.

Anything left over is real drift. Blocks that don't parse as Python at all are
listed for a human — a deliberate docstring excerpt looks the same as a typo to
a parser, so the script won't guess.

Requires `ruff` on PATH (`uv tool install ruff`).

### A note on writing signals

`evals.json` carries an optional `signals` block per eval — regexes that must be
present, and regexes that must be **absent**. `grade_signals.py` scans the
answers for them so the mechanical expectations produce reproducible evidence
instead of an impression that drifts between iterations.

The absent-signals are the ones that need care. Three of the four in this suite
were wrong on their first run, all the same way: they matched a *mention* rather
than a *use*.

- `utcnow` fired on a with-skill answer that was **warning** about
  `datetime.utcnow()`.
- `ANN101|ANN102` fired on a scaffold answer explaining that ruff **removed**
  those rules.
- `setup.py` fired on an answer listing it under "don't do this".

In every case the skill was working and the signal called it a failure. Review
and scaffolding prompts name anti-patterns constantly — that's the job. Match
the construct (`ignore = [... ANN101`, `default_factory=datetime.utcnow`), never
the bare word.

The reverse failure is worth watching for too: a signal that passes in **both**
columns isn't measuring the skill. Fix the expectation or drop it — don't tune
the regex until the delta looks good.

### Signals catch text; expectations carry judgement

Iteration 1 scored ~100% in both columns and taught us the expectations were
testing what the model already knows. The iteration-2 set aims at the edges the
graders found in the *baseline* answers — an upper cap on `requires-python`, a
dangling `[project.scripts]` target, a proto whose prose promised soft delete
while `Delete` returned `Empty`, `cancel_requested` instead of
`requested_cancellation`.

Most of that sharpening is **not** expressible as a regex. "States the
consequence rather than sidestepping it", "the module it names actually appears
in the source", "judged separately from the package-version finding" — those
need a grader reading the answer. `grade_signals.py` only ever catches the
textually-detectable subset, and running the sharpened signals against the
iteration-1 answers proves the point: one new signal fired (the
`requires-python` upper cap, exactly the defect the grader flagged), the rest
stayed flat.

So read a flat signal delta as "no *textual* difference", never as "no
difference". The grader is where the judgement lives; the scanner just keeps the
mechanical half honest and reproducible.
