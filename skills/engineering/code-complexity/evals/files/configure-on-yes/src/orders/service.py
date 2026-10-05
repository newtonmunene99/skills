"""Thin service layer; each call records the transition and returns the new order."""


def _record(action: str, **fields: object) -> dict:
    return {"action": action, **fields}


def create(payload: dict) -> dict:
    return _record("create", **payload)


def cancel(order_id: str) -> dict:
    return _record("cancel", order_id=order_id)


def pay(order_id: str, amount: int) -> dict:
    return _record("pay", order_id=order_id, amount=amount)


def refund(order_id: str, amount: int) -> dict:
    return _record("refund", order_id=order_id, amount=amount)


def ship(order_id: str, carrier: str) -> dict:
    return _record("ship", order_id=order_id, carrier=carrier)


def deliver(order_id: str) -> dict:
    return _record("deliver", order_id=order_id)


def start_return(order_id: str) -> dict:
    return _record("return", order_id=order_id)


def hold(order_id: str, reason: str) -> dict:
    return _record("hold", order_id=order_id, reason=reason)


def release(order_id: str) -> dict:
    return _record("release", order_id=order_id)


def split(order_id: str, lines: list) -> dict:
    return _record("split", order_id=order_id, lines=lines)


def merge(order_ids: list) -> dict:
    return _record("merge", order_ids=order_ids)


def annotate(order_id: str, note: str) -> dict:
    return _record("annotate", order_id=order_id, note=note)
