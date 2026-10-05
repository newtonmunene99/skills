#!/usr/bin/env python3
"""Create the eval workspace layout from evals/evals.json.

Creates <skill-name>-workspace/iteration-N/eval-{id}/ with:
  - eval_metadata.json (eval_id, eval_name, prompt, expectations)
  - with_skill/run-1/outputs/
  - without_skill/run-1/outputs/
  - <config>/run-1/repo/, for an eval with a fixture under evals/files/<name>/

A fixture is plain files, since a committed .git directory would be recorded as a
nested repo rather than as files. `base/` becomes the first commit on `main`;
`change/` is laid over it, then committed on `fixture_branch` when the eval sets
one, or left uncommitted as a working-tree change when it does not. Each config
gets its own repo so a run that edits files cannot leak into the other.

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
import os
import shutil
import subprocess
import sys
from pathlib import Path

# A fixed identity and date keep commit SHAs identical across iterations.
GIT_ENV = {
    "GIT_AUTHOR_NAME": "Sam Rivera",
    "GIT_AUTHOR_EMAIL": "sam@example.com",
    "GIT_COMMITTER_NAME": "Sam Rivera",
    "GIT_COMMITTER_EMAIL": "sam@example.com",
    "GIT_AUTHOR_DATE": "2026-09-28T10:00:00Z",
    "GIT_COMMITTER_DATE": "2026-09-28T10:00:00Z",
}


def git(repo: Path, *args: str) -> None:
    env = {**os.environ, **GIT_ENV}
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)


def build_repo(fixture: Path, repo: Path, branch: str | None, message: str) -> None:
    """Create a git repo from fixture/base, with fixture/change applied on top."""
    if repo.exists():
        shutil.rmtree(repo)
    shutil.copytree(fixture / "base", repo)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "initial import")
    if branch:
        git(repo, "checkout", "-q", "-b", branch)
    shutil.copytree(fixture / "change", repo, dirs_exist_ok=True)
    if branch:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message)


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
        }
        (eval_dir / "eval_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

        fixture = skill_dir / "evals" / "files" / metadata["eval_name"]
        if (fixture / "base").is_dir():
            # Tells the runner to start in the built repo, not the raw fixture files.
            metadata["repo"] = "<config>/run-1/repo"
            (eval_dir / "eval_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        for config in ("with_skill", "without_skill"):
            run_dir = eval_dir / config / "run-1"
            (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
            if (fixture / "base").is_dir():
                build_repo(
                    fixture,
                    run_dir / "repo",
                    entry.get("fixture_branch"),
                    entry.get("fixture_commit_message", "change"),
                )

    print(f"Created {iter_dir}")
    print(f"  Skill:     {skill_name}")
    print(f"  Evals:     {[e.get('id') for e in evals]}")
    print(f"  Workspace: {workspace_dir}")


if __name__ == "__main__":
    main()
