"""Fetch spot prices from the upstream pricing API."""

import asyncio
from decimal import Decimal

import httpx

BASE_URL = "https://prices.internal.example/v1"
SUPPORTED_CURRENCIES = frozenset({"USD", "EUR", "GBP", "KES"})


class PriceNotFoundError(LookupError):
    """Raised when the upstream API has no price for a symbol."""


async def fetch_price(
    client: httpx.AsyncClient,
    symbol: str,
    currency: str = "USD",
    *,
    timeout_s: float = 5.0,
) -> Decimal:
    """Return the current spot price of `symbol` in `currency`.

    Args:
        client: Shared HTTP client.
        symbol: Ticker, e.g. "XAU".
        currency: ISO 4217 code; must be one of SUPPORTED_CURRENCIES.
        timeout_s: Upper bound on the whole request.

    Returns:
        The price as a Decimal.

    Raises:
        ValueError: If `currency` is not supported.
        PriceNotFoundError: If upstream returns 404 for the symbol.
        TimeoutError: If upstream does not answer within `timeout_s`.
        httpx.HTTPStatusError: For any other non-2xx response.
    """
    currency = currency.upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"unsupported currency: {currency}")
    async with asyncio.timeout(timeout_s):
        resp = await client.get(f"{BASE_URL}/spot/{symbol}", params={"currency": currency})
    if resp.status_code == 404:
        raise PriceNotFoundError(symbol)
    resp.raise_for_status()
    return Decimal(resp.json()["price"])
