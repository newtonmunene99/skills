#!/usr/bin/env bash
# Lint every ```python fence in the skill against the skill's OWN ruff config.
#
# Why this exists: the skill tells agents to run `ruff check --fix`. If a code
# sample in the skill is something ruff would rewrite, the skill teaches a style
# its own tooling immediately undoes. That drift is invisible on review and
# obvious to a linter, so let the linter find it.
#
# Three things make the signal clean rather than a wall of noise:
#   - Fragments (no imports, elided `...` bodies) have those rules turned off.
#   - Blocks using PEP 695 syntax are linted at py312, since the skill
#     deliberately shows them as a 3.12+ opt-in.
#   - Fences containing a "# No" counter-example are expected to trip ruff.
#     Those are reported but don't fail the run — ruff agreeing IS the point.
#
# Usage:
#   ./evals/lint-snippets.sh          # pass/fail gate
#   ./evals/lint-snippets.sh --diff   # show the rewrites ruff would apply
#
# Requires: ruff on PATH (`uv tool install ruff`, `brew install ruff`, ...).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

command -v ruff >/dev/null 2>&1 || { echo "Error: ruff not on PATH." >&2; exit 1; }

mkdir -p "$WORK/py311" "$WORK/py312" "$WORK/expected"

python3 - "$SKILL_DIR" "$WORK" <<'PYEOF'
import ast
import pathlib
import re
import sys

skill, work = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])

# PEP 695: `type X = ...`, `def f[T](...)`, `class C[T]:` — 3.12+ only, and the
# skill presents them that way on purpose.
PEP695 = re.compile(r"^type\s+\w+\s*(\[|=)|^(def|class)\s+\w+\[", re.M)

counts = {"py311": 0, "py312": 0, "expected": 0}
unparseable = []

for md in sorted(skill.rglob("*.md")):
    rel = md.relative_to(skill)
    for i, block in enumerate(re.findall(r"```python\n(.*?)```", md.read_text(), re.S)):
        # Encode the source path in the filename so ruff's output points back at
        # the markdown a human actually has to edit.
        name = f"{str(rel).replace('/', '__').removesuffix('.md')}__block{i}.py"

        try:
            ast.parse(block)
        except SyntaxError as exc:
            # Either a real error in a sample, or a deliberate non-code excerpt
            # (a bare `Args:` docstring section). Both need a human, not ruff.
            unparseable.append(f"{rel} block {i}: {exc.msg} (line {exc.lineno})")
            continue

        if re.search(r"^\s*#\s*No\b", block, re.M):
            bucket = "expected"          # labelled counter-example
        elif PEP695.search(block):
            bucket = "py312"
        else:
            bucket = "py311"

        (work / bucket / name).write_text(block)
        counts[bucket] += 1

total = sum(counts.values()) + len(unparseable)
print(f"Extracted {total} python blocks from {skill.name}/")
print(f"  {counts['py311']} linted at py311, {counts['py312']} at py312, "
      f"{counts['expected']} counter-examples, {len(unparseable)} not parseable")
if unparseable:
    print("\nNot parseable as Python (check by hand — a real typo looks like this too):")
    for u in unparseable:
        print(f"  - {u}")
PYEOF

# The skill's own `select` list, minus rules that cannot hold for a fragment
# with no imports, no module docstring, and elided bodies.
write_config() {
  cat > "$1" <<TOMLEOF
line-length = 80
target-version = "$2"

[lint.isort]
known-first-party = ["myproj", "myproject"]

[lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM", "PL", "RUF", "PT", "TID", "TC"]
ignore = [
    "F821", "F401", "F811", "F704", "F706", "F841",  # fragments lack surrounding scope
    "PLE1142",                                        # \`await\` outside an async def
    "B007",                                           # loop vars unused in \`...\` bodies
    "E501", "W291", "W293",                           # prose-driven wrapping
    "E301", "E302", "E303", "E305", "I001",           # blank lines / trailing newline
    "TC003", "PLR2004", "RUF100",
]
TOMLEOF
}
write_config "$WORK/ruff311.toml" py311
write_config "$WORK/ruff312.toml" py312

if [ "${1:-}" = "--diff" ]; then
  ruff check --config "$WORK/ruff311.toml" --diff "$WORK/py311" || true
  ruff check --config "$WORK/ruff312.toml" --diff "$WORK/py312" || true
  exit 0
fi

echo ""
echo "--- counter-examples (findings here are expected) ---"
ruff check --config "$WORK/ruff311.toml" --output-format concise "$WORK/expected" || true

echo ""
echo "--- real snippets (findings here are drift to fix) ---"
STATUS=0
ruff check --config "$WORK/ruff311.toml" --output-format concise "$WORK/py311" || STATUS=1
ruff check --config "$WORK/ruff312.toml" --output-format concise "$WORK/py312" || STATUS=1

echo ""
if [ "$STATUS" -eq 0 ]; then
  echo "PASS: every snippet survives the skill's own ruff config."
else
  echo "FAIL: fix the snippet in the markdown file named in each path above."
  echo "      Run with --diff to see exactly what ruff would rewrite."
fi
exit "$STATUS"
