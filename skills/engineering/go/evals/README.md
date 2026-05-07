# Evals and benchmark workflow

This directory contains test cases for goperf-skill and instructions for running the full eval pipeline (runner, grader, aggregate, viewer) using the **skill-creator** tooling.

## Prerequisites

- The **skill-creator** skill must be installed (e.g. under `.agents/skills/skill-creator/` or `~/.cursor/skills/skill-creator/`). Its scripts and eval-viewer are required for aggregate and review.
- **Runner**: Executed by an agent (e.g. Claude with access to the skill). The agent spawns subagents or runs prompts with/without the skill and saves outputs into the workspace.
- **Grader**: Uses the skill-creator’s grader agent (`agents/grader.md`) to evaluate outputs against expectations and produce `grading.json`.

## Files

- **evals.json** — Defines eval prompts, expected outputs, optional input files, and expectations (assertions). Add or edit expectations before or after the first run.
- **prepare_workspace.py** — Creates the workspace directory layout and `eval_metadata.json` from `evals.json` so you can run the agent and then grade/aggregate/view.
- **run_benchmark.sh** — Runs the skill-creator’s `aggregate_benchmark` and `generate_review` so you get `benchmark.json`/`benchmark.md` and the review UI.

## Directory layout

The workspace is a **sibling** of the skill directory:

```
goperf-skill/              # skill root
goperf-skill-workspace/    # workspace (created by prepare_workspace.py)
└── iteration-1/
    ├── eval-1/
    │   ├── eval_metadata.json
    │   ├── with_skill/
    │   │   └── run-1/
    │   │       ├── outputs/      # agent writes here
    │   │       ├── grading.json  # grader writes here
    │   │       └── timing.json   # optional: from run notification
    │   └── without_skill/
    │       └── run-1/
    │           ├── outputs/
    │           ├── grading.json
    │           └── timing.json
    ├── eval-2/
    │   └── ...
    └── eval-3/
        └── ...
```

After grading and aggregation:

- `iteration-1/benchmark.json` — produced by `aggregate_benchmark`
- `iteration-1/benchmark.md` — human-readable summary

## Workflow

### 1. Prepare the workspace

From the **skill root** (parent of `evals/`):

```bash
python evals/prepare_workspace.py
```

Or from repo root if goperf-skill is in a subdir:

```bash
python goperf-skill/evals/prepare_workspace.py --skill-dir goperf-skill
```

This creates `goperf-skill-workspace/iteration-1/eval-1/`, `eval-2/`, `eval-3/` with `eval_metadata.json` and empty `with_skill/run-1/outputs/` and `without_skill/run-1/outputs/`.

### 2. Run evals (agent)

Use the skill-creator workflow (or your own runner):

- For each eval in `evals.json`, run the **prompt** twice:
  - **With skill**: skill path = path to `goperf-skill`, save outputs to `goperf-skill-workspace/iteration-1/eval-<id>/with_skill/run-1/outputs/`.
  - **Without skill**: same prompt, no skill, save to `goperf-skill-workspace/iteration-1/eval-<id>/without_skill/run-1/outputs/`.
- Optionally save `timing.json` in each `run-1/` when the run completes (from the run notification: `total_tokens`, `duration_ms`, `total_duration_seconds`).

If you use an agent that follows the skill-creator SKILL.md, it will spawn subagents with these instructions and paths.

### 3. Add expectations (optional but recommended)

Edit `evals/evals.json` and fill in **expectations** for each eval — short, verifiable statements the grader can check (e.g. “The response recommends draining the response body before closing” or “The response includes a code example using sync.Pool”). Re-run `prepare_workspace.py` to refresh `eval_metadata.json` from the updated evals, or copy the expectations into each `eval_metadata.json` under the key the grader expects (e.g. `expectations`).

### 4. Grade each run

For each run directory that has `outputs/`, run the **grader** (skill-creator’s grader agent or equivalent):

- Inputs: the run’s `eval_metadata.json` (prompt, expectations), transcript (if any), and `outputs/`.
- Output: write `grading.json` into that run directory (`with_skill/run-1/grading.json`, etc.) with the schema from skill-creator’s `references/schemas.md`: at least `expectations` (array of `{ "text", "passed", "evidence" }`) and `summary` (`passed`, `failed`, `total`, `pass_rate`).

The skill-creator’s `agents/grader.md` describes how the grader agent should evaluate and format results.

### 5. Aggregate and open the viewer

Set the path to the skill-creator directory (e.g. where you have `scripts/aggregate_benchmark.py` and `eval-viewer/generate_review.py`). If goperf-skill lives inside the goperf repo and skill-creator is in `.agents/skills/skill-creator/`:

```bash
export SKILL_CREATOR_PATH=".agents/skills/skill-creator"   # or absolute path
./evals/run_benchmark.sh 1
```

Or pass the path as the second argument:

```bash
./evals/run_benchmark.sh 1 /path/to/skill-creator
```

This will:

1. Run `python -m scripts.aggregate_benchmark goperf-skill-workspace/iteration-1 --skill-name goperf-skill` from the skill-creator directory, producing `benchmark.json` and `benchmark.md`.
2. Run `python eval-viewer/generate_review.py goperf-skill-workspace/iteration-1 --skill-name goperf-skill --benchmark goperf-skill-workspace/iteration-1/benchmark.json` to start the review server (or use `--static out.html` for a static file in headless environments).

Then open the URL (e.g. http://localhost:3117) to review outputs and the benchmark tab. When done, submit feedback; it is saved to `goperf-skill-workspace/iteration-1/feedback.json`.

### 6. Iterate

Improve the skill based on feedback, then rerun from step 2 into a new iteration (e.g. `iteration-2/`). When launching the viewer for iteration 2+, pass the previous iteration so the UI can show previous outputs and feedback:

```bash
# After creating iteration-2 and grading:
python eval-viewer/generate_review.py goperf-skill-workspace/iteration-2 \
  --skill-name goperf-skill \
  --benchmark goperf-skill-workspace/iteration-2/benchmark.json \
  --previous-workspace goperf-skill-workspace/iteration-1
```

## Schema references

- **evals.json**: see skill-creator’s `references/schemas.md` (evals.json, grading.json, timing.json, benchmark.json).
- **grading.json** must use `expectations[].text`, `expectations[].passed`, and `expectations[].evidence` — the viewer expects these field names.
