# Async (Python 3.11+)

Patterns for `asyncio` — targeting 3.11+ where `TaskGroup`, `asyncio.timeout`, and `ExceptionGroup` are available.

## Contents

- [Baseline](#baseline)
- [Structured concurrency with TaskGroup](#structured-concurrency-with-taskgroup)
- [Timeouts](#timeouts)
- [Cancellation](#cancellation)
- [Bridging sync and async](#bridging-sync-and-async)
- [Producer/consumer with queues](#producerconsumer-with-queues)
- [Common pitfalls](#common-pitfalls)

## Baseline

- **One event loop per thread.** Start with `asyncio.run(main())`. Don't create loops manually unless writing a framework.
- **Never `time.sleep()` in async code** — it blocks the loop. Use `asyncio.sleep()`.
- **`asyncio` is for IO waits, not CPU work.** A loop full of CPU-bound coroutines runs on one thread. For parsing/compression/math, use a process pool — see [../pyguide/language-rules.md](../pyguide/language-rules.md#threads-vs-processes-vs-asyncio).
- **Never call a blocking function directly on the loop** (`requests.get`, `open` on large files, DB drivers without async support). Use an async equivalent (`httpx.AsyncClient`, `aiofiles`, async DB driver) or `asyncio.to_thread()`.
- **Every coroutine must be awaited or scheduled.** A bare `foo()` on a `async def foo` returns a coroutine object; the type checker will warn.

## Structured concurrency with TaskGroup

`asyncio.TaskGroup` (3.11+) is the default way to run concurrent tasks. It:

- Waits for all tasks to finish before exiting the `async with` block.
- Cancels sibling tasks if one raises.
- Aggregates errors into an `ExceptionGroup`.

```python
import asyncio
from collections.abc import Sequence

async def fetch(url: str) -> bytes:
    ...

async def fetch_all(urls: Sequence[str]) -> list[bytes]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(u)) for u in urls]
    return [t.result() for t in tasks]
```

**A `TaskGroup` raises `ExceptionGroup`, not the original exception.** `except ValueError:` around the `async with` will not match. Use `except*` (see [errors.md](errors.md#exceptiongroup-and-except)):

```python
try:
    async with asyncio.TaskGroup() as tg:
        ...
except* ValueError as eg:
    ...
```

Prefer `TaskGroup` over `asyncio.gather` in new code. Reasons:

- `gather` returns partial results only when `return_exceptions=True`; otherwise a failure leaves siblings running until they eventually raise or complete.
- `gather` doesn't cancel siblings on the first failure by default.
- `TaskGroup` gives you `ExceptionGroup` — you can handle multiple failures at once.

`gather` still makes sense when you truly want every task to complete regardless of failures (`return_exceptions=True`):

```python
results = await asyncio.gather(*coros, return_exceptions=True)
for r in results:
    if isinstance(r, Exception):
        logger.warning("Task failed: %r", r)
```

## Timeouts

Use `asyncio.timeout()` (3.11+) — it's a context manager, composes cleanly with `TaskGroup`, and cancels the block on expiry.

```python
async def fetch_with_deadline(url: str) -> bytes:
    async with asyncio.timeout(5.0):
        return await fetch(url)
```

`asyncio.wait_for(coro, timeout)` still works and is fine for single-coroutine cases, but `asyncio.timeout()` is more flexible.

**Rule:** every `await` that talks to the outside world (HTTP, DB, filesystem, subprocess) is wrapped in a timeout — either the client's own timeout or `asyncio.timeout()`. No unbounded waits in production code.

## Cancellation

Cancellation is delivered as `asyncio.CancelledError` at the next `await` point. Rules:

- **`except Exception:` does *not* catch `CancelledError`.** Since 3.8 `asyncio.CancelledError` inherits from `BaseException`, precisely so broad handlers can't eat cancellation. What *does* swallow it: bare `except:` and `except BaseException:`. Avoid `except Exception:` in async code anyway — it hides every programming error — but don't rely on it as a cancellation hazard.
- **Catch `CancelledError` only to clean up, then re-raise.** Returning normally from a cancelled task tells the caller the work completed.
- **Cleanup with `try`/`finally` or `async with`.** The `finally` block runs on cancellation.
- **`asyncio.shield(coro)`** protects a coroutine from cancellation — use rarely, only when a partial commit is worse than blocking.

```python
async def do_work() -> None:
    try:
        await step_one()
        await step_two()
    except asyncio.CancelledError:
        logger.info("do_work cancelled, cleaning up")
        await cleanup()
        raise
```

Never write `except asyncio.CancelledError: pass` — that silently deadlocks the caller waiting on the task.

## Bridging sync and async

**Sync code called from async: use `asyncio.to_thread`.** It runs the callable in the default executor without blocking the loop.

```python
async def parse_large_file(path: Path) -> Parsed:
    raw = await asyncio.to_thread(path.read_bytes)
    return parse(raw)
```

**Async code called from sync:** use `asyncio.run()` at the top level, or `anyio.from_thread.run()` from a worker thread. Do not create nested event loops with `asyncio.new_event_loop()` — that's a footgun.

**Never mix sync and async I/O in a request handler:** either the whole path is async or it isn't. Half-async is the worst of both worlds.

## Producer/consumer with queues

`asyncio.Queue` is the standard channel:

```python
_CONSUMERS = 4

async def producer(q: asyncio.Queue[Item | None], consumers: int) -> None:
    async for item in source():
        await q.put(item)
    for _ in range(consumers):
        await q.put(None)  # one sentinel per consumer

async def consumer(q: asyncio.Queue[Item | None]) -> None:
    while True:
        item = await q.get()
        try:
            if item is None:
                return
            await handle(item)
        finally:
            q.task_done()

async def main() -> None:
    q: asyncio.Queue[Item | None] = asyncio.Queue(maxsize=100)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q, _CONSUMERS))
        for _ in range(_CONSUMERS):
            tg.create_task(consumer(q))
```

**One sentinel per consumer, or the group hangs.** A single `None` wakes exactly one consumer; the rest block on `q.get()` forever and `TaskGroup` waits for all of them. This is the most common asyncio deadlock.

The alternative is `q.join()` and no sentinels at all — the producer awaits drain, then the consumers are cancelled:

```python
async def main() -> None:
    q: asyncio.Queue[Item] = asyncio.Queue(maxsize=100)
    consumers = [asyncio.create_task(consumer(q)) for _ in range(_CONSUMERS)]
    try:
        async for item in source():
            await q.put(item)
        await q.join()          # every put has a matching task_done
    finally:
        for c in consumers:
            c.cancel()
        await asyncio.gather(*consumers, return_exceptions=True)
```

`maxsize` gives you backpressure in both shapes.

## Fire-and-forget

Never write `asyncio.create_task(coro())` and drop the reference — the task can be GC'd before it runs, and exceptions vanish into `_log_traceback`.

- In a `TaskGroup`: `tg.create_task(coro())` — the group holds the reference.
- Outside a group: store the task in a set and add a `done_callback` to remove it.

```python
_background: set[asyncio.Task[Any]] = set()

def spawn(coro: Coroutine[Any, Any, Any]) -> None:
    task = asyncio.create_task(coro)
    _background.add(task)
    task.add_done_callback(_background.discard)
```

## `async for` and `async with`

- Async iteration protocol: implement `__aiter__` and `__anext__`.
- Async context managers: implement `__aenter__` and `__aexit__`, or use `contextlib.asynccontextmanager`.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def transaction(db: Database) -> AsyncIterator[Transaction]:
    tx = await db.begin()
    try:
        yield tx
    except BaseException:
        await tx.rollback()
        raise
    else:
        await tx.commit()
```

`except BaseException:` — not bare `except:` (which [errors.md](errors.md) forbids) and not `except Exception:`. A rollback must also run when the task is cancelled or the process is interrupted, and `CancelledError`/`KeyboardInterrupt` are `BaseException`s. This is one of the few places the widest catch is correct, and it re-raises immediately.

## Common pitfalls

- **Calling `asyncio.run()` inside a coroutine.** It creates a nested loop and crashes.
- **Blocking the loop with sync I/O.** Turn on debug mode — `asyncio.run(main(), debug=True)` or `PYTHONASYNCIODEBUG=1` — and the loop logs any callback that runs longer than `slow_callback_duration` (0.1s default). To tighten it, reach for the loop from *inside* a coroutine: `asyncio.get_running_loop().slow_callback_duration = 0.05`. Don't use `asyncio.get_event_loop()` — it's deprecated outside a running loop and raises in 3.14+.
- **`asyncio.sleep(0)` misuse.** It's a yield to the loop, not a real sleep. Fine for cooperative scheduling; useless as a delay.
- **Sharing a session/client across the loop but never closing it.** Use `async with client:` or explicit `await client.aclose()` on shutdown.
- **Signal handling in the wrong place.** Use `loop.add_signal_handler` inside `main()`, not at module scope.

## Alternative: `anyio`

`anyio` gives structured-concurrency primitives that work on both `asyncio` and `trio`. Consider it if your library needs to support both, or if you want cancellation semantics closer to trio's (task groups block until every child truly exits). For app code targeting `asyncio` only, stdlib primitives are usually enough.
