from orders import service


def handle_command(name: str, payload: dict) -> dict:
    match name:
        case "create":
            return service.create(payload)
        case "cancel":
            return service.cancel(payload["order_id"])
        case "pay":
            return service.pay(payload["order_id"], payload["amount"])
        case "refund":
            return service.refund(payload["order_id"], payload["amount"])
        case "ship":
            return service.ship(payload["order_id"], payload["carrier"])
        case "deliver":
            return service.deliver(payload["order_id"])
        case "return":
            return service.start_return(payload["order_id"])
        case "hold":
            return service.hold(payload["order_id"], payload["reason"])
        case "release":
            return service.release(payload["order_id"])
        case "split":
            return service.split(payload["order_id"], payload["lines"])
        case "merge":
            return service.merge(payload["order_ids"])
        case "annotate":
            return service.annotate(payload["order_id"], payload["note"])
        case _:
            raise ValueError(f"unknown command: {name}")
