# Logging

Use the stdlib `logging` module. It has warts, but it's ubiquitous, integrates with every framework, and supports structured output through adapters.

## The three-line setup

```python
import logging

logger = logging.getLogger(__name__)
```

- **One logger per module**, always named `__name__`. This creates a tree that matches the package hierarchy so you can tune per-package levels without touching modules.
- **Never** call `logging.info(...)` directly on the root logger — you lose the module attribution.
- **Never** configure logging inside library code. Libraries only *use* loggers; the application configures them.

## Formatting: pattern + args, never f-strings

```python
# Yes
logger.info("processed key=%s in %.2fms", key, elapsed_ms)
logger.warning("retry %d/%d after %r", attempt, max_attempts, err)

# No — always formats, even when the level is disabled; also breaks aggregation
logger.info(f"processed key={key} in {elapsed_ms:.2f}ms")
```

Reasons:

1. The formatter can skip work if the level is disabled.
2. Log aggregators (Datadog, Sentry, Loki) group messages by the pattern. F-strings produce a new unique message per call → no grouping, no useful counts.
3. The pattern is queryable ("show me all `processed key=%s` messages") — the formatted string is not.

Use `%r` for values that could be `None`, empty, or contain whitespace — it makes the log unambiguous.

## Levels

| Level      | When                                                          |
| ---------- | ------------------------------------------------------------- |
| `DEBUG`    | Detail useful only when debugging a specific problem.         |
| `INFO`     | Normal operations — request start/end, jobs succeeded.        |
| `WARNING`  | Unexpected condition, but code recovered. Ops should notice.  |
| `ERROR`    | Operation failed. Something needs attention.                  |
| `CRITICAL` | Process is about to die or is degraded across the board.      |

- Default level in production: `INFO`. Only bump to `DEBUG` when investigating.
- Never `logger.warning("succeeded")`. Match the level to actual severity.

## Exceptions

```python
# At the boundary that handles the error — log here, don't re-raise
try:
    do_thing()
except MyError:
    logger.exception("do_thing failed key=%s", key)
    return None
```

Inner layers that can't handle the error should chain instead of logging: `raise WrapperError(...) from e`. Logging *and* re-raising prints the same traceback at every level.

`logger.exception(msg, *args)` is equivalent to `logger.error(msg, *args, exc_info=True)`. It attaches the exception currently being handled, so it belongs **inside** an `except` block — called anywhere else it still logs, but appends a useless `NoneType: None`.

**Log once** — usually at the boundary where you decide the error stops propagating. See [errors.md](errors.md#where-to-catch-where-to-propagate).

## Structured / contextual logging

Two idioms.

### `logging.LoggerAdapter` for per-context fields

```python
class RequestLogger(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: dict[str, object]) -> tuple[str, dict[str, object]]:
        extra = kwargs.setdefault("extra", {})
        extra.update(self.extra)
        return msg, kwargs

def with_request(request_id: str) -> RequestLogger:
    return RequestLogger(logger, {"request_id": request_id})

log = with_request(request.id)
log.info("received payload_size=%d", len(request.body))
```

With a JSON formatter (e.g. `python-json-logger`), the `extra` fields appear as top-level JSON keys.

### `structlog` (third-party)

For pure structured logging with immutable, thread-safe contexts, `structlog` is the standard choice. Configure it once at startup; use `structlog.get_logger()` in modules.

```python
import structlog

log = structlog.get_logger()
log.info("processed", key=key, elapsed_ms=elapsed_ms)
```

Only introduce `structlog` if the whole app buys in. Mixing stdlib `logging.info(pattern, args)` and structlog key/value calls in the same codebase is worse than either alone.

## Configuration

Configure logging **once, at startup**, in the main entry point — never at import time.

### Programmatic (simple apps)

```python
import logging
import os
import sys

def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stderr,
    )
    # Tame chatty libraries
    logging.getLogger("urllib3").setLevel("WARNING")
    logging.getLogger("botocore").setLevel("WARNING")

def main() -> None:
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))
    ...
```

### `dictConfig` for anything more complex

```python
import logging.config

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "json": {
            # v3.x path; v2.x was pythonjsonlogger.jsonlogger.JsonFormatter
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stderr",
        },
    },
    "root": {"level": "INFO", "handlers": ["stderr"]},
    "loggers": {
        "urllib3": {"level": "WARNING"},
    },
}

logging.config.dictConfig(LOGGING)
```

## What to log

- **Request/task boundaries.** Start with a context id, end with duration + outcome.
- **State transitions** in long-running processes (leader election, connection reconnect, queue drained).
- **Non-obvious skips.** ("cache hit, skipping fetch") — helps future debugging.
- **Exceptions** at the point they're handled.

## What not to log

- **Secrets.** Passwords, tokens, session cookies, PII. Redact at the boundary.
- **The full request body** on every request — sample instead.
- **Loops** without sampling — one log per item can DOS your aggregator.
- **Success messages at every layer.** One "processed X in Y ms" at the outermost successful path is enough.

## Timing

For hot paths, prefer a metrics library (`prometheus_client`, `opentelemetry`) over logs. Use logs for *events*, metrics for *distributions*.

If you must log timings:

```python
import time

start = time.perf_counter()
try:
    do_work()
finally:
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("do_work elapsed_ms=%.2f", elapsed_ms)
```

## Testing loggers

Use `caplog` in pytest:

```python
def test_warns_on_retry(caplog):
    with caplog.at_level(logging.WARNING):
        do_thing_that_retries()
    assert any(r.msg == "retry %d/%d after %r" for r in caplog.records)
    assert caplog.records[0].args[0] == 1
```

Know which attribute is which:

| Attribute        | Value                                                            |
| ---------------- | ---------------------------------------------------------------- |
| `record.msg`     | The **pattern** you passed — `"retry %d/%d after %r"`            |
| `record.args`    | The **arguments** tuple — `(1, 3, err)`                          |
| `record.message` | The **formatted** result, set by `Formatter.format()`            |
| `caplog.text`    | Every record rendered through the handler's formatter            |

Assert on `record.msg` and `record.args` — that's the pair that stays stable when someone changes the formatter. `record.message` is the rendered string (it only exists at all because pytest's capture handler formats each record), so asserting on it couples the test to formatting.
