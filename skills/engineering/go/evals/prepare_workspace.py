#!/usr/bin/env python3
"""
Create the eval workspace layout from evals/evals.json.

Creates <skill-name>-workspace/iteration-1/eval-{id}/ with:
  - eval_metadata.json (prompt, eval_id, expectations)
  - with_skill/run-1/outputs/
  - without_skill/run-1/outputs/

Run from the skill root (parent of evals/) or pass --skill-dir.

Usage:
  python evals/prepare_workspace.py
  python evals/prepare_workspace.py --skill-dir /path/to/goperf-skill
  python evals/prepare_workspace.py --iteration 2
"""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare eval workspace from evals.json")
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=None,
        help="Skill root directory (default: parent of evals/ when script is in evals/)",
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=1,
        help="Iteration number (default: 1)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    skill_dir = args.skill_dir
    if skill_dir is None:
        skill_dir = script_dir.parent
    skill_dir = skill_dir.resolve()

    evals_path = skill_dir / "evals" / "evals.json"
    if not evals_path.exists():
        print(f"Error: {evals_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(evals_path) as f:
        data = json.load(f)

    skill_name = data.get("skill_name", "goperf-skill")
    workspace_dir = skill_dir.parent / f"{skill_name}-workspace"
    iter_dir = workspace_dir / f"iteration-{args.iteration}"

    for eval_entry in data.get("evals", []):
        eid = eval_entry.get("id")
        prompt = eval_entry.get("prompt", "")
        expectations = eval_entry.get("expectations", [])

        eval_name = f"eval-{eid}"
        eval_dir = iter_dir / eval_name
        eval_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "eval_id": eid,
            "eval_name": eval_name,
            "prompt": prompt,
            "expectations": expectations,
        }
        metadata_path = eval_dir / "eval_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")

        for config in ("with_skill", "without_skill"):
            run_dir = eval_dir / config / "run-1" / "outputs"
            run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Created {iter_dir}")
    print(f"  Evals: {[e.get('id') for e in data.get('evals', [])]}")
    print(f"  Workspace: {workspace_dir}")


if __name__ == "__main__":
    main()
