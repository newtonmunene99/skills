#!/usr/bin/env bash
# Validates that every SKILL.md has required frontmatter fields and a references/ directory.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
errors=0

while IFS= read -r skillfile; do
  dir="$(dirname "$REPO/$skillfile")"
  name="" desc="" has_fm=false

  while IFS= read -r line; do
    if [[ "$line" == "---" ]]; then
      if $has_fm; then break; else has_fm=true; continue; fi
    fi
    $has_fm || continue
    [[ "$line" =~ ^name:\ *(.*) ]] && name="${BASH_REMATCH[1]}"
    [[ "$line" =~ ^description: ]] && desc="present"
  done < "$REPO/$skillfile"

  if ! $has_fm; then
    echo "FAIL  $skillfile  missing YAML frontmatter"
    ((errors++))
  fi
  if [[ -z "$name" ]]; then
    echo "FAIL  $skillfile  missing 'name' in frontmatter"
    ((errors++))
  fi
  if [[ -z "$desc" ]]; then
    echo "FAIL  $skillfile  missing 'description' in frontmatter"
    ((errors++))
  fi
  if [[ ! -d "$dir/references" ]]; then
    echo "WARN  $skillfile  no references/ directory"
  fi
done < <("$REPO/scripts/list-skills.sh")

if (( errors > 0 )); then
  echo ""
  echo "$errors error(s) found."
  exit 1
else
  echo "All skills OK."
fi
