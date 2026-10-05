"""Thin client for the warehouse inventory APIs."""

import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


class WarehouseClient:
    def __init__(self, name: str, counts: dict[str, int]) -> None:
        self.name = name
        self._counts = counts  # stand-in for the HTTP API in this sketch

    def get_count(self, sku: str) -> int:
        logger.info(f"{self.name}: GET /counts/{sku}")
        return self._counts[sku]
