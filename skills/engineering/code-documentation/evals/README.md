# Evals

Test cases for the **code-documentation** skill, plus the harness for running them
through the [skill-creator](https://github.com/anthropics/skills) eval pipeline
(runner → grader → aggregate → viewer).

The point of an eval here is not "does the skill produce good prose" — it's
**does having the skill change the answer**. Every run happens twice, once with
the skill and once without, so the benchmark shows the delta rather than an
absolute score. An expectation that passes in both columns isn't measuring the
skill; it's measuring the model. Those are worth rewriting.

> Iteration 1 ran the first five prompts
> ([`code-documentation-workspace/iteration-1/benchmark.md`](../../code-documentation-workspace/iteration-1/benchmark.md), gitignored):
> 98% with the skill, 100% without. The prompts were too easy to show a delta, so
> evals 2, 3 and 5 were hardened, a few always-passing expectations were dropped,
> and evals 6-9 were added for the rules nothing tested. Rerun from step 1 to
> measure the new set.

## Files

| File | Purpose |
| ---- | ------- |
| `evals.json` | The 10 eval prompts and their expectations (what the grader checks) |
| `files/<eval-name>/` | Fixture projects for the evals that work on a repo on disk (5-10) |
| `prepare_workspace.py` | Builds the workspace directory layout and `eval_metadata.json` from `evals.json`, and copies each eval's fixture project |
| `run_benchmark.sh` | Aggregates grading results and opens the review viewer |

## What the prompts target

| id | name | The thing a bare model gets wrong |
| -- | ---- | --------------------------------- |
| 1 | `document-go-package` | Documenting the unexported `advance` with its locking precondition, and stating units |
| 2 | `respect-existing-docs` | **Idempotency.** The existing docs carry `{Type}` tags and a missing period, which the usual TSDoc preference would "fix". Leaving them byte-identical is the test |
| 3 | `readme-from-scratch` | Not inventing a FAQ, rendering config as a table, and keeping the unmerged Slack work out of Features and Usage |
| 4 | `okf-concept-and-index` | Leaving `index.md` frontmatter-free, using bundle-absolute links, and **not fabricating `verified`** |
| 5 | `okf-ambiguous-scope-ask` | **Asking instead of guessing.** The prompt never says OKF; the bundle under `docs/catalog/` is only visible on disk, so a baseline writes godoc |
| 6 | `comment-proto-keep-lint-out-of-ci` | Adding buf lint **without** the `COMMENTS` category or `except` entries that hide existing findings, leaving `customerId` and the shared `Order` response alone, and proving the descriptor unchanged with `buf build -o` and `cmp` |
| 7 | `update-docs-after-change` | **Scope.** Fixing the stale `Allow` docs in `doc.go` and the README, and not sweeping the undocumented `internal/store` |
| 8 | `audit-skips-generated-and-okf` | Leaving generated and `third_party/` code out of the audit, leading with wrong docs, and **not creating** an OKF bundle that does not exist |
| 9 | `project-style-guide-wins` | Following `CONTRIBUTING.md`'s NumPy docstring rule over the Google default, and checking only docstrings changed |
| 10 | `full-pass-doc-go-and-coverage` | **Coverage.** Renaming `docs.go` to `doc.go`, moving a package comment out of a regular file, and documenting every non-test declaration, trivial ones included, while leaving `Test*` functions to a separate offer |

Evals 2, 5 and 7 are scored on restraint; 6 and 9 also check that the reply names a
mechanical comments-only check rather than asserting one.

Eval 2's signals are exact substrings lifted from the *existing* doc comments — if
the skill rewrote them, those strings vanish and the signal goes red. That makes
churn mechanically detectable rather than a judgement call, which is unusual and
worth keeping.

Eval 5 has no correct artifact at all: the right output is one question. Its
`absent` signals check that the project diff adds no frontmatter and no Go doc
comments, because a baseline's failure mode here is to pick one artifact and write it.

Eval 4 carries the integrity check. Its `absent` signals are `by: human:` and
`verified: {`, so a fabricated human sign-off on content nobody reviewed shows up
mechanically rather than needing a grader to notice it.

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
code-documentation/                          # skill root
code-documentation-workspace/
└── iteration-1/
    ├── eval-1/
    │   ├── eval_metadata.json    # prompt + expectations, from evals.json
    │   ├── with_skill/run-1/
    │   │   ├── outputs/          # the agent writes here
    │   │   ├── grading.json      # the grader writes here
    │   │   └── timing.json       # tokens + duration, from the run notification
    │   └── without_skill/run-1/  # same prompt, no skill — the baseline
    ├── eval-2/ ...
    ├── eval-5/                   # an eval with fixture files
    │   ├── inputs/               # pristine fixture project, to diff against
    │   └── with_skill/run-1/
    │       ├── project/          # working copy the agent edits in place
    │       └── outputs/          # the agent's reply
    ├── benchmark.json            # from aggregate_benchmark
    └── benchmark.md
```

The workspace directory is named from `skill_name` in `evals.json`, which
matches the skill directory name (`code-documentation`).

## Workflow

### 1. Prepare

```bash
python evals/prepare_workspace.py              # iteration 1
python evals/prepare_workspace.py --iteration 2
```

For evals with `files`, each run gets its own copy of the fixture project in
`<config>/run-1/project/`, and `eval-N/inputs/` keeps a pristine copy. Point the
agent at `project/` as its working directory and let it edit in place; its reply
still goes to `outputs/`.

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

Documentation quality is mostly a judgement call, so most of the weight here sits
in `expectations` rather than `signals`. "Explains the full-jitter behaviour",
"states the locking precondition", "usage grouped by use case" — none of those are
regex-expressible, and a grader has to read the answer. The signals only catch the
textually-detectable subset: whether a required string appeared, and whether an
existing one survived. For fixture evals, match them against the reply plus
`diff -ru inputs <config>/run-1/project`, which is why their `absent` patterns
look for added lines (`+...`). Read a flat signal delta as "no *textual* difference", never
as "no difference".
