#!/usr/bin/env python3
"""Create the eval workspace layout from evals/evals.json.

Creates <skill-name>-workspace/iteration-N/eval-{id}/ with:
  - eval_metadata.json (eval_id, eval_name, prompt, expectations, files)
  - with_skill/run-1/outputs/
  - without_skill/run-1/outputs/
  - with_skill/run-1/project/ and without_skill/run-1/project/, a fresh copy
    of the eval's fixture files, when the eval lists any under "files"

The workspace is a sibling of the skill directory and is gitignored
(`*-workspace/`), so runs never pollute the repo.

Run from the skill root (parent of evals/) or pass --skill-dir.

Usage:
  python evals/prepare_workspace.py
  python evals/prepare_workspace.py --skill-dir /path/to/skill
  python evals/prepare_workspace.py --iteration 2
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare eval workspace from evals.json")
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=None,
        help="Skill root directory (default: parent of evals/ when run from evals/)",
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=1,
        help="Iteration number (default: 1)",
    )
    args = parser.parse_args()

    skill_dir = (args.skill_dir or Path(__file__).resolve().parent.parent).resolve()

    evals_path = skill_dir / "evals" / "evals.json"
    if not evals_path.exists():
        print(f"Error: {evals_path} not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(evals_path.read_text())

    # skill_name drives the workspace directory name; it must match the
    # `name` in SKILL.md so the viewer and benchmark labels line up.
    skill_name = data.get("skill_name")
    if not skill_name:
        print(f"Error: {evals_path} has no 'skill_name'", file=sys.stderr)
        sys.exit(1)

    workspace_dir = skill_dir.parent / f"{skill_name}-workspace"
    iter_dir = workspace_dir / f"iteration-{args.iteration}"

    evals = data.get("evals", [])
    if not evals:
        print(f"Error: {evals_path} has no evals", file=sys.stderr)
        sys.exit(1)

    for entry in evals:
        eid = entry.get("id")
        eval_dir = iter_dir / f"eval-{eid}"
        eval_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "eval_id": eid,
            # A descriptive name reads better than "eval-3" in the viewer.
            "eval_name": entry.get("name", f"eval-{eid}"),
            "prompt": entry.get("prompt", ""),
            "expectations": entry.get("expectations", []),
            "files": entry.get("files", []),
        }
        (eval_dir / "eval_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

        # Fixtures live in evals/files/<eval-name>/; each run gets its own copy,
        # with paths relative to that folder, so one run's edits can't leak
        # into the other's starting point.
        fixture_root = skill_dir / "evals" / "files" / entry.get("name", "")
        for config in ("with_skill", "without_skill"):
            run_dir = eval_dir / config / "run-1"
            (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
            for rel in entry.get("files", []):
                src = skill_dir / rel
                if not src.is_file():
                    print(f"Error: eval {eid} lists missing file {rel}", file=sys.stderr)
                    sys.exit(1)
                dest = run_dir / "project" / src.relative_to(fixture_root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

    print(f"Created {iter_dir}")
    print(f"  Skill:     {skill_name}")
    print(f"  Evals:     {[e.get('id') for e in evals]}")
    print(f"  Workspace: {workspace_dir}")


if __name__ == "__main__":
    main()
