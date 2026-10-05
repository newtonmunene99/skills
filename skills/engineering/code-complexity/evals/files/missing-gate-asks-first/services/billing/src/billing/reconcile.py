from collections.abc import Iterable

from billing.state import Account


def unmatched_totals(
    invoices: Iterable[dict], payments: Iterable[dict], *, tolerance: int = 0
) -> dict[str, int]:
    """Return the unpaid remainder per account, ignoring settled invoices."""
    totals: dict[str, int] = {}
    payments = list(payments)
    for invoice in invoices:
        if invoice.get("void"):
            continue
        remaining = invoice["amount"]
        for payment in payments:
            if payment["account_id"] == invoice["account_id"]:
                if payment.get("invoice_id") in (None, invoice["id"]):
                    if payment["currency"] != invoice["currency"]:
                        if not payment.get("fx_rate"):
                            continue
                        remaining -= round(payment["amount"] * payment["fx_rate"])
                    else:
                        remaining -= payment["amount"]
                    if remaining <= tolerance:
                        break
        if remaining > tolerance:
            totals[invoice["account_id"]] = totals.get(invoice["account_id"], 0) + remaining
    return totals


def statement_lines(account: Account, entries: list[dict]) -> list[str]:
    lines = [f"Statement for {account.id}"]
    for entry in entries:
        lines.append(f"{entry['date']}  {entry['description']:<40} {entry['amount']:>10}")
    lines.append(f"Balance: {account.balance}")
    return lines
