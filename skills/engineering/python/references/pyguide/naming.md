# Naming (pyguide §3.16)

Distilled from [Google Python Style Guide §3.16](https://google.github.io/styleguide/pyguide.html#316-naming).

## The one-line cheat sheet

`module_name`, `package_name`, `ClassName`, `method_name`, `ExceptionName`, `function_name`, `GLOBAL_CONSTANT_NAME`, `global_var_name`, `instance_var_name`, `function_parameter_name`, `local_var_name`, `query_proper_noun_for_thing`, `send_acronym_via_https`.

## Guidelines derived from Guido's recommendations

| Type                         | Public               | Internal                          |
| ---------------------------- | -------------------- | --------------------------------- |
| Packages                     | `lower_with_under`   |                                   |
| Modules                      | `lower_with_under`   | `_lower_with_under`               |
| Classes                      | `CapWords`           | `_CapWords`                       |
| Exceptions                   | `CapWords` + `Error` |                                   |
| Functions                    | `lower_with_under()` | `_lower_with_under()`             |
| Global / Class constants     | `CAPS_WITH_UNDER`    | `_CAPS_WITH_UNDER`                |
| Global / Class variables     | `lower_with_under`   | `_lower_with_under`               |
| Instance variables           | `lower_with_under`   | `_lower_with_under` (protected)   |
| Method names                 | `lower_with_under()` | `_lower_with_under()` (protected) |
| Function / method parameters | `lower_with_under`   |                                   |
| Local variables              | `lower_with_under`   |                                   |

## Principles

- **Descriptive**, not clever. Scope of visibility governs length: a 5-line loop can use `i`; a class attribute cannot.
- **No abbreviation** by deleting letters within a word. `usr` → `user`. `resp` is OK because it's a widely accepted contraction of `response`.
- **Acronyms: pick one convention per project and hold it.** Both are defensible and the pyguide's cheat sheet (`send_acronym_via_https`, `SendAcronymViaHttps`) does not forbid either:
  - *Capitalize the whole acronym* — `HTTPClient`, `XMLParser`. This is what [PEP 8](https://peps.python.org/pep-0008/#descriptive-naming-styles) recommends ("HTTPServerError is better than HttpServerError") and what the stdlib does (`HTTPServer`, `XMLParser`).
  - *Treat it as one word* — `HttpClient`, `XmlParser`. Reads better when two acronyms collide (`HTTPSXMLClient` vs `HttpsXmlClient`).
  In **function and variable** names acronyms are always lowercase either way: `parse_xml`, `send_via_https`.
- **Files use `.py` and never dashes.** Dashes make imports impossible.

## Names to avoid

- Single-character names, **except**:
  - counters/iterators: `i`, `j`, `k`, `n`, `v` in a small scope.
  - exception in `try`/`except`: `e`.
  - file handle in `with`: `f`.
  - private type variables: `_T = TypeVar("_T")`, `_P = ParamSpec("_P")`.
  - names matching an academic paper's notation (see [mathematical notation](#mathematical-notation)).
- Dashes in package/module names.
- `__double_leading_and_trailing_underscore__` — reserved by the language.
- Names that encode the type: `id_to_name_dict` → `names_by_id`.
- Offensive terms.

## Internal / protected / private

- **Single leading underscore** (`_foo`) means "protected" — linters and IDEs will flag external access, but tests may still reach it. This is the standard way to signal "not part of the public API".
- **Double leading underscore** (`__foo`) triggers name mangling. **Avoid it** — it hurts readability and testability without giving true privacy. Prefer `_foo`.
- Modules can control what `from module import *` exports with `__all__`. Do not rely on this for encapsulation; it's for import hygiene.

## Constants

- Module-level constants: `UPPER_SNAKE_CASE`.
- Class-level constants (rare — usually put on the module): `UPPER_SNAKE_CASE`.
- **Immutable value objects** aren't constants unless they're module-level; `_DEFAULT_TIMEOUT = 30` yes, `default_config = load_config()` no.
- Use `typing.Final` when static analysis needs the guarantee:

```python
from typing import Final

MAX_RETRIES: Final = 3
```

## Enums

Members use `UPPER_SNAKE`:

```python
from enum import Enum, StrEnum

class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
```

Prefer `StrEnum` (3.11+) / `IntEnum` when serialization is involved. On 3.10, use `class Role(str, Enum):` as the `StrEnum` equivalent.

## Type variables

Type variables have specific naming conventions:

- **Descriptive when public/exported** (used across modules or in a public API): `AddableType`, `AnyFunction`.
- **Short private form OK** for locally-scoped, unconstrained `TypeVar` / `ParamSpec`: `_T`, `_U`, `_P`, `_R`.
- **Not** `T = TypeVar("T")` at module scope (missing leading `_`) unless it's part of the public API.

```python
# Yes
_T = TypeVar("_T")
_P = ParamSpec("_P")
AddableType = TypeVar("AddableType", int, float, str)
AnyFunction = TypeVar("AnyFunction", bound=Callable[..., Any])

# No
T = TypeVar("T")
_T = TypeVar("_T", int, float, str)   # constrained -> deserves a real name
_F = TypeVar("_F", bound=Callable)     # bound -> deserves a real name
```

PEP 695 (3.12+) offers an even lighter syntax:

```python
def first[T](items: Sequence[T]) -> T:
    return items[0]
```

## Test naming

`test_<method_under_test>_<state>` for new code. Underscores may appear inside the "state" portion:

```python
def test_parse_returns_none_when_input_empty():
    ...

def test_parse_raises_when_invalid_json():
    ...
```

Legacy CapWords test names (`testDoesThing`) are grandfathered; new tests use snake_case.

## File naming

- Must have `.py` extension.
- Never dashes.
- Lowercase with underscores. Old `CapWords.py` modules are discouraged — they collide visually with class names when imported.

## Mathematical notation

For math-heavy code, short variable names that match a paper's notation are preferred. When doing so:

1. Cite the source (paper URL) in the docstring or a comment.
2. Prefer PEP 8 names for the public API.
3. Silence the linter locally: `# noqa: N803, N806` on each affected line. Ruff has **no block-level suppression** — `# ruff: noqa: N806` is file-wide wherever you put it, so reserve it for a module that is entirely math (e.g. a dedicated `_kalman.py`) rather than sprinkling it mid-file.

```python
def kalman_update(x, P, z, H, R):  # noqa: N803, N806
    """Kalman filter measurement update.

    Follows notation from Bar-Shalom, "Estimation with Applications to
    Tracking and Navigation" (2001).
    """
    ...
```
