#!/usr/bin/env python3
"""Create the eval workspace layout from evals/evals.json.

Creates <skill-name>-workspace/iteration-N/eval-{id}/ with:
  - eval_metadata.json (eval_id, eval_name, prompt, expectations)
  - with_skill/run-1/outputs/
  - without_skill/run-1/outputs/
  - <config>/run-1/project/, a fresh copy of the eval's fixture files, when the
    eval lists any. The run uses it as its working directory, so each run can
    edit its own copy without affecting the other. It is its own git repository
    with the fixture committed, so "the repo root" means the fixture root and
    `git status` shows what the run changed.

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
import subprocess
import sys
from pathlib import Path


def fixture_relpath(path: str, eval_name: str) -> Path:
    """Path of a fixture file inside the project copy.

    Files under evals/files/<eval-name>/ keep their layout below that directory, so
    the fixture is a project tree; anything else lands at the project root.
    """
    prefix = Path("evals") / "files" / eval_name
    rel = Path(path)
    try:
        return rel.relative_to(prefix)
    except ValueError:
        return Path(rel.name)


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

        name = entry.get("name", f"eval-{eid}")
        files = entry.get("files", [])
        metadata = {
            "eval_id": eid,
            # A descriptive name reads better than "eval-3" in the viewer.
            "eval_name": name,
            "prompt": entry.get("prompt", ""),
            "expectations": entry.get("expectations", []),
        }
        if files:
            metadata["files"] = [str(fixture_relpath(f, name)) for f in files]
        (eval_dir / "eval_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

        for config in ("with_skill", "without_skill"):
            run_dir = eval_dir / config / "run-1"
            (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
            if not files:
                continue
            # Start from a clean copy: an earlier run may have edited the project.
            project = run_dir / "project"
            shutil.rmtree(project, ignore_errors=True)
            for f in files:
                src = skill_dir / f
                if not src.is_file():
                    print(f"Error: eval {eid} lists missing file {f}", file=sys.stderr)
                    sys.exit(1)
                dest = project / fixture_relpath(f, name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            # Commit the fixture so `git status` in project/ shows what the run changed.
            git = ["git", "-C", str(project), "-c", "user.name=eval"]
            git += ["-c", "user.email=eval@localhost", "-c", "commit.gpgsign=false"]
            subprocess.run([*git, "init", "-q"], check=True)
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-q", "--no-verify", "-m", "fixture"], check=True)

    print(f"Created {iter_dir}")
    print(f"  Skill:     {skill_name}")
    print(f"  Evals:     {[e.get('id') for e in evals]}")
    print(f"  Workspace: {workspace_dir}")


if __name__ == "__main__":
    main()
