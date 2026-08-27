#!/usr/bin/env bash
# Aggregate grading results and open the review viewer for one iteration.
#
# Usage:
#   ./evals/run_benchmark.sh [iteration] [skill-creator-path]
#
# Default iteration: 1
# skill-creator path resolution order:
#   1. second argument
#   2. $SKILL_CREATOR_PATH
#   3. <repo-root>/.agents/skills/skill-creator
#   4. ~/.claude/skills/skill-creator
#
# Example:
#   export SKILL_CREATOR_PATH="$HOME/.claude/skills/skill-creator"
#   ./evals/run_benchmark.sh 1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# The skill name lives in evals.json so it can't drift from prepare_workspace.py.
SKILL_NAME="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["skill_name"])' "$SCRIPT_DIR/evals.json")"
WORKSPACE_DIR="$(cd "$SKILL_DIR/.." && pwd)/${SKILL_NAME}-workspace"

ITERATION="${1:-1}"
ITER_DIR="$WORKSPACE_DIR/iteration-$ITERATION"

SKILL_CREATOR_PATH="${2:-${SKILL_CREATOR_PATH:-}}"
if [ -z "$SKILL_CREATOR_PATH" ]; then
  for CANDIDATE in \
    "$(cd "$SKILL_DIR/../../.." && pwd)/.agents/skills/skill-creator" \
    "$HOME/.claude/skills/skill-creator"
  do
    if [ -d "$CANDIDATE" ]; then SKILL_CREATOR_PATH="$CANDIDATE"; break; fi
  done
fi
if [ -z "$SKILL_CREATOR_PATH" ] || [ ! -d "$SKILL_CREATOR_PATH" ]; then
  echo "Error: skill-creator not found." >&2
  echo "Pass it as the second argument or set SKILL_CREATOR_PATH." >&2
  exit 1
fi
SKILL_CREATOR_PATH="$(cd "$SKILL_CREATOR_PATH" && pwd)"

if [ ! -d "$ITER_DIR" ]; then
  echo "Error: workspace iteration not found: $ITER_DIR" >&2
  echo "Run: python evals/prepare_workspace.py --iteration $ITERATION" >&2
  exit 1
fi

echo "Skill:         $SKILL_NAME"
echo "Iteration:     $ITER_DIR"
echo "skill-creator: $SKILL_CREATOR_PATH"
echo ""

echo "Running aggregate_benchmark..."
(cd "$SKILL_CREATOR_PATH" && python3 -m scripts.aggregate_benchmark "$ITER_DIR" --skill-name "$SKILL_NAME")

BENCHMARK_JSON="$ITER_DIR/benchmark.json"
if [ ! -f "$BENCHMARK_JSON" ]; then
  echo "Warning: benchmark.json not produced — grading.json is probably missing from the run dirs." >&2
fi

echo "Launching review viewer..."
PREV_DIR="$WORKSPACE_DIR/iteration-$((ITERATION - 1))"
ARGS=("$ITER_DIR" --skill-name "$SKILL_NAME")
[ -f "$BENCHMARK_JSON" ] && ARGS+=(--benchmark "$BENCHMARK_JSON")
[ -d "$PREV_DIR" ] && ARGS+=(--previous-workspace "$PREV_DIR")

(cd "$SKILL_CREATOR_PATH" && python3 eval-viewer/generate_review.py "${ARGS[@]}")

echo "Done. Open the URL shown above (usually http://localhost:3117)."
