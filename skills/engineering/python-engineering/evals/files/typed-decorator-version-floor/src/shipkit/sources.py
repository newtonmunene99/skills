"""Sources that shipment documents can be loaded from."""

from pathlib import Path

import httpx


class Source:
    """Base class for anything that can return a shipment document by ref."""

    def fetch(self, ref: str) -> bytes:
        raise NotImplementedError

    def close(self) -> None:
        """Release any held resources. No-op by default."""


class FileSource(Source):
    def __init__(self, root: Path) -> None:
        self._root = root

    def fetch(self, ref: str) -> bytes:
        return (self._root / ref).read_bytes()


class HttpSource(Source):
    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=10.0)

    def fetch(self, ref: str) -> bytes:
        resp = self._client.get(f"{self._base_url}/documents/{ref}")
        resp.raise_for_status()
        return resp.content

    def close(self) -> None:
        self._client.close()
