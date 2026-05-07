#!/usr/bin/env bash
# Prints name, description, and path for each skill by parsing SKILL.md frontmatter.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

while IFS= read -r skillfile; do
  name="" desc="" in_fm=false

  while IFS= read -r line; do
    if [[ "$line" == "---" ]]; then
      if $in_fm; then break; else in_fm=true; continue; fi
    fi
    $in_fm || continue

    if [[ "$line" =~ ^name:\ *(.*) ]]; then
      name="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^description:\ *\>-?$ ]]; then
      desc=""
    elif [[ -n "$name" && -z "$desc" && "$line" =~ ^\ +(.+) ]]; then
      desc="${BASH_REMATCH[1]}"
    fi
  done < "$REPO/$skillfile"

  rel_dir="$(dirname "$skillfile")"
  printf "%-22s  %-50s  %s\n" "${name:-(unnamed)}" "${desc:-(no description)}" "$rel_dir"
done < <("$REPO/scripts/list-skills.sh")
