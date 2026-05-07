#!/usr/bin/env bash
# Run aggregate_benchmark and generate_review for a given iteration.
#
# Usage:
#   ./evals/run_benchmark.sh [iteration] [skill-creator-path]
#
# Default iteration: 1
# Default skill-creator path: $SKILL_CREATOR_PATH or parent repo's .agents/skills/skill-creator
#
# Example (from goperf-skill root):
#   export SKILL_CREATOR_PATH="../.agents/skills/skill-creator"
#   ./evals/run_benchmark.sh 1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="goperf-skill"
WORKSPACE_DIR="$(cd "$SKILL_DIR/.." && pwd)/${SKILL_NAME}-workspace"

ITERATION="${1:-1}"
ITER_DIR="$WORKSPACE_DIR/iteration-$ITERATION"

# Resolve skill-creator path
SKILL_CREATOR_PATH="${2:-$SKILL_CREATOR_PATH}"
if [ -z "$SKILL_CREATOR_PATH" ]; then
  # Default: .agents/skills/skill-creator relative to workspace parent (e.g. goperf repo)
  CANDIDATE="$(cd "$SKILL_DIR/../.." && pwd)/.agents/skills/skill-creator"
  if [ -d "$CANDIDATE" ]; then
    SKILL_CREATOR_PATH="$CANDIDATE"
  else
    echo "Error: SKILL_CREATOR_PATH not set and not found at $CANDIDATE" >&2
    echo "Usage: $0 [iteration] [skill-creator-path]" >&2
    echo "  or set SKILL_CREATOR_PATH" >&2
    exit 1
  fi
fi
SKILL_CREATOR_PATH="$(cd "$SKILL_CREATOR_PATH" && pwd)"

if [ ! -d "$ITER_DIR" ]; then
  echo "Error: workspace iteration not found: $ITER_DIR" >&2
  echo "Run: python evals/prepare_workspace.py" >&2
  exit 1
fi

echo "Skill: $SKILL_NAME"
echo "Workspace iteration: $ITER_DIR"
echo "Skill-creator: $SKILL_CREATOR_PATH"
echo ""

# Aggregate
echo "Running aggregate_benchmark..."
(cd "$SKILL_CREATOR_PATH" && python3 scripts/aggregate_benchmark.py "$ITER_DIR" --skill-name "$SKILL_NAME")
BENCHMARK_JSON="$ITER_DIR/benchmark.json"
if [ ! -f "$BENCHMARK_JSON" ]; then
  echo "Warning: benchmark.json not produced (grading.json may be missing in run dirs)" >&2
fi

# Viewer
echo "Launching review viewer..."
(cd "$SKILL_CREATOR_PATH" && python3 eval-viewer/generate_review.py "$ITER_DIR" \
  --skill-name "$SKILL_NAME" \
  $([ -f "$BENCHMARK_JSON" ] && echo "--benchmark $BENCHMARK_JSON"))

echo "Done. If the viewer started a server, open the URL shown above (e.g. http://localhost:3117)."
