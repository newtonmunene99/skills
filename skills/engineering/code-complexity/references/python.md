# Python

Ruff carries both the cyclomatic rule (from mccabe) and the pylint refactor family,
which together cover more of the picture than the cyclomatic gate alone.

## Contents

- [The rules](#the-rules)
- [None of them are on by default](#none-of-them-are-on-by-default)
- [C901, the cyclomatic gate](#c901-the-cyclomatic-gate)
- [The PLR family](#the-plr-family)
- [No cognitive complexity](#no-cognitive-complexity)
- [Recommended config](#recommended-config)
- [Exemptions](#exemptions)

## The rules

| Code | Rule | Setting | Default |
| ---- | ---- | ------- | ------- |
| `C901` | [complex-structure](https://docs.astral.sh/ruff/rules/complex-structure/) | `lint.mccabe.max-complexity` | `10` |
| `PLR1702` | too-many-nested-blocks | `lint.pylint.max-nested-blocks` | `5` |
| `PLR0912` | too-many-branches | `lint.pylint.max-branches` | `12` |
| `PLR0915` | too-many-statements | `lint.pylint.max-statements` | `50` |
| `PLR0911` | too-many-return-statements | `lint.pylint.max-returns` | `6` |
| `PLR0913` | too-many-arguments | `lint.pylint.max-args` | `5` |
| `PLR0914` | too-many-locals | `lint.pylint.max-locals` | `15` |
| `PLR0916` | too-many-boolean-expressions | `lint.pylint.max-bool-expr` | `5` |

Unusually among the three ecosystems here, **ruff's defaults are already sensible.**
`max-complexity: 10` is McCabe's own number rather than a slackened version of it,
and `max-nested-blocks: 5` is a real nesting gate. The problem is not the values.

## None of them are on by default

**`C901` is not in ruff's default rule selection, and neither are the `PLR` rules.**
Ruff's defaults cover pycodestyle errors, pyflakes and a handful of others; the
complexity rules must be selected explicitly.

This is the Python equivalent of the golangci-lint default trap: a project with a
carefully-tuned `[tool.ruff.lint.mccabe]` block and no matching `select` entry has
configured a threshold that never runs. Check both.

```toml
[tool.ruff.lint]
# extend-select adds to the defaults; select replaces them entirely
extend-select = ["C901", "PLR"]
```

Prefer `extend-select` over `select` unless you intend to discard ruff's defaults —
`select = ["C901"]` turns off pyflakes along with everything else.

## C901, the cyclomatic gate

```toml
[tool.ruff.lint]
extend-select = ["C901"]

[tool.ruff.lint.mccabe]
max-complexity = 10
```

The rule is "one plus the number of decision points" — the standard shortcut. It
comes from the `mccabe` package's algorithm, which is why the setting lives under
`[tool.ruff.lint.mccabe]` rather than a ruff-specific namespace.

Python has no `match`-statement exemption equivalent to ESLint's `variant: "modified"`.
A `match` with twelve cases, or a long `elif` ladder dispatching on a string, scores
its full branch count and has to be handled with a `# noqa` and a reason.

If migrating from flake8, `max-complexity` there was the same setting under a
different name — the numbers transfer, unlike between unrelated tools.

## The PLR family

This is the part that makes Python's complexity story better than a bare cyclomatic
gate, and it maps closely onto the multi-metric approach:

- **`PLR1702` (max-nested-blocks, 5)** is the nesting-depth rule. It is the closest
  thing Python has to a readability signal, and the one to enable if you only enable
  one thing beyond `C901`. Nesting points at the offending line where `C901` labels a
  whole function.
- **`PLR0912` (max-branches, 12)** overlaps with `C901` but counts differently —
  branches rather than paths, so boolean operators do not inflate it. Running both is
  reasonable; expect some duplicate findings on the same function.
- **`PLR0915` (max-statements, 50)** and **`PLR0913` (max-args, 5)** are the size
  signals: is this function long, and does it need too much context to call?
- **`PLR0911` (max-returns, 6)** is the one to consider relaxing. Guard-clause style
  produces many early returns deliberately, and that style is usually an improvement
  in readability, not a regression. Raising it to 8–10 is defensible.
- **`PLR0914` (max-locals, 15)** proxies how much state a reader must track.

**`PLR0914` and `PLR1702` are preview rules** (still so in ruff 0.16), and both halves
of enabling them bite:

- **Without preview they are silent no-ops.** Ruff prints *"Selection `PLR1702` has no
  effect because preview is not enabled"* as a warning and then reports all checks
  passed. A selected rule that never runs is a missing gate that looks configured.
- **`preview = true` alone adopts every preview rule** in the groups already selected.
  On one real project that added 69 unrelated errors. Pair it with
  `explicit-preview-rules = true`, so only preview rules named by their full code run.

Check `ruff check --show-settings` or the warning output after enabling; never assume.

## No cognitive complexity

Ruff has no cognitive complexity rule, and neither does flake8's core. Python is the
weakest of the three ecosystems here for readability metrics.

The practical substitute is **`PLR1702` for nesting depth plus `PLR0915` for length**.
Between them they catch most of what cognitive complexity would, because nesting and
size are the two biggest drivers of the score. What they miss is the shorthand credit
— a long `match` statement will trip `PLR0912` even though it reads cleanly, and
there is no config flag to exempt it.

If cognitive complexity specifically matters, it means reaching outside ruff — a
SonarQube or SonarCloud scan carries it for Python. Say that plainly rather than
implying ruff covers it.

## Recommended config

```toml
[tool.ruff.lint]
# PLR1702 is a preview rule: without preview it silently does nothing, and preview
# without explicit-preview-rules turns on every preview rule in the selected groups.
preview = true
explicit-preview-rules = true
extend-select = [
  "C901",     # cyclomatic complexity
  "PLR1702",  # nesting depth — the readability signal
  "PLR0912",  # branches
  "PLR0913",  # arguments
  "PLR0915",  # statements
]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-nested-blocks = 4
max-branches = 12
max-args = 6
max-statements = 50
max-returns = 8       # relaxed: guard clauses are good style

[tool.ruff.lint.per-file-ignores]
# Fixtures and parametrised tests legitimately run long and branch wide.
# The leading **/ also catches packages/*/tests in a monorepo.
"**/tests/**" = ["C901", "PLR0912", "PLR0913", "PLR0915", "PLR1702"]
```

If the project already has a `per-file-ignores` entry for its tests, merge these codes
into it rather than adding a second key for the same files.

In a monorepo, mind where the block lands. Ruff uses the closest `pyproject.toml` that
has a `[tool.ruff]` section and does not merge it with parents, so adding this to a
package's `pyproject.toml` silently drops the root's ruff settings for that package.
Put it in the root config, or start the package's section with
`extend = "../../pyproject.toml"` (the relative path to the root).

Deliberate choices here: nesting is tightened to 4 while the cyclomatic gate stays at
McCabe's 10, and `max-returns` is loosened because the default punishes a style worth
encouraging.

Ruff is also the formatter (`ruff format`), and formatting has no bearing on any of
these scores — complexity is computed from the syntax tree, not the layout. Nobody
can lower a score by reformatting.

## Scoring every function

Ruff reports only violations, so a per-function table for the report needs the
thresholds forced to the floor and the scores parsed out of the messages:

```bash
ruff check <scope> --isolated --output-format json \
  --select C901,PLR0912,PLR0915,PLR1702 \
  --preview --config 'lint.explicit-preview-rules=true' \
  --config 'lint.mccabe.max-complexity=0' \
  --config 'lint.pylint.max-branches=0' \
  --config 'lint.pylint.max-statements=0' \
  --config 'lint.pylint.max-nested-blocks=1'
```

Each message carries the score, e.g. *"`f` is too complex (7 > 0)"*, so take the first
number in the parentheses and key the row by `filename` plus the function name. Use
`--isolated` so the project's own thresholds and ignores do not hide functions;
depth 1 never shows up, which is fine because it is never a finding. Group by package
from the file path in the same script that parses the JSON, rather than re-deriving
counts with `sed` afterwards.

## Exemptions

```python
# One branch per supported event type; each is a single dispatch call, so the
# score reflects branch count rather than difficulty.
def handle_event(event: Event) -> None:  # noqa: C901
    match event:
        case OrderPlaced():
            ...
```

Ruff honours `# noqa: C901` on the `def` line. It does not enforce that a reason is
present, so the convention has to be a review habit: **a bare `# noqa` with no
comment is the same as no gate.**

For a whole file, prefer `per-file-ignores` in `pyproject.toml` over a file-level
`# ruff: noqa` — the config version is visible to everyone reading the project
settings rather than buried at the top of one module.
