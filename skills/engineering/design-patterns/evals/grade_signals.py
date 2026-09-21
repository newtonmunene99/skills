#!/usr/bin/env python3
"""Scan eval outputs for the textual signals declared in evals.json.

This does not replace the grader — several expectations ("distinguishes the
boundary from the interior") need judgement, and no regex settles them. What it
does is turn the *mechanical* expectations into reproducible evidence, so a
finding doesn't drift between iterations because a human read the answer at a
different time of day.

Feed the output to the grader agent alongside the answer, or read it directly to
see at a glance whether the with-skill and baseline columns actually differ.

Usage:
  python evals/grade_signals.py                 # iteration 1
  python evals/grade_signals.py --iteration 2
  python evals/grade_signals.py --json          # machine-readable
"""

import argparse
import json
import re
import sys
from pathlib import Path

CONFIGS = ("with_skill", "without_skill")


def scan(text: str, patterns: list[str]) -> dict[str, bool]:
    return {p: bool(re.search(p, text, re.I)) for p in patterns}


def main() -> None:
    ap = argparse.ArgumentParser(description="Check eval outputs for declared signals")
    ap.add_argument("--skill-dir", type=Path, default=None)
    ap.add_argument("--iteration", type=int, default=1)
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    skill_dir = (args.skill_dir or Path(__file__).resolve().parent.parent).resolve()
    data = json.loads((skill_dir / "evals" / "evals.json").read_text())
    skill_name = data["skill_name"]
    iter_dir = skill_dir.parent / f"{skill_name}-workspace" / f"iteration-{args.iteration}"

    if not iter_dir.exists():
        print(f"Error: {iter_dir} not found — run prepare_workspace.py first", file=sys.stderr)
        sys.exit(1)

    report: dict = {"skill": skill_name, "iteration": args.iteration, "evals": []}
    missing = 0

    for entry in data["evals"]:
        eid = entry["id"]
        signals = entry.get("signals", {})
        present, absent = signals.get("present", []), signals.get("absent", [])
        row = {"id": eid, "name": entry.get("name", f"eval-{eid}"), "configs": {}}

        for config in CONFIGS:
            out_dir = iter_dir / f"eval-{eid}" / config / "run-1" / "outputs"
            files = sorted(out_dir.glob("*")) if out_dir.exists() else []
            if not files:
                row["configs"][config] = {"status": "no output"}
                missing += 1
                continue
            text = "\n".join(f.read_text(errors="replace") for f in files if f.is_file())
            hits = scan(text, present)
            # An "absent" pattern scoring True is a miss — the text contains
            # something the skill says not to write.
            avoids = {p: not v for p, v in scan(text, absent).items()}
            score = sum(hits.values()) + sum(avoids.values())
            total = len(present) + len(absent)
            row["configs"][config] = {
                "status": "ok",
                "score": score,
                "total": total,
                "present": hits,
                "avoided": avoids,
                "chars": len(text),
            }
        report["evals"].append(row)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"{skill_name} — iteration {args.iteration}\n")
    for row in report["evals"]:
        w = row["configs"].get("with_skill", {})
        b = row["configs"].get("without_skill", {})
        if w.get("status") != "ok" or b.get("status") != "ok":
            print(f"  {row['id']}. {row['name']}: incomplete "
                  f"(with_skill={w.get('status')}, baseline={b.get('status')})")
            continue
        delta = w["score"] - b["score"]
        arrow = "+" if delta > 0 else ""
        print(f"  {row['id']}. {row['name']}")
        print(f"     with skill {w['score']}/{w['total']}   baseline {b['score']}/{b['total']}   "
              f"delta {arrow}{delta}")
        for p in sorted(set(list(w["present"]) + list(w["avoided"]))):
            wv = w["present"].get(p, w["avoided"].get(p))
            bv = b["present"].get(p, b["avoided"].get(p))
            if wv != bv:  # only the discriminating signals are interesting
                print(f"       {'PASS' if wv else 'fail'} / {'PASS' if bv else 'fail'}  {p}")
        print()

    if missing:
        print(f"{missing} run(s) had no output — those evals can't be scored yet.")


if __name__ == "__main__":
    main()
