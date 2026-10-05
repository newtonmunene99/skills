def post(entries: list[dict]) -> int:
    return sum(e["amount"] for e in entries)
