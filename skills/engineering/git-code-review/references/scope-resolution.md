# Scope resolution

Turning what the user said into the exact set of changes to review. Getting this
wrong wastes the whole review, so resolve the scope before reading any code.

## Contents

- [Scope by intent](#scope-by-intent)
- [Relative and filtered history](#relative-and-filtered-history)
- [Resolving people](#resolving-people)
- [Time windows](#time-windows)
- [Multiple commits](#multiple-commits)

## Scope by intent

Default to **working tree plus staged changes** when no scope is given.

| User intent                | Git commands                                                                  |
| -------------------------- | ----------------------------------------------------------------------------- |
| Default (changed + staged) | `git status`, `git diff`, `git diff --cached`                                 |
| Unstaged only              | `git diff`                                                                    |
| Staged only                | `git diff --cached`                                                           |
| Single commit              | `git show <commit> --stat` then `git show <commit>`                           |
| Commit range               | `git log --oneline <base>..<head>`, `git diff <base>..<head>`                 |
| Branch vs base             | `git diff <base-branch>...HEAD` → use the merge-review workflow               |
| Last N commits             | `git log -n <N> --oneline`, then `git show` each or `git diff HEAD~<N>..HEAD` |
| Last commit by author      | `git log -1 --author=<author>`, `git show <sha>`                              |
| Time window by author      | `git log --since=<time> --author=<author>`, review commits or the net diff    |
| MR/PR number or URL        | Detect the host → platform CLI if available, else `git diff <base>...<head>`  |
| Current branch for merge   | `git diff <default-base>...HEAD` → use the merge-review workflow              |

Run independent commands in parallel. Start with `git status` unless reviewing a
specific commit or range, where it tells you nothing.

Use user-provided SHAs, refs, and ranges **exactly as given**. Ask once if genuinely
ambiguous, then proceed.

### Two-dot vs three-dot

`git diff base..head` shows the difference between the two endpoints. `git diff
base...head` shows only what happened on `head` since it diverged from `base`.

For branch and merge reviews you almost always want **three dots** — otherwise
changes that landed on `base` after the branch point show up as if the author had
reverted them, which produces confident, completely wrong findings.

## Relative and filtered history

| User says                               | Resolve to                                                           |
| --------------------------------------- | -------------------------------------------------------------------- |
| "last 5 commits", "recent 3 commits"    | `git log -n N --oneline`                                             |
| "last commit from me", "my last commit" | `git log -1 --author=<me> --oneline`                                 |
| "last commit from Alice"                | `git log -1 --author=Alice --oneline`                                |
| "past week's commits from me"           | `git log --since="1 week ago" --author=<me> --oneline`               |
| "last 2 weeks from Bob"                 | `git log --since="2 weeks ago" --author=Bob --oneline`               |
| "today's commits from me"               | `git log --since=midnight --author=<me> --oneline`                   |
| "yesterday from Jane"                   | `git log --since=yesterday --until=midnight --author=Jane --oneline` |

## Resolving people

**"me"** — read `git config user.email`, falling back to `git config user.name`.
`--author=` matches on a substring, so either works.

**A named contributor** — use the name or email as given. If nothing matches, list
the actual authors rather than guessing at a spelling:

```bash
git log --format='%an <%ae>' | sort -u | head -20
```

## Time windows

| Phrase        | Flag                        |
| ------------- | --------------------------- |
| "past week"   | `--since="1 week ago"`      |
| "past N weeks"| `--since="N weeks ago"`     |
| "past month"  | `--since="1 month ago"`     |
| "today"       | `--since=midnight`          |
| "yesterday"   | `--since=yesterday --until=midnight` |

## Multiple commits

- **Five or fewer** — review each with `git show`.
- **More than five** — summarize the log, review the net diff, then deep-dive only
  the risky commits.

Either way, **list the commits included** in the review header. Without it the
reader cannot tell whether their change was covered, and a review of unknown scope
is one they have to redo themselves.
