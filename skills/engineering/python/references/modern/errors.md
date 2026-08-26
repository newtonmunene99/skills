# Errors and Exceptions

Modern Python exception design (3.11+). Extends the [language rules on exceptions](../pyguide/language-rules.md#exceptions).

## Contents

- [Choose the right exception](#choose-the-right-exception)
- [Custom exception design](#custom-exception-design)
- [Chaining and preservation](#chaining-and-preservation)
- [`try` / `except` / `else` / `finally`](#try--except--else--finally)
- [`ExceptionGroup` and `except*`](#exceptiongroup-and-except)
- [Where to catch, where to propagate](#where-to-catch-where-to-propagate)
- [Logging exceptions](#logging-exceptions)
- [`contextlib.suppress`](#contextlibsuppress)
- [`assert` is not error handling](#assert-is-not-error-handling)

## Choose the right exception

Use a built-in when it fits:

| Situation                              | Exception              |
| -------------------------------------- | ---------------------- |
| Wrong argument type                    | `TypeError`            |
| Right type, invalid value              | `ValueError`           |
| Missing dict/JSON key                  | `KeyError`             |
| Missing attribute                      | `AttributeError`       |
| Index out of range                     | `IndexError`           |
| Not implemented / abstract method      | `NotImplementedError`  |
| File missing                           | `FileNotFoundError`    |
| I/O failure                            | `OSError` (or subclass)|
| Bug that shouldn't happen              | `AssertionError` (in tests) / `RuntimeError` |
| Timed out                              | `TimeoutError`         |
| User cancelled                         | `KeyboardInterrupt`    |

Domain-specific errors get a custom class.

## Custom exception design

Every custom exception:

1. Ends in `Error` (`ConfigError`, not `ConfigException`).
2. Inherits from a stdlib base **or** from your package's own base exception.
3. Has a docstring saying what the exception *represents* (not "raised when...").
4. Provides useful attributes for programmatic recovery — don't cram everything into the message.

```python
class ConfigError(Exception):
    """A configuration value is invalid or missing."""


class MissingKeyError(ConfigError):
    """A required configuration key is missing."""

    def __init__(self, key: str) -> None:
        super().__init__(f"Missing required config key: {key!r}")
        self.key = key
```

**Package-wide base:**

```python
class MyLibError(Exception):
    """Base class for all errors raised by mylib."""


class TransportError(MyLibError): ...
class AuthError(MyLibError): ...
class RateLimitError(MyLibError):
    def __init__(self, retry_after: float) -> None:
        super().__init__(f"Rate limited; retry after {retry_after}s")
        self.retry_after = retry_after
```

Callers can `except MyLibError` to catch anything from your library, or narrow.

**Don't shadow a builtin exception name.** `ConnectionError`, `TimeoutError`, `PermissionError`, and `FileNotFoundError` are all builtins (subclasses of `OSError`). Defining your own `class ConnectionError(MyLibError)` means every later `except ConnectionError:` in that module silently stops catching the socket errors the reader expects. Pick `TransportError`, `MyLibTimeout`, and so on.

## Chaining and preservation

Always chain when translating an exception to a higher-level one:

```python
try:
    parsed = json.loads(raw)
except json.JSONDecodeError as e:
    raise ConfigError(f"Invalid JSON in config file: {path}") from e
```

- `raise X from e` — explicit cause. Traceback shows both.
- `raise X` inside an `except` — implicit context. Traceback shows both, prefixed "During handling of the above exception, another exception occurred".
- `raise X from None` — suppresses the context. Use when the original exception adds no value for the caller.

Never do `raise ConfigError(str(e))` — you lose the traceback.

## `try` / `except` / `else` / `finally`

Full form:

```python
conn = None                       # bind before the try, or finally raises
try:
    conn = open_connection(url)
except OSError as e:
    raise ServiceUnavailable(url) from e
else:
    handle(conn)
finally:
    if conn is not None:
        conn.close()
```

**Bind every name the `finally` touches *before* the `try`.** Without the first line, a failure in `open_connection` leaves `conn` unbound, so `finally` raises `UnboundLocalError` (`NameError` at module scope) — which replaces the `ServiceUnavailable` you were trying to raise. In real code, prefer `with` and skip the whole problem:

```python
with closing_connection(url) as conn:
    handle(conn)
```

Rules:

- Keep the `try` body as small as possible — only the line(s) that can raise the exception you're handling.
- `else` runs only if no exception was raised. Put the "success" path here so `except` handles only what the `try` body raises.
- `finally` always runs. Use it for cleanup that must happen even on cancellation.
- Prefer `with` for resources — you rarely need explicit `finally` for close-like behavior.

**Never catch what you can't act on:**

```python
# No — swallows programming errors
try:
    result = do_thing()
except Exception:
    return None

# Yes — narrow
try:
    result = do_thing()
except ExternalServiceError as e:
    logger.warning("do_thing failed: %r", e)
    return None
```

**Never bare `except:`.** It catches the `BaseException`s you must not swallow — `KeyboardInterrupt`, `SystemExit`, and `asyncio.CancelledError`. (`MemoryError` is an ordinary `Exception`, so `except Exception:` catches that one too.) The single legitimate use of the widest catch is cleanup that immediately re-raises: `except BaseException: rollback(); raise`.

## `ExceptionGroup` and `except*`

Introduced by PEP 654 (3.11+). Used by `TaskGroup` to surface multiple concurrent failures.

```python
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(fetch("a"))
        tg.create_task(fetch("b"))
        tg.create_task(fetch("c"))
except* HTTPError as eg:
    for err in eg.exceptions:
        logger.warning("HTTP error: %r", err)
except* TimeoutError as eg:
    logger.error("Timeouts: %d", len(eg.exceptions))
```

`except*` splits the group by type; unmatched exceptions re-raise as a smaller group.

Wrap-your-own:

```python
raise ExceptionGroup(
    "validation failed",
    [
        ValueError("missing name"),
        ValueError("bad email"),
    ],
)
```

## Where to catch, where to propagate

- **Library code:** raise. Let the caller decide policy. Never `logger.exception(...)` and swallow.
- **Application boundary** (HTTP handler, CLI entry, worker task): catch, log, translate to a user-visible response or exit code.
- **Retryable path:** catch specific transient errors; retry with backoff; convert to a domain error after N attempts.

```python
async def handle(request: Request) -> Response:
    try:
        result = await service.do(request.payload)
    except ValidationError as e:
        return Response(status=400, body={"errors": e.errors})
    except NotFoundError as e:
        return Response(status=404, body={"error": str(e)})
    except Exception:                    # deliberate: this is the last frame
        logger.exception("unhandled error in handle")
        return Response(status=500, body={"error": "internal"})
    return Response(status=200, body=result.to_dict())
```

The broad `except Exception:` is correct *here* and nowhere above it — a request handler is the last frame that can turn a crash into a response. It does not catch `asyncio.CancelledError` (a `BaseException`), so a cancelled request still unwinds normally.

At the top of each thread or task, install the same catch-all + `logger.exception()` — otherwise the exception dies silently.

## Logging exceptions

Inside an `except`, prefer `logger.exception(...)` (auto-attaches the traceback):

```python
def run_worker(queue: Queue[Job]) -> None:
    while (job := queue.get()) is not None:
        try:
            process(job)
        except Exception:
            # Task boundary: nothing above this frame will ever see it.
            logger.exception("job failed id=%s", job.id)
```

Use `logger.error(..., exc_info=True)` if you need to control the log level.

**Log once, and don't log-and-re-raise.** The traceback already carries every frame, so a `logger.exception(...)` followed by `raise` in an inner layer just prints the same failure twice with less context than the outer log will have. Log at the layer that decides the error stops propagating; everywhere below it, either chain (`raise MyError(...) from e`) or let it fly.

The one exception is a thread or task boundary, where nothing above you will ever see the exception — there, log *and* re-raise (or fail the process).

## `contextlib.suppress`

For "I don't care if this fails" cleanup:

```python
from contextlib import suppress

with suppress(FileNotFoundError):
    shutil.rmtree(workdir)
```

Equivalent to a `try` / `except FileNotFoundError: pass` pair, but compact enough to read as intent rather than as swallowed error. Only for genuinely benign cases — never as a way to silence bugs.

Check for a purpose-built flag first: `path.unlink(missing_ok=True)` and `shutil.rmtree(d, ignore_errors=True)` say the same thing more precisely than wrapping them in `suppress`.

## `assert` is not error handling

- `python -O` **strips `assert` statements**. They must not be load-bearing.
- Use them for invariants that indicate a bug, and only where losing them at `-O` is acceptable (typically none, in production paths).
- **Fine in tests** — pytest uses `assert` extensively and rewrites it for good failure messages.

```python
# No — production validation must not use assert
def get(user_id: str) -> User:
    assert user_id, "user_id required"

# Yes
def get(user_id: str) -> User:
    if not user_id:
        raise ValueError("user_id required")
```

## Error message hygiene

Repeat the pyguide's error message rules ([style-rules.md](../pyguide/style-rules.md#error-messages)):

- Precisely describe the actual condition.
- Interpolate with `{p=}` or `{p!r}` so values are clearly delimited.
- Greppable, stable phrasing — avoid embedding user input in the middle.

```python
raise ValueError(f"Not a probability: {p=}")
raise KeyError(f"Unknown role: {role!r} (expected one of {sorted(ALLOWED)})")
```
