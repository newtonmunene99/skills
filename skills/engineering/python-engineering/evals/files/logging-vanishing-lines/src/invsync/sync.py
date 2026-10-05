"""Reconcile inventory counts between two warehouses."""

import logging

from invsync.client import WarehouseClient

log = logging.getLogger(__name__)


def reconcile(a: WarehouseClient, b: WarehouseClient, skus: list[str]) -> list[str]:
    mismatched = []
    for sku in skus:
        try:
            left, right = a.get_count(sku), b.get_count(sku)
        except Exception as e:
            log.error(f"failed to fetch {sku}: {e}")
            continue
        if left != right:
            log.warning("sku %s: %s=%d %s=%d", sku, a.name, left, b.name, right)
            mismatched.append(sku)
    log.info("reconciled %d skus, %d mismatched", len(skus), len(mismatched))
    return mismatched
