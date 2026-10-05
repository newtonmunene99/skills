from dataclasses import dataclass

from billing.state import Account


@dataclass(frozen=True)
class Event:
    kind: str
    account_id: str
    amount: int = 0
    reason: str = ""


def apply_event(account: Account, event: Event) -> Account:
    match event.kind:
        case "opened":
            return account.open()
        case "closed":
            return account.close()
        case "charged":
            return account.charge(event.amount)
        case "refunded":
            return account.refund(event.amount)
        case "credited":
            return account.credit(event.amount)
        case "debited":
            return account.debit(event.amount)
        case "suspended":
            return account.suspend(event.reason)
        case "reinstated":
            return account.reinstate()
        case "disputed":
            return account.dispute(event.amount, event.reason)
        case "dispute_won":
            return account.resolve_dispute(won=True)
        case "dispute_lost":
            return account.resolve_dispute(won=False)
        case "written_off":
            return account.write_off(event.reason)
        case "plan_changed":
            return account.change_plan(event.reason)
        case _:
            raise ValueError(f"unknown event kind: {event.kind}")
