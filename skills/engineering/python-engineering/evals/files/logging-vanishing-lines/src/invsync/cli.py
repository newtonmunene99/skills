"""Command-line entry point: one reconciliation run."""

import argparse
import logging.config

from invsync.client import WarehouseClient
from invsync.sync import reconcile

LOGGING = {
    "version": 1,
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "stderr": {"class": "logging.StreamHandler", "formatter": "plain"},
    },
    "root": {"level": "INFO", "handlers": ["stderr"]},
}


def main() -> None:
    parser = argparse.ArgumentParser(prog="invsync")
    parser.add_argument("skus", nargs="+")
    args = parser.parse_args()

    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(__name__)

    east = WarehouseClient("east", {"A1": 3, "B2": 7, "C3": 0})
    west = WarehouseClient("west", {"A1": 3, "B2": 5, "C3": 0})
    logger.info("starting run for %d skus", len(args.skus))
    mismatched = reconcile(east, west, args.skus)
    logger.info("done, %d mismatched", len(mismatched))


if __name__ == "__main__":
    main()
