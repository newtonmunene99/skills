from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal


class ProrationError(ValueError):
    pass


def days_in_period(start: date, end: date) -> int:
    if end <= start:
        raise ProrationError(f"period end {end} is not after start {start}")
    return (end - start).days


def prorate(amount: Decimal, start: date, end: date, change: date) -> Decimal:
    total = days_in_period(start, end)
    if not start <= change < end:
        raise ProrationError(f"change date {change} is outside {start}..{end}")
    remaining = (end - change).days
    share = amount * Decimal(remaining) / Decimal(total)
    return share.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def credit_for_downgrade(old: Decimal, new: Decimal, start: date, end: date, change: date) -> Decimal:
    if new >= old:
        return Decimal("0.00")
    return prorate(old - new, start, end, change)
