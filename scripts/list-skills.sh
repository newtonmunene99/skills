#!/usr/bin/env bash
# Lists all SKILL.md files in the repository.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

find "$REPO/skills" -name SKILL.md -type f \
  -not -path '*/.git/*' \
  -not -path '*/node_modules/*' \
  -not -path '*-workspace/*' \
  | sed "s|^$REPO/||" \
  | sort
