# Merge review workflow

For changes intended to merge — on a private git server, self-hosted GitLab or Gitea,
or a public host. Git is the source of truth throughout; platform tools only add
metadata and optional comment posting.

## Contents

- [Step 0 — Resolve the diff](#step-0--resolve-the-diff)
- [Step 1 — Pre-flight checks](#step-1--pre-flight-checks)
- [Step 2 — Load project guidelines](#step-2--load-project-guidelines)
- [Step 3 — Review the diff](#step-3--review-the-diff)
- [Step 4 — Validate each finding](#step-4--validate-each-finding)
- [Step 5 — Output](#step-5--output)
- [Step 6 — Post comments](#step-6--post-comments-only-if-asked)
- [Step 7 — Inline comments](#step-7--inline-comments-hosted-only)

## Step 0 — Resolve the diff

Determine scope in this order:

1. **User names a base branch** ("vs main", "against develop") → use it.
2. **User gives an MR/PR number or URL** → inspect the remote and use the platform
   CLI if available. Otherwise fetch the head by number —
   `git fetch origin refs/merge-requests/<N>/head` on GitLab, `refs/pull/<N>/head` on
   GitHub and Gitea — and detect the base as in item 3. Ask for the base only if
   detection fails.
3. **User says "current branch" / "my changes for merge"** → detect the default branch:
   ```bash
   git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
   ```
   Fall back to `main`, and confirm if ambiguous.
4. **User gives an explicit range** → `git diff <base>..<head>` or three-dot
   `git diff <base>...<head>`.

Core commands, which work on every host:

```bash
git fetch origin <base> <head>    # if refs may be stale
git log --oneline <base>..<head>
git diff <base>...<head>           # three-dot: changes on head since diverging
git diff --stat <base>...<head>
```

If the fetch fails — no network, no credentials — carry on with the local refs and
say so in the review. A silent failure means reviewing stale code with no one aware
of it.

### Optional hosted metadata

Detect the remote with `git remote get-url origin`:

| Remote pattern                   | CLI (if installed)             | Fetch title / body / state                                                    |
| -------------------------------- | ------------------------------ | ----------------------------------------------------------------------------- |
| github.com                       | `gh pr view`, `gh pr diff`     | `--json title,body,state,isDraft,headRefOid`                                  |
| gitlab.com or self-hosted GitLab | `glab mr view`, `glab mr diff` | `-F json` (`--output json`)                                                   |
| Other / private / no CLI         | —                              | Use `git log` subject lines and the branch name; ask the user for a description if needed |

**If a CLI is unavailable or auth fails, continue with `git diff`.** Do not stop the
review. The diff is the thing being reviewed; the metadata was only ever context.

Use the title and description — from the platform or from the user — to understand
what the author was trying to do. A change that works but does not do what the
description claims is a finding.

## Step 1 — Pre-flight checks

Stop if any of these apply, and say which:

- **No diff.** `git diff <base>...<head>` is empty. Nothing to review.
- **Closed or merged**, confirmed by platform metadata — unless the user asked for a
  historical review.
- **Draft**, unless the user explicitly asked to review a draft.
- **No review needed** — a trivial or no-op change the user said to skip.
- **Already reviewed** — only when the user did not ask for a re-review *and*
  platform comments show a recent substantive review *and* there are no new commits
  since it.

## Step 2 — Load project guidelines

Find guideline files relevant to **the modified paths only**:

1. Repo root: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.cursor/rules/`
2. For each directory containing a changed file: any nested `AGENTS.md`,
   `CLAUDE.md`, `.cursor/rules/`

Apply a guideline file only when it covers the changed file or one of its parent
directories. A rule scoped to `frontend/` says nothing about a change in `api/`.

**Quote the exact rule** when flagging a violation. An unquoted "this violates the
style guide" is unactionable and unfalsifiable.

## Step 3 — Review the diff

Two passes, in this order:

1. **Guidelines compliance** — unambiguous violations in the changed code.
2. **Bugs and correctness** — in **introduced or changed code only**. The one
   exception: if the change bumps a dependency, untouched code that the bump stops
   from building is in scope. Confirm it with one build or typecheck.

Apply the signal bar from `SKILL.md`. Merge reviews are high signal only.

## Step 4 — Validate each finding

Before writing anything up, confirm for each candidate:

- The bug is real — trace it once more through the actual changed code.
- The guideline genuinely applies to this path.
- It is not a false positive.

Drop anything that does not survive. This step exists because the cost of a wrong
finding is far higher than the cost of a missed one: a wrong finding burns the
author's time and teaches them to discount the next review.

## Step 5 — Output

Read [reporting.md](reporting.md) before writing anything. It defines the template,
the `file:line` format for each issue, and the allowed verdicts.

## Step 6 — Post comments (only if asked)

Post to the host **only** when the user explicitly requests it (`--comment`,
"comment on the MR", "leave a review") **and** a platform CLI is available.

| Situation                                     | Action                                          |
| --------------------------------------------- | ----------------------------------------------- |
| No CLI, or private git without an API         | Output the review in chat — the user posts it   |
| No issues + comment requested + CLI available | Post a summary comment via the platform CLI     |
| Issues + comment requested + CLI available    | Post inline comments (step 7)                   |
| Comment not requested                         | Stop after step 5                               |

No-issues comment template:

```markdown
## Code review

No issues found. Checked for bugs and project guideline compliance.
```

Platform commands:

- **GitHub:** `gh pr comment`; `gh api .../pulls/.../comments` for inline.
- **GitLab:** `glab mr note create <N> -m ...`; for inline, add `--file <path> --line <n>`.
  Older glab releases lack those flags; use `glab api` against the MR's
  `discussions` endpoint instead.
- **Other hosts:** output `file:line` findings with suggested comment text. Do not
  guess at an API.

## Step 7 — Inline comments (hosted only)

- **One comment per unique issue.** Repeating the same point across five files
  reads as noise even when each instance is real; make the point once and reference
  the others.
- Brief description, plus the guideline citation where one applies.
- **For small fixes (≤5 lines)**, include a committable suggestion where the
  platform supports it — GitHub ` ```suggestion ` blocks, GitLab suggestion syntax.
- **For larger fixes**, describe the fix without a suggestion block.
- **Only suggest code that fully fixes the issue.** A partial suggestion that gets
  committed leaves a half-fixed bug and no open comment tracking it.

For code links in external comments, use the host's URL format with a **full commit
SHA** and line range — branch-relative links rot on the next push. If the host URL
format is unknown, cite `file:line` in the commit being reviewed.
