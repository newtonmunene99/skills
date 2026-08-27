# Docstrings (pyguide §3.8)

Distilled from [Google Python Style Guide §3.8](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings). Docstrings follow **Google style** (`Args:` / `Returns:` / `Raises:`) — see also [PEP 257](https://peps.python.org/pep-0257/).

## General rules

- Use triple double quotes: `"""..."""`. Always, including for one-liners.
- **First line = one-sentence summary**, ends with `.`, `?`, or `!`. Fits in 80 chars.
- If more than one line, put a blank line after the summary; the rest is aligned with the opening quote.
- Descriptive style (`"""Fetches rows from a Bigtable."""`) or imperative (`"""Fetch rows..."""`) — pick one and stay consistent within a file.
- Extract with `pydoc`, use `__doc__` for programmatic access.

## Modules

Every module starts with a docstring describing its purpose and typical usage.

```python
"""One-line summary of the module.

Longer description if useful — what problems the module solves, key
classes/functions exported, and a small usage example.

Typical usage example:

    foo = ClassFoo()
    bar = foo.function_bar()
"""
```

**Test modules** don't require a docstring, but add one when there's something the reader needs (unusual setup, external dependency, how to update golden files, etc.).

## Functions and methods

A docstring is required whenever the function is:

- part of the public API,
- non-trivial in size, or
- has non-obvious logic.

Describe **what it does and how to call it**, not how it works internally. Side effects (mutation, I/O, blocking) **must** be documented.

### Sections

Each optional section header ends with a colon. Body uses a hanging indent of 2 or 4 spaces (be consistent within a file — 4 is common).

- **`Args:`** — one entry per parameter. `name: description`. If the description wraps, indent 2 or 4 more. Mention `*args` / `**kwargs` if accepted. Include types only if there's no annotation.
- **`Returns:`** (or **`Yields:`** for generators) — describes semantics. Omit if the function returns `None` or if the summary sentence already covers it (e.g. `"""Returns the number of rows."""`). Never document a tuple return as if it were multiple returns — describe it as `A tuple (a, b) where a is ..., b is ...`.
- **`Raises:`** — every exception that is part of the interface. Do **not** document exceptions raised by API misuse (that would make bad behavior part of the API).

### Full example

```python
def fetch_smalltable_rows(
    table_handle: smalltable.Table,
    keys: Sequence[bytes | str],
    require_all_keys: bool = False,
) -> Mapping[bytes, tuple[str, ...]]:
    """Fetches rows from a Smalltable.

    Retrieves rows pertaining to the given keys from the Table instance
    represented by ``table_handle``. String keys will be UTF-8 encoded.

    Args:
        table_handle: An open smalltable.Table instance.
        keys: A sequence of strings representing the key of each row
          to fetch. String keys will be UTF-8 encoded.
        require_all_keys: If True, only rows with values set for all
          keys will be returned.

    Returns:
        A dict mapping keys to the corresponding row data fetched.
        Each row is represented as a tuple of strings. For example::

            {
                b"Serak": ("Rigel VII", "Preparer"),
                b"Zim":   ("Irk", "Invader"),
            }

        Returned keys are always bytes. Missing keys are omitted when
        ``require_all_keys`` is False.

    Raises:
        OSError: An error occurred accessing the smalltable.
    """
```

Line-break-form for `Args:` when descriptions are long is also allowed — pick one style per file:

```python
    Args:
      table_handle:
        An open smalltable.Table instance.
      keys:
        A sequence of strings representing the key of each row.
```

### Overridden methods

If a method overrides a base-class method and its contract is unchanged, decorate with `@override` (from `typing` in 3.12+; `typing_extensions` otherwise) and skip the docstring — `@override` tells the reader "see base class".

```python
from typing import override  # 3.12+

class Child(Parent):
    @override
    def do_something(self) -> None:
        ...
```

Add a docstring on the override when the behavior refines the contract or has new side effects.

## Classes

Docstring is placed **below** the class definition. Document public attributes in an `Attributes:` section using the same formatting as `Args:`. Do not document `@property` descriptors here — put the docstring on the property itself.

```python
class SampleClass:
    """The address of a cheese shop.

    Attributes:
        likes_spam: A boolean indicating if we like SPAM.
        eggs: An integer count of eggs laid.
    """

    def __init__(self, likes_spam: bool = False) -> None:
        """Initializes the instance.

        Args:
            likes_spam: Defines if the instance exhibits this preference.
        """
        self.likes_spam = likes_spam
        self.eggs = 0

    @property
    def butter_sticks(self) -> int:
        """The number of butter sticks we have."""
        ...
```

Rules:

- Class docstring summarizes **what an instance represents**, not "class that does X". No "Class that..." / "Raised when..." — say what the exception *is* instead.
- Subclasses of `Exception` describe what the error *represents*, not the context in which it might occur.

```python
# Yes
class OutOfCheeseError(Exception):
    """No more cheese is available."""

# No
class OutOfCheeseError(Exception):
    """Raised when no more cheese is available."""
```

## Data descriptor / property

A `@property` uses the same style as an attribute or an `Args` entry:

```python
@property
def bigtable_path(self) -> str:
    """The Bigtable path."""
```

**Not** `"""Returns the Bigtable path."""`.

## Dataclasses

Document dataclass fields either in an `Attributes:` section on the class, or via `dataclasses.field(metadata={"description": "..."})`. The `Attributes:` block is preferred for human readers.

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Point:
    """A 2D coordinate.

    Attributes:
        x: The horizontal position.
        y: The vertical position.
    """
    x: float
    y: float
```

## Punctuation, spelling, grammar

- Full sentences, proper capitalization, terminating punctuation.
- Short end-of-line comments can be less formal but stay consistent.
- Prefer plain English over jargon. Cite external references with URLs when relevant.
