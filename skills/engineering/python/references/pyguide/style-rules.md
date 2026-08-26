# Style Rules (pyguide §3, excluding docstrings/naming/types)

Distilled from [Google Python Style Guide §3](https://google.github.io/styleguide/pyguide.html#3-python-style-rules). For docstrings see [docstrings.md](docstrings.md), for naming see [naming.md](naming.md), for type annotations see [type-annotations.md](type-annotations.md).

## Contents

- [Semicolons](#semicolons)
- [Line length](#line-length)
- [Parentheses](#parentheses)
- [Indentation](#indentation)
- [Blank lines](#blank-lines)
- [Whitespace](#whitespace)
- [Shebang line](#shebang-line)
- [Block and inline comments](#block-and-inline-comments)
- [Strings](#strings)
- [Logging strings](#logging-strings)
- [Error messages](#error-messages)
- [Files, sockets, and stateful resources](#files-sockets-and-stateful-resources)
- [TODO comments](#todo-comments)
- [Imports formatting](#imports-formatting)
- [Statements](#statements)
- [Getters and setters](#getters-and-setters)
- [Main](#main)
- [Function length](#function-length)

## Semicolons

Never terminate a line with `;`. Never put two statements on one line.

## Line length

**Max 80 characters.** Exceptions:

- Long import statements.
- URLs / pathnames / long flags in comments.
- Long unbroken string constants (URLs, pathnames).
- `# noqa` / `# type: ignore` / `# pylint: disable` comments.

**Never use `\` for continuation.** Use implicit joining inside `()`, `[]`, `{}`. Add an extra pair of parentheses if needed.

```python
# Yes
foo_bar(self, width, height, color="black", design=None, x="foo",
        emphasis=None, highlight=0)

if (width == 0 and height == 0
        and color == "red" and emphasis == "strong"):
    ...

with (
    very_long_first_expression_function() as spam,
    very_long_second_expression_function() as beans,
    third_thing() as eggs,
):
    place_order(eggs, beans, spam, beans)
```

**Break at the highest syntactic level.** If you must break twice, break at the same level both times.

**Long literal strings:** use implicit concatenation inside parentheses.

```python
x = ("This will build a very long long "
     "long long long long long long string")
```

Docstring summary lines must fit in 80 chars.

`ruff format` (or `black`) handles most of this. Configure `line-length = 80` in `pyproject.toml`.

## Parentheses

Use sparingly. Do not use them in `return` or `if` statements unless required for line continuation or to build a tuple.

```python
# Yes
if foo:
    bar()
return foo
return spam, beans
onesie = (foo,)  # 1-element tuple

# No
if (x):
    bar()
return (foo)
```

## Indentation

- **4 spaces.** Never tabs.
- Wrapped elements either align with the opening delimiter or use a 4-space hanging indent.
- Closing brackets go at the end of the expression or on their own line at the same indent as the opening line.
- **Trailing commas** in multi-line sequences (they help the formatter and diff hygiene). Also for 1-element tuples.

```python
# Yes — 4-space hanging indent, closing paren on new line
foo = long_function_name(
    var_one, var_two, var_three,
    var_four,
)
meal = (
    spam,
    beans,
)

# No — stuff on first line with hanging children
foo = long_function_name(var_one, var_two,
    var_three, var_four)
```

## Blank lines

- **Two** blank lines between top-level definitions (functions/classes).
- **One** blank line between method definitions and between the class docstring and the first method.
- No blank line after a `def` line.
- Use blank lines inside functions to group logical steps.

## Whitespace

- Standard typographic spacing.
- **No** whitespace inside `()`, `[]`, `{}`.
- **No** whitespace before `,`, `;`, `:`. Yes after (except at end of line).
- **No** whitespace before an opening paren/bracket in a call or index: `spam(1)`, `dict["k"]`.
- **No** trailing whitespace.
- **One** space around `=`/comparison/boolean operators. Use judgment for arithmetic.
- **No** spaces around `=` in keyword arguments **unless** the parameter has an annotation:

```python
# Yes
def f(a, b=0): ...
def f(a, b: int = 0): ...
call(a=1, b=2)

# No
def f(a, b = 0): ...
def f(a, b: int=0): ...
```

- **Do not** vertically align `:`, `#`, `=` on consecutive lines — it's a maintenance burden.

## Shebang line

Most `.py` files need no shebang. If a file is a directly executable entry point, use `#!/usr/bin/env python3`.

## Block and inline comments

- Explain **why**, not what.
- Block comments before tricky code; short comments at end of line for non-obvious operations.
- Inline comments start at least 2 spaces after the code, then `# `.
- Full sentences, proper punctuation, and capitalization.

```python
# We use a weighted dictionary search: extrapolate position from the
# largest value and array size, then binary-search from there.

if i & (i - 1) == 0:  # True if i is 0 or a power of 2.
    ...
```

Don't narrate what the code does. Reserve comments for intent, invariants, trade-offs, references (PEPs, issue links, papers).

## Strings

**Use f-strings.** The pyguide also permits `%` formatting and `.format()`, but ruff's `UP` rules — which this skill recommends selecting — rewrite both to f-strings (`UP031`, `UP032`). In a new project, f-strings are the only form that survives `ruff check --fix`.

A single `+` between two strings is OK; do not accumulate a string with `+=` in a loop.

```python
# Yes
x = f"name: {name}; score: {n}"

# Legal per the pyguide, but `ruff --fix` rewrites both to f-strings
x = "%s, %s!" % (imperative, expletive)          # UP031
x = "name: {}; score: {}".format(name, n)        # UP032

# Yes — accumulate then join
parts = ["<table>"]
for last, first in employees:
    parts.append(f"<tr><td>{last}, {first}</td></tr>")
parts.append("</table>")
table = "".join(parts)

# No
x = "name: " + name + "; score: " + str(n)
# No — quadratic accumulation
table = "<table>"
for last, first in employees:
    table += f"<tr><td>{last}, {first}</td></tr>"
```

**Quote character:** pick `'` or `"` and be consistent within a file. Use the other one to avoid escaping. `ruff format`/`black` default to `"`.

**Multi-line strings:** use `"""` (always for docstrings). If you need to avoid indentation bleeding into the string, either concatenate single lines or use `textwrap.dedent`.

```python
import textwrap

msg = textwrap.dedent("""\
    First line.
    Second line.
""")
```

## Logging strings

**Never use f-strings in logging calls.** Pass the pattern as a literal and the arguments separately. This lets the logging system (a) skip formatting when the level is disabled and (b) group log messages by pattern in aggregators.

```python
import logging
logger = logging.getLogger(__name__)

# Yes
logger.info("Current $PAGER is: %s", os.getenv("PAGER", default=""))
logger.error("Cannot write to home directory, $HOME=%r", homedir)

# No — always formatted, breaks aggregation
logger.info(f"Current $PAGER is: {os.getenv('PAGER', '')}")
```

The one place `%` formatting stays: **logging calls**, where you pass the pattern and args separately and never format them yourself. Ruff knows the difference and leaves those alone.

See [../modern/logging.md](../modern/logging.md) for full logging setup.

## Error messages

Three rules:

1. The message must precisely match the actual error condition.
2. Interpolated pieces must be clearly identifiable — use `{p=}` or `{p!r}`.
3. Text should be greppable and stable — avoid embedding user input in the middle without markers.

```python
# Yes
if not 0 <= p <= 1:
    raise ValueError(f"Not a probability: {p=}")

try:
    os.rmdir(workdir)
except OSError as error:
    logger.warning("Could not remove directory (reason: %r): %r", error, workdir)
```

```python
# No — assumes the reason, misleading
try:
    os.rmdir(workdir)
except OSError:
    logger.warning("Directory already was deleted: %s", workdir)
```

## Files, sockets, and stateful resources

**Always use `with`.** Do not rely on `__del__` for cleanup — GC timing is not guaranteed.

```python
with open("hello.txt") as f:
    for line in f:
        print(line)
```

`urllib.request.urlopen` (not `urllib.urlopen` — that's Python 2) is already a context manager:

```python
import urllib.request

with urllib.request.urlopen("https://example.com") as page:
    for line in page:
        ...
```

For objects that have `.close()` but no `__enter__`/`__exit__` — typically older third-party handles — wrap them in `contextlib.closing`:

```python
import contextlib

with contextlib.closing(legacy_lib.open_cursor()) as cursor:
    for row in cursor:
        ...
```

Extends to DB connections, mmap mappings, matplotlib figures, `asyncio.TaskGroup`, etc.

## TODO comments

Format: `# TODO: <link or bug id> - <explanation>`.

```python
# TODO: crbug.com/192795 - Investigate cpufreq optimizations.
# TODO: https://github.com/org/repo/issues/42 - Handle Unicode filenames.
```

- The context must be a link, bug id, or a concrete future event ("Remove when all clients handle X"). Avoid `# TODO(username)` — people change teams.
- Old form `# TODO(link): text` is discouraged in new code.

## Imports formatting

- Imports on separate lines. Exception: multiple symbols from `typing` or `collections.abc` on one line are allowed.
- Imports at the **top of the file**, right after the module docstring and before any code.
- Grouped, each group separated by a blank line, sorted lexicographically within each group:
  1. `from __future__` imports
  2. Standard library imports
  3. Third-party imports
  4. First-party (repo/project) imports

```python
"""Module docstring."""

from __future__ import annotations

import collections
import queue
import sys
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

import httpx
import tensorflow as tf
from absl import app, flags

from myproject.backend import huxley
from myproject.backend.state_machine import main_loop
```

`ruff`'s `I` rules (isort) enforce this automatically — including the ordering *within* each group: plain `import x` statements first, then `from x import y`, each block sorted lexicographically. Don't hand-order imports; run `ruff check --fix`.

## Statements

**One statement per line.** The pyguide tolerates `if foo: bar(foo)` when the whole thing fits, but ruff's `E701` (enabled by `select = ["E"]`, which this skill recommends) flags it. Write the two-line form in new code:

```python
# Yes
if foo:
    bar(foo)

# No — E701, and never with try/except or if/else
if foo: bar(foo)
```

The stub-body form (`def f() -> int: ...` in a `Protocol` or an `@overload`) is the one shape that stays on one line.

## Getters and setters

Only when meaningful. If it's just `return self._x` / `self._x = value`, make the attribute public.

- If getting or setting invalidates or rebuilds state, use a **setter method** — the call site hints that non-trivial work is happening.
- Follow `get_foo()` / `set_foo()` naming.
- Consider `@property` for simple derived values (see [language-rules.md](language-rules.md#properties)).

## Main

Import-safety matters (`pydoc`, tests, tools). Put main logic in a `main()` function guarded by `if __name__ == "__main__":`.

```python
def main() -> None:
    ...

if __name__ == "__main__":
    main()
```

With `absl`:

```python
from absl import app

def main(argv: Sequence[str]) -> None:
    ...

if __name__ == "__main__":
    app.run(main)
```

**Nothing at module scope should have observable side effects at import time** (no HTTP calls, no reading `sys.argv`, no logging setup that hits I/O).

## Function length

- Prefer small, focused functions.
- No hard limit. If a function passes ~40 lines, consider whether it can be split without hurting structure.
- Long functions grow bugs over time as people add cases. Splitting eagerly is cheap; splitting later is expensive.
