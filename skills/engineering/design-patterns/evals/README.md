# Evals

Test cases for the **design-patterns** skill, plus the harness for running them
through the [skill-creator](https://github.com/anthropics/skills) eval pipeline
(runner → grader → aggregate → viewer).

The point of an eval here is not "does the skill produce good prose". It is
**does having the skill change the answer**. Every run happens twice, once with the
skill and once without, so the benchmark shows the difference rather than an
absolute score. An expectation that passes in both columns is measuring the model,
not the skill.

> Results live in the gitignored workspace, so a fresh clone has no `iteration-1/`
> until someone runs step 1 below.

## Files

| File | Purpose |
| ---- | ------- |
| `evals.json` | The 6 eval prompts, their expectations (what the grader checks) and regex signals |
| `prepare_workspace.py` | Builds the workspace layout and `eval_metadata.json` from `evals.json` |
| `grade_signals.py` | Scans answers for the declared signals, so the mechanical checks are reproducible |
| `run_benchmark.sh` | Aggregates grading results and opens the review viewer |

## What the six prompts target

Earlier suites in this repo scored close to 100% in both columns, because their
expectations tested what the model already knew. These prompts are built around
the places a model without the skill goes wrong: it does what the prompt asks, in
the textbook shape, even when the right answer is a different shape or no pattern
at all.

| id | name | What a model without the skill gets wrong |
| -- | ---- | ----------------------------------------- |
| 1 | `go-singleton-db-pool` | **Obliges.** Writes the `sync.Once` global it was asked for, and misses that `pgxpool.New` needs a context and returns an error a no-argument `db.Pool()` cannot surface |
| 2 | `python-strategy-without-abc` | Builds the requested ABC with one-method subclasses. The force is real, so the answer is a registry of functions, not "leave it" and not the Java shape |
| 3 | `solid-review-without-invention` | Lists a violation for each of the five principles. There is one real finding (dependency construction inside `sendToFinance`); the currency `switch` and `OrderRepo` are fine |
| 4 | `no-force-no-pattern` | **Restraint.** "Make it enterprise-grade with patterns" over a 15-line function. The right answer adds no pattern and says what would change that |
| 5 | `ts-observer-durable-and-leak-free` | Stops at "use an event emitter". Misses unsubscribe, error isolation, publishing after commit, and that in-process events are lost on a crash |
| 6 | `go-visitor-is-a-type-switch` | Implements `Accept`/`Visit` double dispatch in Go, where a type switch over a sealed interface does the same, plus the exhaustiveness gap Go leaves open |

Evals 2 and 4 are the load-bearing pair, and they pull in opposite directions. Eval
2 has a real force, so declining to refactor is wrong; eval 4 has none, so any
pattern is wrong. A skill that only teaches "patterns are bad" passes 4 and fails 2.
A model that obliges every request passes neither.

Evals 1, 2 and 4 are adversarial: each prompt presupposes a design and asks only for
its implementation. Agreeing is the easy path and the wrong answer.

## Iteration 1 results (2026-09-21)

**94% with the skill, 80% without** (32 of 34 expectations against 27 of 34), at
about 72k tokens and 117 s per run against 44k and 62 s. The aggregate script's token
column is unreliable for these runs; those figures come from the run notifications.

| id | With skill | Without | What happened |
| -- | ---------- | ------- | ------------- |
| 1 | 5/5 | 4/5 | Baseline led with the global `db.Pool()` it was asked for |
| 2 | 6/6 | 3/6 | Baseline built the ABC; the skill run used a dict of functions |
| 3 | 6/6 | 4/6 | Baseline called the two-case switch an Open/Closed problem and never said what was fine |
| 4 | 4/5 | 5/5 | Both declined the pattern. The skill run changed `LateFee` to return an error, a behavior change inside a refactor |
| 5 | 5/6 | 5/6 | Both knew the outbox; neither discussed listener leaks |
| 6 | 6/6 | 6/6 | Both used a type switch and a sealed interface |

What changed after this iteration:

- **Eval 4 exposed a real gap.** The skill said nothing about keeping refactors
  behavior-preserving. `SKILL.md` now says a latent bug is a separate, opt-in
  finding, never folded into the refactor.
- **Eval 3 exposed the opposite risk.** The baseline also reported real bugs (money
  as floats, a status denylist, unescaped CSV) that the skill run, focused on
  design, left out. `SKILL.md` now scopes "do not invent findings" to design
  findings, and eval 3 has an expectation for the correctness list.
- **Signals fixed:** eval 1 missed "in `main`" written with backticks; eval 2's
  `refund|Protocol` matched the baseline through "refund".

Still weak, to sharpen in iteration 2: evals 4, 5 and 6 barely separate the columns.
The current model already declines patterns on a small function, knows the outbox
pattern, and prefers a type switch to Visitor in Go. Harder prompts (more pressure to
use a pattern, a design where leaks really matter) are needed to measure the skill
there.

## A note on the signals

`evals.json` carries an optional `signals` block per eval: regexes that must be
present and regexes that must be **absent**. `grade_signals.py` scans the answers
for them.

The absent signals match a *construct*, never a bare word, because a good answer
often names the rejected design in order to reject it. `\nclass \w+\(PaymentStrategy\):`
matches a class definition, not the sentence "instead of a `PaymentStrategy` ABC".
Even so, a with-skill answer can show the rejected code as a counter-example. Treat
an absent-signal hit as a prompt to read the answer, not as proof of failure.

A flat signal delta means "no *textual* difference", never "no difference". Most
expectations here ("names a concrete change the code makes painful", "says which
parts are fine") need a grader reading the answer.

## Prerequisites

The **skill-creator** skill must be installed: its `scripts/` and `eval-viewer/` do
the aggregation and review UI. `run_benchmark.sh` checks the usual locations:

```bash
export SKILL_CREATOR_PATH="$HOME/.claude/skills/skill-creator"
# or  .agents/skills/skill-creator  at the repo root
```

## Workspace layout

The workspace is a **sibling** of the skill directory and is gitignored
(`*-workspace/`), so runs never end up in a commit:

```
design-patterns/                          # skill root
design-patterns-workspace/
└── iteration-1/
    ├── eval-1/
    │   ├── eval_metadata.json    # prompt + expectations, from evals.json
    │   ├── with_skill/run-1/
    │   │   ├── outputs/          # the agent writes here
    │   │   ├── grading.json      # the grader writes here
    │   │   └── timing.json       # tokens + duration, from the run notification
    │   └── without_skill/run-1/  # same prompt, no skill: the baseline
    ├── eval-2/ ...
    ├── benchmark.json            # from aggregate_benchmark
    └── benchmark.md
```

## Workflow

### 1. Prepare

From the skill root (the parent of `evals/`):

```bash
python3 evals/prepare_workspace.py                 # iteration 1
python3 evals/prepare_workspace.py --iteration 2   # later iterations
```

### 2. Run

For each eval, run the prompt twice: once with the skill available (save to
`with_skill/run-1/outputs/`) and once without (save to `without_skill/run-1/outputs/`).
The skill-creator runner does this with subagents. Save `timing.json` from each run's
notification (`total_tokens`, `duration_ms`).

### 3. Grade

Run the skill-creator grader on each run directory. It reads `eval_metadata.json` and
`outputs/`, and writes `grading.json` with `expectations[].text`, `.passed` and
`.evidence`; the viewer depends on those exact field names. Feed it the output of
`grade_signals.py` too:

```bash
python3 evals/grade_signals.py              # table of with-skill vs baseline
python3 evals/grade_signals.py --json       # for the grader
```

### 4. Aggregate and review

```bash
./evals/run_benchmark.sh 1
```

This writes `benchmark.json` and `benchmark.md` and opens the viewer (usually
http://localhost:3117). For iteration 2 and later, the script passes the previous
iteration so the viewer can show both.
