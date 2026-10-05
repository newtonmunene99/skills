"""Cron worker: reconciles the full catalogue every 15 minutes."""

from invsync.client import WarehouseClient
from invsync.sync import reconcile


def main() -> None:
    east = WarehouseClient("east", {"A1": 3, "B2": 7})
    west = WarehouseClient("west", {"A1": 3, "B2": 5})
    reconcile(east, west, ["A1", "B2"])


if __name__ == "__main__":
    main()
