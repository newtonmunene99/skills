# Testing with pytest

pytest is the standard. `unittest` is stdlib but the ergonomics are worse in every dimension.

## Contents

- [Layout](#layout)
- [Naming](#naming)
- [Assertions](#assertions)
- [Fixtures](#fixtures)
- [Parametrize](#parametrize)
- [Mocking](#mocking)
- [Async tests](#async-tests)
- [Temporary files, HTTP, databases](#temporary-files-http-databases)
- [Coverage](#coverage)
- [Test doubles that stay real](#test-doubles-that-stay-real)
- [Anti-patterns](#anti-patterns)

## Layout

Prefer **src layout** and a sibling `tests/` directory:

```
myproj/
├── pyproject.toml
├── src/
│   └── myproj/
│       ├── __init__.py
│       └── ...
└── tests/
    ├── conftest.py
    ├── test_foo.py
    └── integration/
        └── test_end_to_end.py
```

- Tests import from the installed package (`from myproj import ...`), never with relative paths from the source tree.
- `conftest.py` in `tests/` holds shared fixtures; nest more `conftest.py`s under subdirectories for scope-limited fixtures.

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
xfail_strict = true
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:third_party_lib.*",
]
```

## Naming

- Test files: `test_<subject>.py`.
- Test functions: `test_<behavior>_<condition>` — describes what and when, not how.

```python
def test_parse_returns_none_when_input_empty(): ...
def test_parse_raises_when_json_invalid(): ...
def test_charge_uses_default_currency_when_not_provided(): ...
```

Group related tests in a class named `Test<Subject>` if fixtures/state are shared. Otherwise keep them flat.

## Assertions

`assert` is fine here — pytest rewrites it for good failure messages. Prefer plain assertions over helper methods:

```python
def test_charge_calculates_total():
    total = charge(100, tax_rate=0.1)
    assert total == 110

def test_parse_extracts_fields():
    parsed = parse('{"a": 1, "b": 2}')
    assert parsed == {"a": 1, "b": 2}
```

For "raises" checks:

```python
import pytest

def test_charge_rejects_negative():
    with pytest.raises(ValueError, match=r"amount must be >= 0"):
        charge(-1)
```

Use `match=` (regex) to assert on the message — it catches copy-paste bugs.

For approximate float equality:

```python
assert compute() == pytest.approx(0.1 + 0.2)
```

## Fixtures

Fixtures replace setUp/tearDown. They're **lazy**, **composable**, and **scoped**.

```python
import sqlite3

import pytest

@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE users (id TEXT, name TEXT)")
    yield conn
    conn.close()

def test_insert_user(db):
    db.execute("INSERT INTO users VALUES (?, ?)", ("u1", "Alice"))
    row = db.execute("SELECT name FROM users WHERE id = ?", ("u1",)).fetchone()
    assert row == ("Alice",)
```

**Scopes:** `function` (default), `class`, `module`, `package`, `session`. Widen only when setup is expensive and shared safely across tests.

```python
@pytest.fixture(scope="session")
def app_config() -> Config:
    return Config.from_env()
```

**Type your fixtures.** The return type helps callers.

```python
from collections.abc import Iterator

@pytest.fixture
def user() -> Iterator[User]:
    u = User(...)
    yield u
    u.delete()
```

## Parametrize

Use `@pytest.mark.parametrize` for table-driven tests. Give each case a meaningful id:

```python
@pytest.mark.parametrize(
    ("input_", "expected"),
    [
        pytest.param("",      None,      id="empty"),
        pytest.param("42",    42,        id="int"),
        pytest.param("42.5",  42.5,      id="float"),
        pytest.param("nope",  None,      id="unparseable"),
    ],
)
def test_parse_number(input_, expected):
    assert parse_number(input_) == expected
```

Stack `parametrize` decorators for cartesian products.

## Mocking

Prefer **fakes** and **passing collaborators as dependencies** over `unittest.mock`. Mocks are OK for hard boundaries (network, filesystem, time), but they erode confidence — the mock can drift from the real API silently.

### `monkeypatch` for env, attributes, cwd

```python
def test_uses_env_config(monkeypatch):
    monkeypatch.setenv("APP_MODE", "debug")
    assert load_mode() == "debug"

def test_time_frozen(monkeypatch):
    frozen = datetime(2026, 1, 1, tzinfo=UTC)   # aware, never naive
    monkeypatch.setattr("myproj.clock.now", lambda: frozen)
    ...
```

### `unittest.mock` for narrow boundary mocks

```python
from unittest.mock import Mock

def test_charges_gateway_once():
    gateway = Mock(spec=PaymentGateway)
    service = ChargeService(gateway=gateway)
    service.charge(order_id="o1", amount=100)
    gateway.charge.assert_called_once_with(order_id="o1", amount=100)
```

Always pass `spec=` so the mock rejects methods that don't exist on the real class.

### Prefer real seams

Design so tests can pass a plain fake — usually a small class or a dict satisfying a `Protocol`:

```python
class InMemoryUsers:
    def __init__(self) -> None:
        self._data: dict[str, User] = {}
    def get(self, user_id: str) -> User | None:
        return self._data.get(user_id)
    def save(self, user: User) -> None:
        self._data[user.id] = user

def test_creates_user_when_missing():
    repo: UserRepository = InMemoryUsers()
    service = UserService(repo=repo)
    service.ensure("u1", "Alice")
    assert repo.get("u1") == User("u1", "Alice")
```

## Async tests

Install `pytest-asyncio`, configure once:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Set `asyncio_default_fixture_loop_scope` explicitly.** pytest-asyncio 0.24+ raises a `PytestDeprecationWarning` from `pytest_configure` when it's unset. That runs before `filterwarnings` (or `pytest -W`) applies, so locally the warning is easy to miss — but a CI job that runs `python -W error -m pytest` or sets `PYTHONWARNINGS=error` turns it into an `INTERNALERROR` that exits before a single test runs. Setting it also pins which event loop async fixtures share, instead of leaving it to a default the plugin has said will change.

Then any `async def test_...` is picked up automatically:

```python
async def test_fetch_returns_body(httpx_mock):
    httpx_mock.add_response(url="https://example.com/", text="hi")
    result = await fetch("https://example.com/")
    assert result == "hi"
```

Async fixtures work the same way:

```python
@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient() as c:
        yield c
```

`anyio` users: AnyIO ships its own plugin (`anyio.pytest_plugin`) with the `anyio` package — there is no separate `pytest-anyio` distribution. Mark tests with `@pytest.mark.anyio` and declare the backend once:

```python
# conftest.py
@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
```

## Temporary files, HTTP, databases

- **Files:** `tmp_path` (Path) — auto-cleaned. Prefer over `tempfile.TemporaryDirectory`.
- **HTTP:** `respx` (for `httpx`) or `pytest-httpx`; `responses` (for `requests`). Never make real HTTP calls in unit tests.
- **DB:** use an in-memory SQLite for logic tests; a real DB (in Docker) for integration tests.
- **Time:** `freezegun` or `time-machine` if you need to freeze `datetime.now`. Prefer injecting a `clock` callable into your code.

## Coverage

```toml
[tool.coverage.run]
source = ["src/myproj"]
branch = true

[tool.coverage.report]
show_missing = true
skip_covered = true
fail_under = 85
exclude_also = [
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "pragma: no cover",
    "\\.\\.\\.$",
]
```

Coverage is a floor, not a goal. Uncovered lines are a signal to look at; 100% coverage on trivial code is not a substitute for good tests.

## Test doubles that stay real

Prefer this test pyramid:

1. **Unit tests** — pure logic, no I/O. Fast. Most of the suite.
2. **Boundary tests** — one collaborator faked via `Protocol`, everything else real.
3. **Integration tests** — real DB, real HTTP, run in CI.
4. **End-to-end tests** — smoke coverage. Slow. Small in number.

## Anti-patterns

- **Sleeping in tests** to "wait for" async work. Use `TaskGroup` / `await`.
- **Tests that depend on ordering.** Each test should pass in isolation. Add the `pytest-random-order` plugin and run `pytest --random-order` in CI to catch this.
- **Overuse of `MagicMock`** without `spec`. Mocks silently return more `MagicMock`s and hide bugs.
- **Sharing state between tests** via module-level variables or singletons. Reset in a fixture with `yield` + cleanup, or refactor the code.
- **Skipping tests as documentation.** Delete the test or fix it. `@pytest.mark.skip("broken")` rots.
- **Testing private methods directly.** Test through the public API. If a private method is hard enough to test to warrant its own tests, it should be a public function in a helper module.
